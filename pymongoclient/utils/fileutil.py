import sys
import os

import pkg_resources


def locate_in_modules(filepath):
    result = pkg_resources.resource_filename("pymongoclient", filepath)
    print(result)
    return result  # return filepath #os.path.join('resources',filepath)
    """
    print(sys.path)
    for python_path in sys.path:
        full_path = os.path.join(python_path, filepath)
        if os.path.exists(full_path):
            return full_path
    return None
    """
