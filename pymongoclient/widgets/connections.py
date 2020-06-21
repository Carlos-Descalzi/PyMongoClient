__all__ = ["ConnectionsView"]
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "3.0")
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib, Gdk
from ..connection import MongoConnection
from ..utils import GtkUtil, ModelUtil
import json
import os
import os.path
from ..messages import MESSAGES as messages


class ConnectionsView(Gtk.ScrolledWindow):

    __gsignals__ = {
        "connection-selected": (GObject.SIGNAL_RUN_FIRST, None, (object, str)),
        "connection-error": (GObject.SIGNAL_RUN_FIRST, None, (object, object)),
        "disconnected": (GObject.SIGNAL_RUN_FIRST, None, (object,)),
    }

    def __init__(self):
        Gtk.ScrolledWindow.__init__(self)
        self.view = Gtk.TreeView()
        self.add(self.view)
        self.view.connect("row-activated", self._on_row_selected)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Connections", renderer)
        column.set_cell_data_func(renderer, self._render_cell)
        self.view.append_column(column)
        self._init_connections()
        self._menu_actions = {}
        self.menu = Gtk.Menu()

        self._add_menu_item(messages.MN_ITEM_CONNECT, "connection", self._on_connect)
        self._add_menu_item(
            messages.MN_ITEM_DISCONNECT, "connection", self._on_disconnect
        )

        self.view.connect("button_press_event", self._on_button_press_event)

    def get_selected_connection(self):
        selection = self.view.get_selection()
        model, itr = selection.get_selected()
        if itr:
            value = model.get_value(itr, 0)
            if not isinstance(value, MongoConnection):
                itr = model.iter_parent(itr)
                value = model.get_value(itr, 0)
            return value
        return None

    def get_selected_path(self):
        selection = self.view.get_selection()
        model, itr = selection.get_selected()
        if itr:
            value = model.get_value(itr, 0)

            if isinstance(value, MongoConnection):
                return [value]

            itr = model.iter_parent(itr)
            return [model.get_value(itr, 0), value]

        return None

    def add_connection(self, name, config):
        connections = self._load_connections()
        connections[name] = config
        self._save_connections(connections)
        self._add_new_conn_obj(self.view.get_model(), name, config)

    def update_connection(self, conn_obj, data):
        connections = self._load_connections()
        connections[conn_obj.name] = data
        self._save_connections(connections)

        connected = conn_obj.is_connected()
        if connected:
            conn_obj.disconnect_from_server()

        conn_obj.config = data

        if connected:
            conn_obj.connect_to_server()

    def remove_connection(self, conn_obj):
        model, itr = self._get_conn_iter(conn_obj)
        model.remove(itr)

        if conn_obj.is_connected():
            conn_obj.disconnect_from_server()
            self.emit("disconnected", conn_obj)

        connections = self._load_connections()
        del connections[conn_obj.name]
        self._save_connections(connections)

    def _render_cell(self, col, cell, model, iter, data):
        value = model.get(iter, 0)[0]

        if value:
            if isinstance(value, MongoConnection):
                status = "Not connected"
                if value.is_connected():
                    status = "Connected"
                elif value.is_connecting():
                    status = "Connecting"

                conn_str = "%s (%s)" % (value.name, status)
                cell.set_property("text", conn_str)
            else:
                cell.set_property("text", value)
        else:
            cell.set_property("text", "")

    def _load_connections(self):

        connections_file = self._get_connections_file()

        if os.path.exists(connections_file):
            try:
                with open(connections_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_connections(self, connections):

        connections_file = self._get_connections_file()

        with open(connections_file, "w") as f:
            json.dump(connections, f, indent=4)

    def _get_connections_file(self):
        folder = os.path.join(os.environ["HOME"], ".mongoclient")

        if not os.path.isdir(folder):
            try:
                os.mkdir(folder)
            except:
                pass

        return os.path.join(folder, "connections.json")

    def _init_connections(self):
        connections = self._load_connections()
        store = Gtk.TreeStore(object)

        for key, data in list(connections.items()):
            self._add_new_conn_obj(store, key, data)

        self.view.set_model(store)

    def _add_new_conn_obj(self, store, name, data):
        conn = MongoConnection(name, data)
        conn.connect("connected", self._conn_connected)
        conn.connect("connect_error", self._conn_error)
        store.append(None, [conn])

    def _on_row_selected(self, view, path, column):
        model = view.get_model()

        itr = model.get_iter(path)

        value = model.get_value(itr, 0)

        if isinstance(value, MongoConnection):
            if not value.is_connected():
                value.connect_to_server()
            else:
                self.emit("connection-selected", value, None)
        else:
            itr = model.get_iter(path)
            conn_obj = model.get_value(model.iter_parent(itr), 0)
            self.emit("connection-selected", conn_obj, value)

    def _conn_connected(self, conn):
        def _load_collections():
            model, itr = self._get_conn_iter(conn)
            db = conn.get_db()

            for coll in sorted(db.collection_names()):
                model.append(itr, [coll])

            path = model.get_path(itr)
            self.view.expand_row(path, True)

        GLib.idle_add(_load_collections)

    def _get_conn_iter(self, conn):
        model = self.view.get_model()
        for itr in ModelUtil.iterator(model):
            if model.get_value(itr, 0) == conn:
                return model, itr
        return model, None

    def _conn_error(self, conn, error):
        def _notify():
            self.emit("connection-error", conn, error)

        GLib.idle_add(_notify)

    def set_actions(self, actions):
        for label, item in list(actions.items()):
            target, action = item
            self._add_menu_item(label, target, action)

    def _add_menu_item(self, label, target, handler):
        item = GtkUtil.menu_item(label, handler)
        self._menu_actions[label] = (target, item)
        self.menu.append(item)

    def _on_button_press_event(self, src, event):
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button == 3:
                self._update_menu_actions()
                self.menu.popup(None, None, None, None, event.button, event.time)

    def _update_menu_actions(self):
        path = self.get_selected_path()

        if path is not None:

            for label, item in list(self._menu_actions.items()):
                target, menu_item = item

                if label == "Connect":
                    menu_item.set_sensitive(
                        len(path) == 1 and not path[0].is_connected()
                    )
                else:
                    if target == "connection":
                        menu_item.set_sensitive(
                            len(path) == 1 and path[0].is_connected()
                        )
                    elif target == "collection":
                        menu_item.set_sensitive(
                            len(path) == 2 and path[0].is_connected()
                        )
                    else:
                        menu_item.set_sensitive(True)
        else:
            for item in list(self._menu_actions.values()):
                target, menu_item = item
                menu_item.set_sensitive(False)

    def _on_connect(self, *args):
        conn = self.get_selected_connection()
        conn.connect_to_server()

    def _on_disconnect(self, *args):
        conn = self.get_selected_connection()
        conn.disconnect_from_server()
        self.emit("disconnected", conn)

        model, itr = self._get_conn_iter(conn)

        child_itr = model.iter_children(itr)

        while child_itr:
            model.remove(child_itr)
            child_itr = model.iter_children(itr)
