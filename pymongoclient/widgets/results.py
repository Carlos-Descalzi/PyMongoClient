import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib, Gdk
from ..utils import (GtkUtil, ModelUtil)
from .connectionsview import ConnectionsView
from .JsonFieldRenderer import JsonFieldRenderer
from ..dialogs import ExportDialog


class ResultsView(Gtk.VBox):

    __gsignals__ = {
        'update-request':
        (GObject.SIGNAL_RUN_FIRST, None, (str, object, object, object)),
        'selection-changed':
        (GObject.SIGNAL_RUN_FIRST, None, (str, object, object)),
        'notify-status': (GObject.SIGNAL_RUN_FIRST, None, (str, ))
    }

    def __init__(self):
        Gtk.VBox.__init__(self, False, 0)
        self.model = None
        self.resultset = None
        self._foreground_color = self._get_foreground()
        self.toolbar = Gtk.Toolbar()

        self.first_page_btn = GtkUtil.tool_button(Gtk.STOCK_MEDIA_PREVIOUS,
                                                  'First page',
                                                  self._on_first_page)
        self.prev_page_btn = GtkUtil.tool_button(Gtk.STOCK_MEDIA_REWIND,
                                                 'Previous page',
                                                 self._on_previous_page)
        self.next_page_btn = GtkUtil.tool_button(Gtk.STOCK_MEDIA_FORWARD,
                                                 'Next page',
                                                 self._on_next_page)
        self.last_page_btn = GtkUtil.tool_button(Gtk.STOCK_MEDIA_NEXT,
                                                 'Last page',
                                                 self._on_last_page)

        self.page_n = Gtk.Label()
        self.page_n.set_size_request(100, 20)
        self.totalcount = Gtk.Label()

        self.toolbar.insert(self.first_page_btn, -1)
        self.toolbar.insert(self.prev_page_btn, -1)
        item = Gtk.ToolItem()
        item.add(self.page_n)
        self.toolbar.insert(item, -1)
        self.toolbar.insert(self.next_page_btn, -1)
        self.toolbar.insert(self.last_page_btn, -1)
        item = Gtk.ToolItem()
        item.add(self.totalcount)
        self.toolbar.insert(item, -1)
        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)

        self.pack_start(self.toolbar, False, False, 0)

        self.view = Gtk.TreeView()
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.add(self.view)
        self.view.connect('row-activated', self._on_row_selected)

        self.pack_start(results_scroll, True, True, 0)

        # Key
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Key", renderer)
        column.set_min_width(300)
        column.set_resizable(True)
        column.set_cell_data_func(renderer, self._render_key)
        self.view.append_column(column)

        # Value
        renderer = JsonFieldRenderer()
        renderer.connect('field-edited', self._on_value_edited)
        column = Gtk.TreeViewColumn("Value", renderer)
        column.set_min_width(300)
        column.set_resizable(True)
        column.set_cell_data_func(renderer, self._render_value)
        self.view.append_column(column)

        # Type
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Type", renderer)
        column.set_min_width(100)
        column.set_max_width(100)
        column.set_resizable(False)
        column.set_cell_data_func(renderer, self._render_type)
        self.view.append_column(column)

        self.view.get_selection().connect('changed',
                                          self._on_selection_changed)
        self.set_model(Gtk.TreeStore(str, object))
        self._update_actions()

    def _get_foreground(self):
        widget_path = Gtk.WidgetPath()
        widget_path.append_type(Gtk.Label)
        style_ctx = Gtk.StyleContext()
        style_ctx.set_path(widget_path)
        clr = style_ctx.get_color(Gtk.StateFlags.NORMAL)
        return clr.to_string()

    def add_toolbar_items(self, items):
        for item in items:
            self.toolbar.insert(item, -1)

    def _render_key(self, col, cell, model, iter, data):
        value = model.get(iter, 0)[0]
        value = value if value is not None else ''
        cell.set_property('text', str(value))

    def _render_value(self, col, cell, model, iter, data):
        value = model.get(iter, 1)[0]
        value = value if value is not None else ''
        if isinstance(value, (dict, list)): value = '(%s items)' % len(value)

        if self._has_updates(iter):
            cell.set_property('foreground', '#FF0000')
        else:
            cell.set_property('foreground', self._foreground_color)

        cell.set_property('text', str(value))


    def _render_type(self, col, cell, model, iter, data):
        value = model.get(iter, 1)[0]

        type_str = ''
        if isinstance(value, str): type_str = 'String'
        elif isinstance(value, bool): type_str = 'Boolean'
        elif isinstance(value, int): type_str = 'Integer'
        elif isinstance(value, dict): type_str = 'Object'
        elif isinstance(value, list): type_str = 'Array'
        elif value is None: type_str = 'Null'
        else: type_str = str(type(value).__name__)

        if self._has_updates(iter):
            cell.set_property('foreground', '#FF0000')
        else:
            cell.set_property('foreground', self._foreground_color)

        cell.set_property('text', type_str)

    def set_model(self, model):
        self.model = model
        self.view.set_model(self.model)

    def has_data(self):
        return self.resultset is not None

    def _on_selection_changed(self, *args):
        model, itr = self.view.get_selection().get_selected()
        collection = self.resultset.collection if self.resultset else None

        self.emit('selection-changed', collection, model, itr)
        self._update_actions()

    def _update_actions(self, *args):
        has_data = self.resultset is not None
        self.first_page_btn.set_sensitive(has_data
                                          and self.resultset.has_first())
        self.prev_page_btn.set_sensitive(has_data
                                         and self.resultset.has_prev())
        self.next_page_btn.set_sensitive(has_data
                                         and self.resultset.has_next())
        self.last_page_btn.set_sensitive(has_data
                                         and self.resultset.has_last())

    def _update_page_and_count(self):
        if self.resultset:
            self.totalcount.set_text('%s documents' % len(self.resultset))
            self.page_n.set_text(
                'Page %s of %s' %
                (self.resultset.page + 1, self.resultset.pages))
        else:
            self.totalcount.set_text('%s documents' % 0)
            self.page_n.set_text('Page %s of %s' % (0, 0))

    def get_rowcount(self):
        return len(self.resultset)

    def set_result_set(self, resultset):
        self.resultset = resultset
        if self.resultset.is_ready(): self._show_page()
        self.resultset.connect('ready', self._on_data_ready)

    def _on_next_page(self, src):
        self.resultset.next_page()

    def _on_previous_page(self, src):
        self.resultset.prev_page()

    def _on_first_page(self, src):
        self.resultset.first_page()

    def _on_last_page(self, src):
        self.resultset.last_page()

    def _show_page(self):

        self.emit('notify-status', 'Building results view ...')

        def _ready(model):
            GLib.idle_add(self._on_model_ready, model)

        ModelUtil.build_document_model_async(self.resultset.pagedata, _ready)

    def _on_model_ready(self, model):
        self.set_model(model)
        self._update_page_and_count()
        self._update_actions()
        self.emit('notify-status', 'Done.')

    def _on_data_ready(self, src):
        GLib.idle_add(self._show_page)

    def _get_selected_row_obj(self):
        model, itr = self.view.get_selection().get_selected()
        return model.get_value(itr, 1)

    def _on_row_selected(self, view, path, column):
        pass

    def create_export_job(self, dumper):
        return self.resultset.create_export_job(dumper)

    def get_selection(self):
        return self.view.get_selection().get_selected()

    def get_collection(self):
        return self.resultset.collection

    def _has_updates(self, itr):
        model = self.view.get_model()
        return model.get_value(itr, 2)

    def _on_value_edited(self, source, itr, old_value, new_value):
        model = self.view.get_model()
        model.set_value(itr, 1, new_value)
        model.set_value(itr, 2, True)
        path = ModelUtil.get_json_path(model, itr)
        self.emit('update-request', self.resultset.collection, path[0],
                  path[1:], new_value)

    def clean_updates(self):
        model = self.view.get_model()

        for itr in ModelUtil.iterator(model):
            model.set_value(itr, 2, False)

    def add_array_field(self, itr, value):
        model = self.view.get_model()
        index = model.iter_n_children(itr)
        model.append(itr, (index, value, True))

    def add_field(self, itr, name, value):
        model = self.view.get_model()
        model.append(itr, (name, value, True))

    def remove(self, itr):
        model = self.view.get_model()
        model.remove(itr)
