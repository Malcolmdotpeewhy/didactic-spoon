"""
Logger Module
Handles application logging to file and console using standard logging module.
"""
import logging
from logging.handlers import RotatingFileHandler

# Set up the Python rotating file logger
_log_format = '[%(asctime)s.%(msecs)03d] [%(threadName)s] %(message)s'
_date_format = '%H:%M:%S'

formatter = logging.Formatter(_log_format, datefmt=_date_format)

# Main Logger
_logger = logging.getLogger("AutoLock")
_logger.setLevel(logging.DEBUG)

if not _logger.handlers:
    # File Handler - ALL Logs (5MB max size, keeps 3 backups)
    file_handler = RotatingFileHandler(
        'debug.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Error File Handler - ERROR/CRITICAL Logs Only
    error_handler = RotatingFileHandler(
        'error.log', maxBytes=2*1024*1024, backupCount=2, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    
    _logger.addHandler(file_handler)
    _logger.addHandler(error_handler)
    _logger.addHandler(console_handler)

class Logger:
    """Provides backwards compatibility with the legacy custom logger."""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def init_logger(self):
        """Kept for backward compatibility if instantiated directly."""

    def log(self, tag, message):
        """Log a debug message."""
        _logger.debug(f"[{tag}] {message}")

    @staticmethod
    def debug(tag, msg):
        """Log a debug message."""
        _logger.debug(f"[{tag}] {msg}")

    @classmethod
    def get_logs(cls, module=None, limit=100):
        cls._prune()
        if limit <= 0:
            return []
        if module:
            filtered = [log for log in cls._logs if log["module"] == module]
            return filtered[-limit:]
        return cls._logs[-limit:]

    @staticmethod
    def error(tag, msg):
        """Log an error message."""
        _logger.error(f"[ERROR:{tag}] {msg}")

    @staticmethod
    def info(tag, msg):
        """Log an info message."""
        _logger.info(f"[{tag}] {msg}")

    @staticmethod
    def warning(tag, msg):
        """Log a warning message."""
        _logger.warning(f"[{tag}] {msg}")

# Kept for backward compatibility — routes to Logger.debug
def log(tag, msg):
    """Module-level log helper function. Prefer Logger.debug() directly."""
    Logger.debug(tag, msg)
