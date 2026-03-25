import unittest
from unittest.mock import MagicMock, patch
import sys

class TestUIFactory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a dictionary of mocks for modules that might not be available
        cls.module_patcher = patch.dict(sys.modules, {
            'customtkinter': MagicMock(),
            'tkinter': MagicMock(),
            'utils.logger': MagicMock(),
            'PIL': MagicMock(),
            'PIL.Image': MagicMock(),
        })
        cls.module_patcher.start()

        # Mock TOKENS to avoid loading design_tokens.json
        with patch('ui.theme.token_loader.TOKENS', MagicMock()):
            from ui.components.factory import UIFactory
            cls.UIFactory = UIFactory

    @classmethod
    def tearDownClass(cls):
        cls.module_patcher.stop()

    @patch('ui.components.cards.Card')
    def test_create_card(self, mock_card):
        # Setup
        parent = MagicMock()
        variant = "default"
        extra_kwarg = "extra"

        # Action
        result = self.UIFactory.create_card(parent, variant=variant, custom_param=extra_kwarg)

        # Assert
        mock_card.assert_called_once_with(parent, variant=variant, custom_param=extra_kwarg)
        self.assertEqual(result, mock_card.return_value)

    @patch('ui.components.cards.Card')
    def test_create_card_different_variant(self, mock_card):
        # Setup
        parent = MagicMock()
        variant = "elevated"

        # Action
        result = self.UIFactory.create_card(parent, variant=variant)

        # Assert
        mock_card.assert_called_once_with(parent, variant=variant)
        self.assertEqual(result, mock_card.return_value)
