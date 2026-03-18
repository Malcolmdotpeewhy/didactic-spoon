import unittest
from unittest.mock import Mock
from utils.logger import Logger

class TestLoggerGetLogs(unittest.TestCase):
    def setUp(self):
        # Mock _logs and _prune specifically for testing without altering production codebase permanently
        self.original_logs = getattr(Logger, '_logs', None)
        self.original_prune = getattr(Logger, '_prune', None)

        Logger._logs = []
        Logger._prune = Mock()

    def tearDown(self):
        # Restore original attributes
        if self.original_logs is not None:
            Logger._logs = self.original_logs
        else:
            delattr(Logger, '_logs')

        if self.original_prune is not None:
            Logger._prune = self.original_prune
        else:
            delattr(Logger, '_prune')

    def test_get_logs_empty(self):
        """Test getting logs when the list is empty."""
        logs = Logger.get_logs()
        self.assertEqual(logs, [])
        Logger._prune.assert_called_once()

    def test_get_logs_no_filter_no_limit(self):
        """Test getting all logs without module filter and default limit."""
        Logger._logs.extend([
            {"module": "core", "msg": "test1"},
            {"module": "ui", "msg": "test2"},
            {"module": "core", "msg": "test3"},
        ])
        logs = Logger.get_logs()
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0]["msg"], "test1")
        self.assertEqual(logs[2]["msg"], "test3")

    def test_get_logs_with_limit(self):
        """Test getting logs with a specific limit."""
        Logger._logs.extend([
            {"module": "core", "msg": "test1"},
            {"module": "ui", "msg": "test2"},
            {"module": "core", "msg": "test3"},
        ])
        logs = Logger.get_logs(limit=2)
        self.assertEqual(len(logs), 2)
        # Should get the last 2 logs
        self.assertEqual(logs[0]["msg"], "test2")
        self.assertEqual(logs[1]["msg"], "test3")

    def test_get_logs_with_module_filter(self):
        """Test filtering logs by module."""
        Logger._logs.extend([
            {"module": "core", "msg": "test1"},
            {"module": "ui", "msg": "test2"},
            {"module": "core", "msg": "test3"},
        ])
        logs = Logger.get_logs(module="core")
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]["msg"], "test1")
        self.assertEqual(logs[1]["msg"], "test3")

    def test_get_logs_with_module_filter_and_limit(self):
        """Test filtering logs by module and applying a limit."""
        Logger._logs.extend([
            {"module": "core", "msg": "test1"},
            {"module": "ui", "msg": "test2"},
            {"module": "core", "msg": "test3"},
            {"module": "core", "msg": "test4"},
        ])
        logs = Logger.get_logs(module="core", limit=2)
        self.assertEqual(len(logs), 2)
        # Should get the last 2 'core' logs
        self.assertEqual(logs[0]["msg"], "test3")
        self.assertEqual(logs[1]["msg"], "test4")

    def test_get_logs_module_not_found(self):
        """Test getting logs for a module that has no logs."""
        Logger._logs.extend([
            {"module": "core", "msg": "test1"},
            {"module": "ui", "msg": "test2"},
        ])
        logs = Logger.get_logs(module="network")
        self.assertEqual(logs, [])

    def test_get_logs_zero_limit(self):
        """Test getting logs with a limit of 0."""
        Logger._logs.extend([
            {"module": "core", "msg": "test1"},
            {"module": "ui", "msg": "test2"},
        ])
        logs = Logger.get_logs(limit=0)
        self.assertEqual(logs, [])

if __name__ == '__main__':
    unittest.main()
