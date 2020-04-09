#!/usr/bin/python3

import sys

version = sys.version_info.major * 10 + sys.version_info.minor
if version < 35:
	sys.stderr.write('This program only works on Python >= 3.5\n')
	sys.exit(1)

from client import MainWindow
		
if __name__ == '__main__':
	w = MainWindow()
	w.run_main()
