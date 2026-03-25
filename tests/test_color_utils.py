import sys
import unittest
from unittest.mock import patch, MagicMock

# Mock dependencies before importing the module under test
patch.dict(sys.modules, {
    'customtkinter': MagicMock(),
    'tkinter': MagicMock(),
    'PIL': MagicMock(),
    'PIL.Image': MagicMock(),
    'PIL.ImageTk': MagicMock()
}).start()

from ui.components.color_utils import hex_to_rgb, darken_color
import utils.logger

class TestColorUtils(unittest.TestCase):
    def test_hex_to_rgb_6_char(self):
        """Test with standard 6-character hex string with leading #"""
        self.assertEqual(hex_to_rgb("#FFFFFF"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("#000000"), (0, 0, 0))
        self.assertEqual(hex_to_rgb("#FF0000"), (255, 0, 0))
        self.assertEqual(hex_to_rgb("#00FF00"), (0, 255, 0))
        self.assertEqual(hex_to_rgb("#0000FF"), (0, 0, 255))
        self.assertEqual(hex_to_rgb("#1A2B3C"), (26, 43, 60))

    def test_hex_to_rgb_6_char_no_hash(self):
        """Test with 6-character hex string without leading #"""
        self.assertEqual(hex_to_rgb("FFFFFF"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("000000"), (0, 0, 0))
        self.assertEqual(hex_to_rgb("1A2B3C"), (26, 43, 60))

    def test_hex_to_rgb_3_char(self):
        """Test with 3-character hex string with leading #"""
        self.assertEqual(hex_to_rgb("#FFF"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("#000"), (0, 0, 0))
        self.assertEqual(hex_to_rgb("#F00"), (255, 0, 0))
        self.assertEqual(hex_to_rgb("#123"), (17, 34, 51))

    def test_hex_to_rgb_3_char_no_hash(self):
        """Test with 3-character hex string without leading #"""
        self.assertEqual(hex_to_rgb("FFF"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("000"), (0, 0, 0))
        self.assertEqual(hex_to_rgb("123"), (17, 34, 51))

    def test_hex_to_rgb_invalid_length(self):
        """Test with invalid hex string lengths"""
        with self.assertRaises(ValueError):
            hex_to_rgb("#FF") # Length 2
        with self.assertRaises(ValueError):
            hex_to_rgb("#FFFF") # Length 4
        with self.assertRaises(ValueError):
            hex_to_rgb("FFFFF") # Length 5
        with self.assertRaises(ValueError):
            hex_to_rgb("#FFFFFFF") # Length 7

    def test_hex_to_rgb_invalid_chars(self):
        """Test with invalid characters in hex string"""
        with self.assertRaises(ValueError):
            hex_to_rgb("#ZZZZZZ")
        with self.assertRaises(ValueError):
            hex_to_rgb("GHIJKL")

    def test_darken_color_standard(self):
        """Test default 10% darkening"""
        # #FFFFFF (255, 255, 255) darkened by 10% (factor = 0.9) should be #e5e5e5 (229, 229, 229)
        self.assertEqual(darken_color("#FFFFFF"), "#e5e5e5")

        # #FF0000 (255, 0, 0) darkened by 10% should be #e50000
        self.assertEqual(darken_color("#FF0000"), "#e50000")

    def test_darken_color_percent(self):
        """Test specific percentages"""
        # 50% darken: #FFFFFF -> #7f7f7f (127)
        self.assertEqual(darken_color("#FFFFFF", percent=50), "#7f7f7f")

        # 100% darken: #FFFFFF -> #000000
        self.assertEqual(darken_color("#FFFFFF", percent=100), "#000000")

        # 0% darken: #FFFFFF -> #ffffff (case changed by string formatting)
        self.assertEqual(darken_color("#FFFFFF", percent=0), "#ffffff")

    def test_darken_color_transparent(self):
        """Test 'transparent' returns the same string"""
        self.assertEqual(darken_color("transparent"), "transparent")

    @patch('utils.logger.Logger.error')
    def test_darken_color_exception(self, mock_logger_error):
        """Test invalid color string handles exception gracefully"""
        # Should return original input and log an error
        result = darken_color("invalid_hex")
        self.assertEqual(result, "invalid_hex")

        mock_logger_error.assert_called_once()
        self.assertEqual(mock_logger_error.call_args[0][0], "color_utils.py")
        self.assertTrue(mock_logger_error.call_args[0][1].startswith("Handled exception:"))

if __name__ == '__main__':
    unittest.main()
