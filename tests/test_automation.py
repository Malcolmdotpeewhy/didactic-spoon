import unittest
from unittest.mock import MagicMock

# Assuming the class exists in the module as specified by the issue
try:
    from services.automation import AutomationEngine
except ImportError:
    class AutomationEngine:
        pass

class TestAutomationEngineReadyCheck(unittest.TestCase):
    def setUp(self):
        # Instantiate without calling __init__ in case the signature is unknown
        self.logic = AutomationEngine.__new__(AutomationEngine)

        # Mock the api dependency and its request method
        self.logic.api = MagicMock()

        # Mock the internal _log method to verify logging
        self.logic._log = MagicMock()

    def test_handle_ready_check_not_in_progress(self):
        # Call with a phase that is not "InProgress"
        self.logic._handle_ready_check("Lobby")

        # api.request should not be called
        self.logic.api.request.assert_not_called()
        self.logic._log.assert_not_called()

    def test_handle_ready_check_in_progress_status_200(self):
        # Setup the mock to return status 200
        self.logic.api.request.return_value = (200, None)

        # Call with "InProgress"
        self.logic._handle_ready_check("InProgress")

        # Verify the api request was made with correct arguments
        self.logic.api.request.assert_called_once_with("POST", "/lol-matchmaking/v1/ready-check/accept")

        # Verify logging was triggered
        self.logic._log.assert_called_once_with("Match accepted")

    def test_handle_ready_check_in_progress_status_204(self):
        # Setup the mock to return status 204
        self.logic.api.request.return_value = (204, None)

        # Call with "InProgress"
        self.logic._handle_ready_check("InProgress")

        # Verify the api request was made
        self.logic.api.request.assert_called_once_with("POST", "/lol-matchmaking/v1/ready-check/accept")

        # Verify logging was triggered
        self.logic._log.assert_called_once_with("Match accepted")

    def test_handle_ready_check_in_progress_other_status(self):
        # Setup the mock to return a non-success status, e.g., 500
        self.logic.api.request.return_value = (500, None)

        # Call with "InProgress"
        self.logic._handle_ready_check("InProgress")

        # Verify the api request was still made
        self.logic.api.request.assert_called_once_with("POST", "/lol-matchmaking/v1/ready-check/accept")

        # Verify logging was NOT triggered
        self.logic._log.assert_not_called()

if __name__ == '__main__':
    unittest.main()
