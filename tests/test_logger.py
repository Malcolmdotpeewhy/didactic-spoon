import unittest
from unittest.mock import patch
from utils.logger import Logger

class TestLogger(unittest.TestCase):

    @patch('utils.logger._logger')
    def test_debug(self, mock_logger):
        Logger.debug("TestTag", "This is a debug message.")
        mock_logger.debug.assert_called_once_with("[TestTag] This is a debug message.")

    @patch('utils.logger._logger')
    def test_error(self, mock_logger):
        Logger.error("TestTag", "This is an error message.")
        mock_logger.error.assert_called_once_with("[TestTag] This is an error message.")

    @patch('utils.logger._logger')
    def test_info(self, mock_logger):
        Logger.info("TestTag", "This is an info message.")
        mock_logger.info.assert_called_once_with("[TestTag] This is an info message.")

    @patch('utils.logger._logger')
    def test_warning(self, mock_logger):
        Logger.warning("TestTag", "This is a warning message.")
        mock_logger.warning.assert_called_once_with("[TestTag] This is a warning message.")

if __name__ == '__main__':
    unittest.main()
