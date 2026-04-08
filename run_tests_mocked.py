import sys
import unittest
from unittest.mock import MagicMock

# Shim missing modules
missing_modules = [
    'customtkinter',
    'keyboard',
    'PIL', 'pillow',
    'packaging', 'packaging.version',
    'requests', 'requests.exceptions',
    'win32clipboard',
    'urllib3', 'urllib3.exceptions',
    'watchdog', 'watchdog.observers', 'watchdog.events'
]

for mod in missing_modules:
    sys.modules[mod] = MagicMock()

# Run the tests
if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
