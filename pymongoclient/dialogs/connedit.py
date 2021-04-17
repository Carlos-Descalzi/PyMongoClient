import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "3.0")
import re
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib
from ..utils import GladeObject, modelutil

HOST_PATTERN = "^[a-zA-Z0-9\\.\\-\\+_]+$"
PORT_PATTERN = "^[1-9][0-9]+$"
DB_NAME_PATTERN = "^[a-zA-Z0-9\\.\\-\\+_]+"
USERNAME_PATTERN = "^[a-zA-Z0-9\\.\\-\\+_]+"
PASSWORD_PATTERN = "^[a-zA-Z0-9\\.\\-\\+_]+"


class ConnectionEditorDialog(GladeObject):

    __gsignals__ = {"accept": (GObject.SIGNAL_RUN_FIRST, None, (str, object))}

    def __init__(self):
        GladeObject.__init__(self, "ui/ConnEdit.glade")
        self.replicaset.set_model(Gtk.ListStore(str, int))

        renderer = Gtk.CellRendererText()
        renderer.set_property("editable", True)
        renderer.connect("edited", self._on_host_edited)
        column = Gtk.TreeViewColumn("Host", renderer, text=0)
        column.set_min_width(300)
        self.replicaset.append_column(column)

        self._port_renderer = Gtk.CellRendererText()
        self._port_renderer.set_property("editable", True)
        self._port_renderer.connect("edited", self._on_port_edited)

        column = Gtk.TreeViewColumn("Port", self._port_renderer, text=1)
        column.set_cell_data_func(self._port_renderer, self._set_port_cell_data)
        self.replicaset.append_column(column)

    def _on_host_edited(self, renderer, path, new_text):
        model = self.replicaset.get_model()
        itr = model.get_iter(path)
        model.set_value(itr, 0, new_text)

    def _on_port_edited(self, renderer, path, new_text):
        model = self.replicaset.get_model()
        itr = model.get_iter(path)
        model.set_value(itr, 1, int(new_text))

    def _set_port_cell_data(self, column, cell, model, itr, *data):

        if self.conn_ssl_tls.get_active():
            cell.set_property("text", "(Default)")
        else:
            port = model.get_value(itr, 1)
            cell.set_property("text", str(port))

    def show(self, conn_name=None, connection={}):
        self._populate_form(conn_name, connection)
        self._update_actions()
        self.dialog.show()

    def _on_accept(self, src):
        name, data = self._get_data()
        self.emit("accept", name, data)
        self.dialog.destroy()

    def _on_cancel(self, *args):
        self.dialog.destroy()

    def _on_add_replicaset(self, *args):
        self.replicaset.get_model().append(["[hostname]", 9999])

    def _on_remove_replicaset(self, *args):
        model, itr = self.replicaset.get_selection().get_selected()
        model.remove(itr)

    def _on_conn_ssl_tls_change(self, *args):
        self._port_renderer.set_property("editable", not self.conn_ssl_tls.get_active())

    def _valid(self):

        valid = self._valid_name(self.conn_name.get_text()) and self._valid_db_name(
            self.db_name.get_text()
        )

        if self.auth_type.get_current_page() == 0:
            valid &= self._valid_user_name(
                self.auth_basic_username.get_text()
            ) and self._valid_password(self.auth_basic_password.get_text())

        return valid

    def _update_actions(self, *args):

        self.apply_btn.set_sensitive(self._valid())

        enable_tunnel = self.use_ssh_tunnel.get_active()
        self.tunnel_host.set_sensitive(enable_tunnel)
        self.tunnel_port.set_sensitive(enable_tunnel)
        self.tunnel_user.set_sensitive(enable_tunnel)
        self.use_tunnel_password.set_sensitive(enable_tunnel)
        self.use_tunnel_keyfile.set_sensitive(enable_tunnel)
        use_tunnel_password = self.use_tunnel_password.get_active()

        self.tunnel_password.set_sensitive(enable_tunnel and use_tunnel_password)
        self.tunnel_keyfile.set_sensitive(enable_tunnel and not use_tunnel_password)
        self._port_renderer.set_property("editable", not self.conn_ssl_tls.get_active())

    def _valid_name(self, name):
        return len(name.strip()) > 1

    def _valid_host(self, host):
        return re.match(HOST_PATTERN, host) is not None

    def _valid_port(self, port):
        return re.match(PORT_PATTERN, port) is not None

    def _valid_db_name(self, db_name):
        return re.match(DB_NAME_PATTERN, db_name) is not None

    def _valid_user_name(self, username):
        return re.match(USERNAME_PATTERN, username) is not None

    def _valid_password(self, password):
        return re.match(PASSWORD_PATTERN, password) is not None

    def _get_data(self):
        name = self.conn_name.get_text()

        connection = []

        model = self.replicaset.get_model()

        for itr in modelutil.iterator(model):
            connection.append(
                {"host": model.get_value(itr, 0), "port": model.get_value(itr, 1)}
            )

        if self.auth_type.get_current_page() == 0:
            auth = {
                "user": self.auth_basic_username.get_text(),
                "password": self.auth_basic_password.get_text(),
            }
        else:
            auth = {}

        if self.use_ssh_tunnel.get_active():
            tunnel = {
                "host": self.tunnel_host.get_text(),
                "port": int(self.tunnel_port.get_text()),
                "user": self.tunnel_user.get_text(),
                "password": self.tunnel_password.get_text()
                if self.use_tunnel_password.get_active()
                else None,
                "keyfile": self.tunnel_keyfile.get_filename()
                if not self.use_tunnel_password.get_active()
                else None,
            }
        else:
            tunnel = None

        data = {
            "connection": connection,
            "ssl": self.conn_ssl_tls.get_active(),
            "db": self.db_name.get_text(),
            "auth": auth,
            "tunnel": tunnel,
        }

        return name, data

    def _populate_form(self, name, connection):
        self.conn_name.set_text(name or "")
        self.conn_name.set_sensitive(name is None)
        self.db_name.set_text(connection.get("db", ""))
        self.conn_ssl_tls.set_active(connection.get("ssl", False))

        conn_info = connection.get("connection")
        if conn_info:

            model = self.replicaset.get_model()
            for item in conn_info:
                model.append([item["host"], item["port"]])

        auth = connection.get("auth")
        if auth:
            self.auth_basic_username.set_text(auth["user"])
            self.auth_basic_password.set_text(auth["password"])

        tunnel = connection.get("tunnel")
        if tunnel:
            self.use_ssh_tunnel.set_active(True)
            self.tunnel_host.set_text(tunnel["host"])
            self.tunnel_port.set_text(str(tunnel["port"]))
            self.tunnel_user.set_text(tunnel["user"])

            password = tunnel.get("password")

            if password:
                self.use_tunnel_password.set_active(True)
                self.tunnel_password.set_text(password)
            else:
                self.use_tunnel_keyfile.set_active(True)
                key_file = tunnel.get("keyfile")
                if key_file:
                    self.tunnel_keyfile.set_filename(key_file)
        else:
            self.use_ssh_tunnel.set_active(False)
