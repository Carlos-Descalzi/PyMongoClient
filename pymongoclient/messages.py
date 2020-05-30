import os
import configparser
from .utils.fileutil import locate_in_modules


class _Messages:
    def __init__(self):
        locale = os.environ["LANG"].split(".")[0]
        lang = locale.split("_")[0]

        for option in [locale, lang, "en"]:
            try:
                fname = locate_in_modules(
                    os.path.join("msgs", "%s.properties" % option)
                )
                if os.path.exists(fname):
                    self.__dict__.update(self._read_file(fname))
            except KeyError:
                pass

    def _read_file(self, fname):
        results = {}
        with open(fname, "r") as f:
            for line in f:
                k, v = line.strip().split("=")
                results[k] = v

        return results


MESSAGES = _Messages()
