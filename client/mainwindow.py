import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib
from client.connection import MongoConnection
from client.widgets.queryeditor import QueryEditor
import json
from client.dialogs import ConnectionEditorDialog
from client.utils import GladeObject, Templates
from client.dialogs import (ConfirmDialog, AboutDialog, ConnectionEditorDialog,
                            MessageDialog, ImportDialog, ExportDialog)
from client.widgets.connectionsview import ConnectionsView
from collections import OrderedDict
from client.messages import MESSAGES as messages


class MainWindow(GladeObject):
    def __init__(self):
        GladeObject.__init__(self, "client/ui/MongoClient.glade")

        self.conn_view = ConnectionsView()
        self.conn_area.add(self.conn_view)
        self.conn_view.connect('connection-selected',
                               self._on_connection_selected)
        self.conn_view.connect('connection-error', self._on_connection_error)

        self.build_main_pane()
        self.connection_tabs = []

        self.conn_view.set_actions(
            OrderedDict([
                (messages.BTN_NEW_EDITOR, ('connection', self._new_editor)),
                (messages.BTN_SHOW_INDEXES, ('collection',
                                             self._show_indexes)),
                (messages.BTN_FIND_ALL, ('collection', self._find_all)),
                (messages.BTN_IMPORT_DATA, (None, self._import_data)),
                (messages.BTN_EXPORT_DATA, ('collection', self._export_data))
            ]))

    def build_main_pane(self):
        self.tabs = Gtk.Notebook()
        self.MainPane.add2(self.tabs)
        self.MainPane.set_position(200)

    def on_exit(self, obj):
        self.exit()

    def on_delete_event(self, obj, evt):
        self.exit()

    def exit(self):
        self.close_all()
        Gtk.main_quit()

    def close_all(self):
        list(map(QueryEditor.close, self.connection_tabs))

    def show(self):
        self.MainWindow.maximize()
        self.MainWindow.show_all()

    def get_selected_tab(self):
        index = self.tabs.get_current_page()
        return self.tabs.get_nth_page(index)

    def on_add_connection(self, obj):
        conn_editor = ConnectionEditorDialog()

        def _on_accept(src, name, data):
            self.conn_view.add_connection(name, data)

        conn_editor.connect('accept', _on_accept)
        conn_editor.show()

    def on_edit_connection(self, obj):
        conn_obj = self.conn_view.get_selected_connection()

        conn_editor = ConnectionEditorDialog()

        def _on_accept(src, name, data):
            self.conn_view.update_connection(conn_obj, data)

        conn_editor.connect('accept', _on_accept)
        conn_editor.show(conn_obj.name, conn_obj.config)

    def on_remove_connection(self, obj):
        conn_obj = self.conn_view.get_selected_connection()

        response = ConfirmDialog().show(messages.WARNING,
                                        messages.CONFIRM_DELETE_CONN)

        if response == Gtk.ResponseType.OK:
            self.conn_view.remove_connection(conn_obj)

    def _close_connection(self, conn_obj):
        pass

    def _on_connection_selected(self, src, conn_obj, collection=None):
        tab = QueryEditor(conn_obj)
        tab.show_all()
        box = Gtk.HBox(False, 3)
        label = Gtk.Label.new(conn_obj.name)
        box.pack_start(label, True, True, 0)
        button = Gtk.Button.new_from_icon_name(Gtk.STOCK_CLOSE,
                                               Gtk.IconSize.BUTTON)
        box.pack_start(button, False, False, 0)
        box.show_all()

        index = self.tabs.get_n_pages()

        def _close_editor(src, idx):
            self.tabs.remove_page(idx)

        button.connect('clicked', _close_editor, index)
        self.tabs.append_page(tab, box)
        self.connection_tabs.append(tab)

        self.tabs.set_current_page(index)

        if collection: self._find_all()

    def _new_editor(self, *args):
        conn_obj = self.conn_view.get_selected_connection()
        self._on_connection_selected(None, conn_obj)

    def _show_indexes(self, *args):
        _, coll = tuple(self.conn_view.get_selected_path())
        self._insert_in_current_editor(Templates.indexes(coll))

    def _find_all(self, *args):
        _, coll = tuple(self.conn_view.get_selected_path())
        self._insert_in_current_editor(Templates.find_all(coll))

    def _import_data(self, *args):
        selection = self.conn_view.get_selected_path()
        conn = selection[0]
        collection = selection[1] if len(selection) > 1 else None
        ImportDialog(conn, collection).show()

    def _export_data(self, *args):
        conn, collection = tuple(self.conn_view.get_selected_path())
        ExportDialog(conn, collection=collection).show()

    def _insert_in_current_editor(self, text):
        tab = self.get_selected_tab()
        if tab: tab.buffer.set_text(text)

    def _on_connection_error(self, src, conn, error):
        MessageDialog().show(messages.ERROR, messages.ERROR_CONNECTING % error)

    def _on_about(self, *args):
        AboutDialog().show()

    def run_main(self):
        self.show()
        Gtk.main()
