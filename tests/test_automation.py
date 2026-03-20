import unittest
from unittest.mock import MagicMock, patch

# AutomationLogic seems to be an old class name. The actual class is AutomationEngine.
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
        self.logic.lcu = MagicMock()
        self.logic.config = MagicMock()

        # Mock the internal _log method to verify logging
        self.logic._log = MagicMock()
        self.logic.ready_check_accepted = False
        self.logic.ready_check_start = None
        self.logic.poro_snack_func = None

    def test_handle_ready_check_not_in_progress(self):
        # Call with a phase that is not "ReadyCheck"
        self.logic._handle_ready_check("Lobby")

        # api.request should not be called
        self.logic.lcu.request.assert_not_called()
        self.logic._log.assert_not_called()

    @patch("time.time", return_value=100)
    def test_handle_ready_check_in_progress_status_200(self, mock_time):
        self.logic.config.get.return_value = True # auto_accept

        # Call with "ReadyCheck" - first tick sets start time
        self.logic._handle_ready_check("ReadyCheck")

        # Advance time to pass the delay
        mock_time.return_value = 105

        # Second tick accepts
        self.logic._handle_ready_check("ReadyCheck")

        # Verify the api request was made with correct arguments
        self.logic.lcu.request.assert_called_once_with("POST", "/lol-matchmaking/v1/ready-check/accept")

        # Verify logging was triggered
        self.logic._log.assert_called_once_with("Ready Check Accepted!")

    @patch("time.time", return_value=100)
    def test_handle_ready_check_in_progress_status_204(self, mock_time):
        self.logic.config.get.return_value = True # auto_accept

        # Call with "ReadyCheck" - first tick sets start time
        self.logic._handle_ready_check("ReadyCheck")

        # Advance time to pass the delay
        mock_time.return_value = 105

        # Second tick accepts
        self.logic._handle_ready_check("ReadyCheck")

        # Verify the api request was made
        self.logic.lcu.request.assert_called_once_with("POST", "/lol-matchmaking/v1/ready-check/accept")

        # Verify logging was triggered
        self.logic._log.assert_called_once_with("Ready Check Accepted!")

    def test_handle_ready_check_in_progress_other_status(self):
        # Test when auto_accept is false
        self.logic.config.get.return_value = False # auto_accept

        # Call with "ReadyCheck"
        self.logic._handle_ready_check("ReadyCheck")

        # Verify the api request was NOT made
        self.logic.lcu.request.assert_not_called()

        # Verify logging was NOT triggered
        self.logic._log.assert_not_called()

if __name__ == '__main__':
    unittest.main()
