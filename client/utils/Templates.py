import re
from bson.objectid import ObjectId


def find_all(collection_name):
    return 'resultset = db%s.find({})' % _python_friendly(collection_name)


def indexes(collection_name):
    return 'resultset = db%s.index_information()' % _python_friendly(
        collection_name)


def _python_friendly(collection_name):
    if not re.match('^[a-zA-Z_][0-9a-zA-Z_]+$', collection_name):
        return "['%s']" % collection_name
    return '.%s' % collection_name


def make_path(field_path):
    path_str = ''
    for item in field_path:
        if len(path_str) > 0: path_str += '.'
        path_str += str(item)

    return path_str


def _format_value(value):

    if isinstance(value, ObjectId):
        return "ObjectId('%s')" % str(value)

    return "'%s'" % value \
     if isinstance(value,str) and not 'ObjectId' in value \
     else str(value)


def update(field_path, value):
    path_str = make_path(field_path)
    val_str = _format_value(value)

    return "{'$set':{'%s':%s}}" % (path_str, val_str)