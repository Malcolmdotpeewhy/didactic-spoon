import unittest
from unittest.mock import patch
import os
import sys
from utils.path_utils import get_asset_path, get_data_dir

class TestPathUtils(unittest.TestCase):

    def test_get_asset_path_with_meipass(self):
        # Simulate PyInstaller environment by setting sys._MEIPASS
        mock_meipass = "/tmp/_MEI123456"
        with patch.object(sys, '_MEIPASS', mock_meipass, create=True):
            result = get_asset_path("assets/image.png")
            expected = os.path.join(mock_meipass, "assets/image.png")
            self.assertEqual(result, expected)

    def test_get_asset_path_without_meipass(self):
        # Simulate normal dev environment by ensuring sys._MEIPASS is not set
        # We need to temporarily remove sys._MEIPASS if it exists
        original_has_meipass = hasattr(sys, '_MEIPASS')
        if original_has_meipass:
            original_meipass = getattr(sys, '_MEIPASS')
            del sys._MEIPASS

        try:
            result = get_asset_path("assets/image.png")
            expected = os.path.join(os.path.abspath("."), "assets/image.png")
            self.assertEqual(result, expected)
        finally:
            if original_has_meipass:
                sys._MEIPASS = original_meipass

    def test_get_data_dir_frozen_with_appdata(self):
        # Running as compiled executable with LOCALAPPDATA set
        with patch.object(sys, 'frozen', True, create=True), \
             patch.dict(os.environ, {'LOCALAPPDATA': '/mock/appdata'}):
            result = get_data_dir()
            expected = os.path.join('/mock/appdata', 'DidacticSpoon')
            self.assertEqual(result, expected)

    def test_get_data_dir_frozen_without_appdata(self):
        # Running as compiled executable without LOCALAPPDATA (fallback to expanduser('~'))
        with patch.object(sys, 'frozen', True, create=True):
            # We need to temporarily remove LOCALAPPDATA if it exists
            original_has_appdata = 'LOCALAPPDATA' in os.environ
            if original_has_appdata:
                original_appdata = os.environ['LOCALAPPDATA']
                del os.environ['LOCALAPPDATA']

            try:
                mock_home = '/mock/home'
                with patch('os.path.expanduser', return_value=mock_home):
                    result = get_data_dir()
                    expected = os.path.join(mock_home, 'DidacticSpoon')
                    self.assertEqual(result, expected)
            finally:
                if original_has_appdata:
                    os.environ['LOCALAPPDATA'] = original_appdata

    def test_get_data_dir_not_frozen(self):
        # Running as a regular script
        original_has_frozen = hasattr(sys, 'frozen')
        if original_has_frozen:
            original_frozen = getattr(sys, 'frozen')
            del sys.frozen

        try:
            result = get_data_dir()
            expected = os.path.abspath(".")
            self.assertEqual(result, expected)
        finally:
            if original_has_frozen:
                sys.frozen = original_frozen

if __name__ == '__main__':
    unittest.main()
