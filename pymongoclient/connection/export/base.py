from abc import ABCMeta, abstractmethod


class Exporter(metaclass=ABCMeta):
    def __init__(self, cursor):
        self._cursor = cursor
        self._gzip = False

    def set_gzip(self, gzip):
        self._gzip = gzip

    def get_gzip(self):
        return self._gzip

    gzip = property(get_gzip, set_gzip)

    def export(self, out_file):
        self._do_export(out_file)
        self._do_gzip(out_file)

    @abstractmethod
    def _do_export(self, out_file):
        pass

    def _do_gzip(self, out_file):
        pass
