import unittest
from unittest.mock import patch
from services.asset_manager import AssetManager

class TestAssetManager(unittest.TestCase):

    @patch('os.path.exists', return_value=False)
    def test_get(self, mock_exists):
        """Test the get method of AssetManager."""
        manager = AssetManager()

        # Override internal state to ensure deterministic testing without relying on defaults
        manager.cfg = {
            "test_key": "test_value",
            "another_key": 42
        }

        # Test getting an existing key
        self.assertEqual(manager.get("test_key"), "test_value")
        self.assertEqual(manager.get("another_key"), 42)

        # Test getting a non-existent key, should return None by default
        self.assertIsNone(manager.get("non_existent_key"))

        # Test getting a non-existent key with a custom default value
        self.assertEqual(manager.get("non_existent_key", "custom_default"), "custom_default")

if __name__ == '__main__':
    unittest.main()
