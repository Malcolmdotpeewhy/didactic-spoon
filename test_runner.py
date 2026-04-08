import sys
import unittest
from unittest.mock import MagicMock

# Shim missing dependencies
for mod in ['psutil', 'requests', 'keyboard', 'customtkinter', 'PIL', 'packaging', 'win32clipboard', 'urllib3', 'watchdog', 'tkinterdnd2']:
    sys.modules[mod] = MagicMock()

if __name__ == '__main__':
    # Add src to path
    import os
    sys.path.insert(0, os.path.abspath('src'))

    loader = unittest.TestLoader()
    suite = loader.discover('tests')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())
