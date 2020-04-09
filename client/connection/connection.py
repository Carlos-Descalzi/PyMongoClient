import json
import runpy
import subprocess
import tempfile
import threading
import traceback
from datetime import datetime

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')

import pymongo
from bson.int64 import Int64
from bson.objectid import ObjectId
from gi.repository import GObject


class Tunnel:
    def __init__(self, config):
        self.password = None
        self.keyfile = None
        self.port = None
        self.user = None
        self.host = None
        self.__dict__.update(config)
        self._transport = None
        self._forwards = []
        self._pipe = None

    def connect(self):

        command = []

        if self.password:
            command += ['sshpass', '-p%s' % self.password]

        command += ['ssh']

        if self.keyfile:
            command += ['-i', self.keyfile]

        command += ['-p', str(self.port), '%s@%s' % (self.user, self.host)]

        for forward in self._forwards:
            command += ['-L%(port)d:%(host)s:%(port)d' % forward]

        self._pipe = subprocess.Popen(command,
                                      stdout=subprocess.PIPE,
                                      stdin=subprocess.PIPE)

    def close(self):
        if self._pipe:
            self._pipe.kill()

    def add_host(self, host, port):
        self._forwards.append({'host': host, 'port': port})


class MongoConnection(GObject.GObject):

    __gsignals__ = {
        'connecting': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'connected': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'disconnected': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'connect_error': (GObject.SIGNAL_RUN_FIRST, None, (object, ))
    }

    def __init__(self, name, config):
        GObject.GObject.__init__(self)
        self.name = name
        self.config = config
        self.text = name
        self.conn = None
        self.db = None
        self.info = None
        self.conn_thread = None
        self.tunnel = None
        self._new_conn_info = None

    def connect_to_server(self):
        self.conn_thread = threading.Thread(target=self._do_connect)
        self.conn_thread.daemon = True
        self.conn_thread.start()

    def is_connecting(self):
        return self.conn_thread and \
         self.conn_thread.is_alive() \
         and not self.conn

    def is_connected(self):
        return self.conn is not None and \
         self.info is not None

    def _do_connect(self):
        self.emit('connecting')
        try:
            self.tunnel, self._new_conn_info = self._build_tunnel(self.config)

            url = self._build_url(self.config, self._new_conn_info)
            conn = pymongo.MongoClient(url, connectTimeoutMS=60000)
            db = conn.get_database(self.config['db'])
            self.info = conn.server_info()
            self.conn = conn
            self.db = db
            self.emit('connected')
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            if self.conn: self.conn.close()
            self.conn = None
            self.db = None
            self.info = None
            self.emit('connect_error', e)

    def _build_tunnel(self, conn_info):

        tunnel_config = conn_info.get('tunnel')
        if tunnel_config:
            tunnel = Tunnel(tunnel_config)
            new_conn_info = []

            for conn in conn_info['connection']:
                tunnel.add_host(conn['host'], conn['port'])
                new_conn_info.append({
                    'host': 'localhost',
                    'port': conn['port']
                })

            tunnel.connect()

            return tunnel, new_conn_info
        else:
            return None, conn_info['connection']

    def build_uri(self):
        return self._build_url(self.config, self._new_conn_info)

    def _build_url(self, config, conn_info):
        auth = '%(user)s:%(password)s' % config['auth']
        hostlist = ','.join(
            [self._format_host(item, config) for item in conn_info])

        scheme = 'mongodb+srv' if config.get('ssl') else 'mongodb'

        return '%s://%s@%s/%s' % (scheme, auth, hostlist, config['db'])

    def _format_host(self, host_info, config):
        if config.get('ssl'):
            return '%(host)s' % host_info
        return '%(host)s:%(port)d' % host_info

    def execute_statement(self, statement):
        if not self.is_connected():
            raise Exception('Not connected')

        def _do_execute_statement():
            statement(self.db)

        thread = threading.Thread(target=_do_execute_statement)
        thread.daemon = True
        thread.start()

    def get_connection(self):
        if not self.is_connected():
            return None
        return self.conn

    def get_db(self):
        if not self.is_connected():
            return None
        return self.db

    def disconnect_from_server(self):
        if self.is_connected():
            self.conn.close()
            self.db = None
            self.conn = None
            if self.tunnel:
                self.tunnel.close()
                self.tunnel = None
            self.emit('disconnected')
