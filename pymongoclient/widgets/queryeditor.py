import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "3.0")
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib, Gdk
from ..connection import MongoConnection, CursorResultSet, ListResultSet
from ..utils import GtkUtil, ModelUtil, JsonUtil
from ..dialogs import ExportDialog, FieldEditorDialog, ConfirmDialog
from ..widgets.results import ResultsView
from ..crud import UpdatesHandler
from collections import OrderedDict
from bson.objectid import ObjectId
import uuid
import tempfile
import runpy
import pymongo.cursor
from pymongo.command_cursor import CommandCursor
from ..messages import MESSAGES as messages

QUERY_TEMPLATE = """
from bson.objectid import *

%s
"""


class QueryEditor(Gtk.VBox):
    def __init__(self, conn_obj):
        Gtk.VBox.__init__(self, False, 0)

        self.conn_obj = conn_obj

        self._updates = UpdatesHandler()

        toolbar = Gtk.Toolbar()
        self.execute_btn = GtkUtil.tool_button(
            Gtk.STOCK_EXECUTE, messages.BTN_EXECUTE, self._on_execute
        )
        toolbar.insert(self.execute_btn, -1)

        self.pack_start(toolbar, False, False, 0)

        self.paned = Gtk.Paned()
        self.paned.set_orientation(Gtk.Orientation.VERTICAL)
        self.pack_start(self.paned, True, True, 0)
        self.code_view = GtkSource.View()

        lang_manager = GtkSource.LanguageManager.get_default()

        lang = lang_manager.get_language("python")

        self.buffer = GtkSource.Buffer.new_with_language(lang)
        self.code_view.set_buffer(self.buffer)
        self.code_view.set_show_line_numbers(True)
        font_desc = Pango.FontDescription("monospace 10")
        self.code_view.modify_font(font_desc)
        self.paned.set_position(150)
        self.results = ResultsView()

        code_scroll = Gtk.ScrolledWindow()
        code_scroll.add(self.code_view)

        self.paned.add1(code_scroll)
        self.log = Gtk.TextView()

        log_scroll = Gtk.ScrolledWindow()
        log_scroll.add(self.log)

        self.results.add_toolbar_items(self.build_results_actions())

        self.results_tab = Gtk.Notebook()
        self.results_tab.append_page(self.results, Gtk.Label(messages.TAB_RESULTS))
        self.results_tab.append_page(log_scroll, Gtk.Label(messages.TAB_OUTPUT))
        self.paned.add2(self.results_tab)

        self.results.connect("update-request", self._on_update_field)
        self.results.connect("selection-changed", self._on_selection_changed)
        self.results.connect("notify-status", self._on_results_status)
        self._update_results_actions()

        self.status_bar = Gtk.Statusbar()
        self.pack_start(self.status_bar, False, False, 0)
        self.status_ctx = self.status_bar.get_context_id("")

    ####
    def build_results_actions(self):
        self.save_btn = GtkUtil.tool_button(
            Gtk.STOCK_SAVE, messages.BTN_EXPORT_DATA, self._save_results
        )
        self.flush_updates_btn = GtkUtil.tool_button(
            Gtk.STOCK_APPLY, messages.BTN_APPLY_UPDATES, self._on_flush_updates
        )
        self.edit_val_btn = GtkUtil.tool_button(
            Gtk.STOCK_EDIT, messages.BTN_EDIT_VALUE, self._on_edit_val
        )
        self.add_val_btn = GtkUtil.tool_button(
            Gtk.STOCK_ADD, messages.BTN_ADD_ITEM, self._on_add_field
        )
        self.remove_val_btn = GtkUtil.tool_button(
            Gtk.STOCK_REMOVE, messages.BTN_REMOVE_ITEM, self._on_remove_field
        )
        self.copy_json_doc_btn = GtkUtil.tool_button(
            Gtk.STOCK_COPY, messages.BTN_COPY_JSON, self._on_copy_document_as_json
        )
        self.copy_python_doc_btn = GtkUtil.tool_button(
            Gtk.STOCK_COPY, messages.BTN_COPY_PYTHON, self._on_copy_document_as_python
        )
        self.delete_doc_btn = GtkUtil.tool_button(
            Gtk.STOCK_DELETE, messages.BTN_DELETE_DOCUMENT, self._on_delete_document
        )

        return [
            self.save_btn,
            Gtk.SeparatorToolItem(),
            self.edit_val_btn,
            self.add_val_btn,
            self.remove_val_btn,
            Gtk.SeparatorToolItem(),
            self.flush_updates_btn,
            Gtk.SeparatorToolItem(),
            self.copy_python_doc_btn,
            self.copy_json_doc_btn,
            self.delete_doc_btn,
        ]

    def _save_results(self, *args):
        ExportDialog(self.conn_obj, resultset=self.results).show()

    def _on_edit_val(self, *args):
        model, itr = self.results.get_selection()
        path = ModelUtil.get_json_path(model, itr)
        value = model.get_value(itr, 1)

    def _gen_clear_statement(self, *args):
        pass

    def _on_selection_changed(self, *args):
        self._update_results_actions()

    def _update_results_actions(self):

        has_data = self.results.has_data()
        self.save_btn.set_sensitive(has_data)

        if has_data:
            rowcount = self.results.get_rowcount() > 0
            model, itr = self.results.get_selection()
            if model and itr:
                value = model.get_value(itr, 1)
                can_add = isinstance(value, (dict, list))
                can_edit = not isinstance(value, (dict, list, ObjectId))
                path = ModelUtil.get_json_path(model, itr)
                can_remove = rowcount > 0 and len(path) > 1
            else:
                can_add = False
                can_edit = False
                can_remove = False

            self.edit_val_btn.set_sensitive(can_edit)
            self.add_val_btn.set_sensitive(can_add)
            self.remove_val_btn.set_sensitive(can_remove)
            self.copy_json_doc_btn.set_sensitive(rowcount > 0)
            self.copy_python_doc_btn.set_sensitive(rowcount > 0)
            self.delete_doc_btn.set_sensitive(rowcount > 0)
        else:
            self.edit_val_btn.set_sensitive(False)
            self.add_val_btn.set_sensitive(False)
            self.remove_val_btn.set_sensitive(False)
            self.copy_json_doc_btn.set_sensitive(False)
            self.copy_python_doc_btn.set_sensitive(False)
            self.delete_doc_btn.set_sensitive(False)

        self.flush_updates_btn.set_sensitive(len(self._updates) > 0)

    ####
    def feed_output(self, result):
        self.current_result = result
        self.results.set_result_set(result)
        self.results_tab.set_current_page(0)

        self._update_results_actions()
        self._allow_execute()

    def feed_log(self, line):
        GtkUtil.text_buffer_append(self.log.get_buffer(), line)
        self.results_tab.set_current_page(1)
        self._allow_execute()

    def _disable_execute(self, *args):
        self.execute_btn.set_sensitive(False)

    def _allow_execute(self, *args):
        self.execute_btn.set_sensitive(True)

    def on_cut(self):
        pass

    def on_copy(self):
        pass

    def on_paste(self):
        pass

    def close(self):
        self.conn_obj.disconnect_from_server()

    def _on_execute(self, src):

        query = GtkUtil.get_text(self.code_view)
        self.execute_btn.set_sensitive(False)

        def statement(db):

            script_globals = {"db": db, "log": self._log, "resultset": None}
            try:
                print(query)

                compiled = compile(query, "script.py", "exec")

                eval(compiled, script_globals)

                resultset = script_globals["resultset"]

                if isinstance(resultset, pymongo.cursor.Cursor):
                    print(1)
                    resultset = CursorResultSet(resultset, None)
                elif isinstance(resultset, CommandCursor):
                    resultset = ListResultSet(list(resultset), "", None)
                else:
                    print(2)
                    if not isinstance(resultset, list):
                        print(3)
                        resultset = [resultset]
                    resultset = ListResultSet(resultset, "", None)

                GLib.idle_add(self.feed_output, resultset)
            except SyntaxError as e:
                self._log("%s, at line %s" % (e.msg, e.lineno))
            except Exception as e:
                self._log(str(e))

        self._set_status("Executing query ...")
        self.conn_obj.execute_statement(statement)

    def _log(self, message):
        GLib.idle_add(self.feed_log, message)

    def _on_add_field(self, src):

        model, itr = self.results.get_selection()
        path = ModelUtil.get_json_path(model, itr)
        doc_id = path[0]
        path = path[1:]
        value = model.get_value(itr, 1)
        collection = self.results.get_collection()

        editor = FieldEditorDialog()

        def _on_accept(src):

            field_value = editor.get_field_value()

            if isinstance(value, dict):
                field_name = editor.get_field_name()
                path.append(field_name)
                self._updates.set(collection, doc_id, path, field_value)
                self.results.add_field(itr, field_name, field_value)
            else:
                self._updates.push(collection, doc_id, path, field_value)
                self.results.add_array_field(itr, field_value)
            self._update_results_actions()

        editor.connect("accept", _on_accept)
        editor.show(disable_name=isinstance(value, list))

    def _on_remove_field(self, src):
        model, itr = self.results.get_selection()
        path = ModelUtil.get_json_path(model, itr)
        doc_id = path[0]
        path = path[1:]
        key = model.get_value(itr, 0)
        collection = self.results.get_collection()

        if isinstance(key, int):
            placeholder = str(uuid.uuid1())
            self._updates.set(collection, doc_id, path, placeholder)
            self._updates.pull(collection, doc_id, path[0:-1], placeholder)
        else:
            self._updates.unset(collection, doc_id, path)

        self.results.remove(itr)

        self._update_results_actions()

    def _on_edit_document(self, collection, src, doc_id, path, val):

        field = path[-1]

        editor = FieldEditorDialog()

        def _on_accept():
            pass

        editor.connect("accept", _on_accept)
        editor.show(field, val)

    def _on_copy_document_as_json(self, *args):
        self._copy_document(lambda doc: JsonUtil.dumps(doc, indent=4))

    def _on_copy_document_as_python(self, *args):
        self._on_copy_document(lambda doc: str(doc))

    def _on_copy_document(self, format_func):
        model, itr = self.results.get_selection()
        doc_obj = model.get_value(itr, 1)

        display = Gdk.Display.get_default()
        clipboard = Gtk.Clipboard.get_default(display)

        doc_str = format_func(doc_obj)

        clipboard.set_text(doc_str, -1)

    def _on_delete_document(self, src, *args):
        collection = self.results.get_collection()
        model, itr = self.results.get_selection()
        path = ModelUtil.get_json_path(model, itr)
        doc_id = path[0]

        response = ConfirmDialog().show(messages.CONFIRM, messages.CONFIRM_DELETE)

        if response == Gtk.ResponseType.OK:

            def statement(db):
                db[collection].delete_one({"_id": doc_id})

            self._do_execute_statement(statement)
            self.results.remove(ModelUtil.root(model, itr))

    def _on_flush_updates(self, *args):
        sentences = self._updates.build_sentences()

        def statement(db):
            for item in sentences:
                collection, doc_id, updates = item
                db[collection].find_and_modify({"_id": doc_id}, updates)

        self._do_execute_statement(statement)

    def _do_execute_statement(self, statement):
        def wrapped_stmt(db):
            try:
                statement(db)
            except Exception as e:
                GLib.idle_add(self.feed_log, str(e))
            GLib.idle_add(self._allow_execute)

        self.execute_btn.set_sensitive(False)
        self.conn_obj.execute_statement(wrapped_stmt)
        self._updates.clear()
        self.results.clean_updates()
        self._update_results_actions()

    def _on_update_field(self, src, collection, doc_id, field_path, value):
        self._updates.set(collection, doc_id, field_path, value)
        self._update_results_actions()

    def _on_results_status(self, src, message):
        self._set_status(message)

    def _set_status(self, message):
        self.status_bar.push(self.status_ctx, message)
