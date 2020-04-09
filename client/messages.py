import os
import configparser


class _Messages:
    def __init__(self):
        print('INIT')
        locale = os.environ["LANG"].split(".")[0]
        lang = locale.split('_')[0]

        for option in [locale, lang, 'en']:
            fname = os.path.join('client', 'msgs', '%s.properties' % option)
            if os.path.exists(fname):
                self.__dict__.update(self._read_file(fname))

    def _read_file(self, fname):
        results = {}
        with open(fname, 'r') as f:
            for line in f:
                k, v = line.strip().split('=')
                results[k] = v

        return results


MESSAGES = _Messages()
