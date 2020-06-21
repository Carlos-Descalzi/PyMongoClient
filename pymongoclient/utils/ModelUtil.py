import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "3.0")
from gi.repository import Gtk, GObject, GtkSource, Pango, GLib
import json
from datetime import datetime
from bson.objectid import ObjectId
from threading import Thread


def build_document_model(cursor):
    model = Gtk.TreeStore(object, object, bool)
    for obj in cursor:
        if isinstance(obj, dict):
            if "_id" in obj:
                key = obj["_id"]
            else:
                key = "Document"

            parent = model.append(None, (key, obj, False))
            do_append_obj(model, obj, parent)
        else:
            parent = model.append(None, (None, obj, False))
    return model


def build_document_model_async(cursor, callback):
    def _run():
        model = build_document_model(cursor)
        callback(model)

    thread = Thread(target=_run)
    thread.start()


def do_append_obj(model, obj, parent):
    for key, val in list(obj.items()):
        if isinstance(val, dict):
            child = model.append(parent, (key, val, False))
            do_append_obj(model, val, child)
        elif isinstance(val, list):
            child = model.append(parent, (key, val, False))
            for i, item in enumerate(val):
                childn = model.append(child, (i, item, False))
                if isinstance(item, dict):
                    do_append_obj(model, item, childn)
        elif _is_primitive(val):
            model.append(parent, (key, val, False))
        else:
            print("Unknown value", type(val), val)


def _is_primitive(val):
    return val is None or isinstance(val, (str, int, bool, datetime, ObjectId))


def get_json_path(model, itr):
    path = []
    while itr:
        path.insert(0, model.get_value(itr, 0))
        itr = model.iter_parent(itr)
    return path


def root(model, itr):
    parent = model.iter_parent(itr)

    while parent:
        itr = parent
        parent = model.iter_parent(itr)

    return itr


class _ModelIterator:
    def __init__(self, model):
        self.model = model
        self.itr = self.model.get_iter_first()

    def __iter__(self):
        self.itr = self.model.get_iter_first()
        return self

    def __next__(self):
        if not self.itr:
            raise StopIteration()

        itr = self.itr
        self.itr = self.model.iter_next(self.itr)
        return itr


def iterator(model):
    return _ModelIterator(model)
