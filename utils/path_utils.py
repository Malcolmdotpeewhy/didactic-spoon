import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = getattr(sys, '_MEIPASS', None)
    if base_path is None:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)
