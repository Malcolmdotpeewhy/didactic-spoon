import unittest
from unittest.mock import patch
import os
import sys
from utils.path_utils import get_asset_path

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

if __name__ == '__main__':
    unittest.main()
