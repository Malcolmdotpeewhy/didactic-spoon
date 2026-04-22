import unittest
from unittest.mock import MagicMock, patch

# AutomationLogic seems to be an old class name. The actual class is AutomationEngine.
from services.automation import AutomationEngine

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
        self.logic.toast_func = MagicMock()
        self.logic.ready_check_start = None
        self.logic.ready_check_delay = 2.0
        self.logic.poro_snack_func = None
        self.logic._accept_timer = None
        self.logic.queue_func = MagicMock()

    def test_handle_ready_check_not_in_progress(self):
        # Call with a phase that is not "ReadyCheck"
        self.logic._handle_ready_check("Lobby")

        # api.request should not be called
        self.logic.lcu.request.assert_not_called()
        self.logic._log.assert_not_called()

    @patch("threading.Timer")
    @patch("time.time", return_value=100)
    def test_handle_ready_check_in_progress_status_200(self, mock_time, mock_timer):
        self.logic.config.get.return_value = True # auto_accept
        mock_timer_instance = MagicMock()
        mock_timer.return_value = mock_timer_instance

        # Call with "ReadyCheck" - starts timer
        self.logic._handle_ready_check("ReadyCheck")

        # Get the callback function passed to Timer
        callback = mock_timer.call_args[0][1]

        # Execute the callback directly to simulate timer firing
        callback()

        # Verify the api request was made with correct arguments
        self.logic.lcu.request.assert_called_once_with("POST", "/lol-matchmaking/v1/ready-check/accept")

        # Verify logging was triggered
        self.logic._log.assert_called_once_with("Ready Check Accepted!")

    @patch("threading.Timer")
    @patch("time.time", return_value=100)
    def test_handle_ready_check_in_progress_status_204(self, mock_time, mock_timer):
        self.logic.config.get.return_value = True # auto_accept
        mock_timer_instance = MagicMock()
        mock_timer.return_value = mock_timer_instance

        # Call with "ReadyCheck" - starts timer
        self.logic._handle_ready_check("ReadyCheck")

        # Get the callback function passed to Timer
        callback = mock_timer.call_args[0][1]

        # Execute the callback directly to simulate timer firing
        callback()

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


class TestAutomationEngineWindowState(unittest.TestCase):
    """Tests for window state transitions including stealth mode."""

    def _make_engine(self, stealth=False):
        engine = AutomationEngine.__new__(AutomationEngine)
        engine.lcu = MagicMock()
        engine.config = MagicMock()
        engine.config.get = MagicMock(side_effect=lambda key, default=None: {
            "stealth_mode": stealth,
            "auto_accept": False,
            "auto_requeue": False,
        }.get(key, default))
        engine.assets = MagicMock()
        engine.window_func = MagicMock()
        engine.log = MagicMock()
        engine._log = MagicMock()
        engine.stop_func = None
        engine.stats_func = None
        engine.toast_func = None
        engine.running = True
        engine.paused = False
        engine.setup_done = False
        engine._skin_equipped = False
        engine._requeue_handled = False
        engine._stop_event = MagicMock()
        engine.executor = MagicMock()
        engine._last_error_times = {}
        engine.last_phase = "None"
        engine.current_queue_id = None
        engine.queue_func = MagicMock()
        engine.discord_rpc = MagicMock()
        engine.ready_check_start = None
        engine.ready_check_delay = None
        engine.ready_check_accepted = False
        engine._last_countdown_log = None
        engine._last_disconnect_log = 0.0
        engine._last_priority_swap = 0.0
        engine._last_search_state_time = 0.0
        engine._cached_search_state = None
        engine._accept_timer = None
        return engine

    def test_stealth_off_sends_restore(self):
        """When stealth_mode is OFF, transitioning from InProgress → EndOfGame calls restore."""
        engine = self._make_engine(stealth=False)
        engine.last_phase = "InProgress"

        # Simulate phase data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = "EndOfGame"
        mock_future = MagicMock()
        mock_future.result.return_value = mock_response
        engine.executor.submit.return_value = mock_future

        engine._tick()

        engine.window_func.assert_called_with("restore")

    def test_stealth_on_sends_restore_quiet(self):
        """When stealth_mode is ON, transitioning from InProgress → EndOfGame calls restore_quiet."""
        engine = self._make_engine(stealth=True)
        engine.last_phase = "InProgress"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = "EndOfGame"
        mock_future = MagicMock()
        mock_future.result.return_value = mock_response
        engine.executor.submit.return_value = mock_future

        engine._tick()

        engine.window_func.assert_called_with("restore_quiet")

    def test_inprogress_always_minimizes(self):
        """Regardless of stealth mode, entering InProgress always minimizes."""
        for stealth in (True, False):
            engine = self._make_engine(stealth=stealth)
            engine.last_phase = "ChampSelect"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = "InProgress"
            mock_future = MagicMock()
            mock_future.result.return_value = mock_response
            engine.executor.submit.return_value = mock_future

            engine._tick()

            engine.window_func.assert_called_with("minimize")


if __name__ == '__main__':
    unittest.main()
