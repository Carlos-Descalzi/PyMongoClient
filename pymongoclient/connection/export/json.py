from .base import Exporter
import json
from bson.objectid import ObjectId
from datetime import datetime


class JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return {"$oid": str(o)}
        elif isinstance(o, datetime):
            return {"$datetime": o.isoformat()}
        return super().default(o)


class JsonExporter(Exporter):

    _encoder = JsonEncoder()

    def _do_export(self, out_file):

        with open(out_file, "w") as f:
            for item in self._cursor:
                self._dump(item, f)

    def _dump(self, document, fp):
        fp.write(self._encoder.encode(document))
        fp.write("\n")
