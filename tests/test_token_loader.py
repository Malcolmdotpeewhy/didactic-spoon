import unittest
import json
from unittest.mock import mock_open, patch

from ui.theme.token_loader import DesignTokens, DEFAULT_TOKENS

class TestTokenLoader(unittest.TestCase):

    @patch('builtins.open', new_callable=mock_open, read_data='{"colors": {"primary": "#ffffff"}}')
    def test_load_tokens_success(self, mock_file):
        tokens = DesignTokens()
        self.assertEqual(tokens.tokens, {"colors": {"primary": "#ffffff"}})
        mock_file.assert_called_once()

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_tokens_file_not_found(self, mock_file):
        tokens = DesignTokens()
        self.assertEqual(tokens.tokens, DEFAULT_TOKENS)
        mock_file.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_tokens_invalid_json(self, mock_file):
        tokens = DesignTokens()
        self.assertEqual(tokens.tokens, DEFAULT_TOKENS)
        mock_file.assert_called_once()

if __name__ == '__main__':
    unittest.main()
