import sys
import os

import pkg_resources


def locate_in_modules(filepath):
    return pkg_resources.resource_filename("pymongoclient", filepath)
