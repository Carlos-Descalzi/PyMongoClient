import json
from bson.int64 import Int64
from bson.objectid import ObjectId
from datetime import datetime


class _CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return str(int((o - datetime.utcfromtimestamp(0)).total_seconds() * 1000))
        elif isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def dump(obj, fp, **kwargs):
    json.dump(obj, fp, cls=_CustomJsonEncoder, **kwargs)


def loads(string):
    return json.loads(string)


def dumps(obj, **kwargs):
    return json.dumps(obj, cls=_CustomJsonEncoder, **kwargs)


def dumpf(obj, fname, **kwargs):
    with open(fname, "w") as f:
        dump(obj, f, **kwargs)
