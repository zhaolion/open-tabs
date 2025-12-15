import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_logger = logging.getLogger("TabAPI")


def get_logger(name: str):
    """
    Get a logger with the specified name under the TabAPI namespace.

    This function creates or retrieves a logger with the name 'TabAPI.<name>',
    making it a child of the main TabAPI logger. Child loggers inherit the
    configuration (level, handlers) from the parent logger.

    Args:
        name: The name for the logger. This will be prefixed with 'TabAPI.'
              to create a hierarchical logger structure.

    Returns:
        logging.Logger: A logger instance with the name 'TabAPI.<name>'.

    Example:
        >>> from tabapi.logger import get_logger
        >>> logger = get_logger('provider')
        >>> logger.info('Provider initialized')  # Logs as 'TabAPI.provider'
        >>>
        >>> # Use different loggers for different modules
        >>> router_logger = get_logger('router')
        >>> agent_logger = get_logger('agent')

    Note:
        - All child loggers inherit settings from the main TabAPI logger
        - Use descriptive names like 'provider', 'router', 'agent' for clarity
        - Logger hierarchy helps with filtering and debugging
    """
    return logging.getLogger(f"TabAPI.{name}")


def set_log_level(level):
    """
    Set the logging level for the TabAPI logger and all its handlers.

    This function updates the logging level for both the main logger and all
    attached handlers (console, file, etc.). Messages below this level will
    be ignored.

    Args:
        level: The logging level to set. Can be either:
               - String: 'NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
                 (case-insensitive)
               - Integer: logging.DEBUG (10), logging.INFO (20), etc.

    Raises:
        ValueError: If the level is not a valid string or integer.

    Example:
        >>> from tabapi.logger import set_log_level
        >>> # Using string (case-insensitive)
        >>> set_log_level('DEBUG')    # Show all messages
        >>> set_log_level('warning')  # Show WARNING, ERROR, CRITICAL only
        >>>
        >>> # Using logging constants
        >>> import logging
        >>> set_log_level(logging.INFO)

    Logging Levels (from lowest to highest):
        - NOTSET (0): All messages
        - DEBUG (10): Detailed information for diagnosing problems
        - INFO (20): Confirmation that things are working as expected
        - WARNING (30): Something unexpected happened, but still working
        - ERROR (40): A more serious problem occurred
        - CRITICAL (50): A serious error, program may not continue

    Note:
        - Also updates all existing handlers to the same level
        - Can also be set via environment variable: TabAPI_LOGGING_LEVEL
        - Changes affect the main logger and all child loggers
    """
    valid_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    # Validate and normalize the level
    if isinstance(level, str):
        if level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid logging level. Choose from: {', '.join(valid_levels)}"
            )
        level = level.upper()
    elif not isinstance(level, int):
        raise ValueError("Logging level must be an option from the logging module.")

    # Set level on the main logger
    _logger.setLevel(level)

    # Update level for all handlers to ensure consistency
    for handler in _logger.handlers:
        try:
            handler.setLevel(level)
        except Exception as e:
            _logger.warning(f"Failed to set level on handler {handler}: {e}")

    _logger.debug(f"Logging level set to: {_logger.level}")


def setup_file_logging(
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB default
    backup_count: int = 5,
    log_format: Optional[str] = None,
    level: Optional[str] = None,
    mode: str = "a",
    encoding: str = "utf-8",
):
    """
    Configure file-based logging with automatic rotation.

    Args:
        log_file: Path to the log file. Parent directories will be created if they don't exist.
        max_bytes: Maximum size in bytes before the file is rotated. Default: 10MB (10485760 bytes).
                  Set to 0 to disable size-based rotation.
        backup_count: Number of backup files to keep. Default: 5.
                     If backup_count is 0, no rotation occurs (only one file is kept).
        log_format: Custom log format string. If None, uses default format:
                   '%(asctime)s %(name)s %(levelname)s %(message)s'
        level: Logging level for the file handler (DEBUG, INFO, WARNING, ERROR, CRITICAL).
              If None, inherits from the logger's effective level.
        mode: File opening mode. Default: 'a' (append). Use 'w' to overwrite.
        encoding: File encoding. Default: 'utf-8'.

    Returns:
        RotatingFileHandler: The configured file handler that was added to the logger.
                            If a handler for this file already exists, returns the existing handler.

    Raises:
        ValueError: If log_file is empty or invalid.
        OSError: If unable to create log directory or file.

    Example:
        >>> from tabapi.logger import setup_file_logging
        >>> # Basic usage with defaults (10MB max, 5 backups)
        >>> setup_file_logging('logs/app.log')
        >>>
        >>> # Custom configuration
        >>> setup_file_logging(
        ...     log_file='logs/debug.log',
        ...     max_bytes=50 * 1024 * 1024,  # 50MB
        ...     backup_count=10,
        ...     level='DEBUG',
        ...     log_format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ... )

    Note:
        - Log files will be named: app.log, app.log.1, app.log.2, etc.
        - When max_bytes is reached, app.log -> app.log.1, and a new app.log is created.
        - Oldest backup (app.log.{backup_count}) is deleted when limit is reached.
        - Calling this function multiple times with the same file path will return the existing handler.
    """
    if not log_file:
        raise ValueError("log_file cannot be empty")

    # Normalize the file path for comparison
    normalized_path = os.path.abspath(log_file)

    # Check for existing file handler to the same file
    for handler in _logger.handlers:
        if isinstance(handler, (logging.FileHandler, RotatingFileHandler)):
            if os.path.abspath(handler.baseFilename) == normalized_path:
                _logger.info(f"File handler already exists for: {log_file}")
                return handler

    # Ensure parent directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Set default format if not provided
    if log_format is None:
        log_format = "%(asctime)s %(name)s %(levelname)s %(message)s"

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        filename=normalized_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        mode=mode,
        encoding=encoding,
    )

    # Set formatter
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)

    # Set level
    if level is not None:
        valid_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level_upper = level.upper()
        if level_upper not in valid_levels:
            raise ValueError(
                f"Invalid logging level: {level}. "
                f"Choose from: {', '.join(valid_levels)}"
            )
        file_handler.setLevel(level_upper)
    else:
        # Use effective level instead of direct level access
        file_handler.setLevel(_logger.getEffectiveLevel())

    # Add handler to logger
    _logger.addHandler(file_handler)

    _logger.info(
        f"File logging configured: {log_file} "
        f"(max_bytes={max_bytes}, backup_count={backup_count})"
    )

    return file_handler


def disable_logging():
    """
    Disable all logging output for the TabAPI logger.

    This function completely disables logging by:
    1. Setting the environment variable TabAPI_LOGGING_DISABLED='true'
    2. Setting log level to CRITICAL + 1 (above all standard levels)
    3. Adding a NullHandler to suppress "no handlers found" warnings

    To re-enable logging, call enable_logging().

    Example:
        >>> from tabapi.logger import disable_logging, enable_logging
        >>> disable_logging()  # No more log output
        >>> # ... your code ...
        >>> enable_logging()   # Resume logging

    Note:
        - This affects the main TabAPI logger and all child loggers
        - Environment variable is updated for consistency
        - Adds NullHandler only if not already present
        - All handlers remain attached but inactive
    """
    # Update environment variable to reflect disabled state
    os.environ["TabAPI_LOGGING_DISABLED"] = "true"

    # Set level above CRITICAL to block all messages
    _logger.setLevel(logging.CRITICAL + 1)

    # Add NullHandler to suppress "no handlers found" warnings
    # Check to avoid adding multiple NullHandlers
    if not any(
        isinstance(handler, logging.NullHandler) for handler in _logger.handlers
    ):
        _logger.addHandler(logging.NullHandler())


def enable_logging():
    """
    Enable logging output for the TabAPI logger.

    This function re-enables logging by:
    1. Setting the environment variable TabAPI_LOGGING_DISABLED='false'
    2. Reconfiguring the logger with default or existing settings

    If logging is already configured, this function preserves the existing
    configuration. Otherwise, it applies default settings.

    Example:
        >>> from tabapi.logger import disable_logging, enable_logging
        >>> disable_logging()  # No more log output
        >>> # ... your code ...
        >>> enable_logging()   # Resume logging

    Note:
        - This affects the main TabAPI logger and all child loggers
        - Reconfigures the logger if it was previously disabled
        - Respects existing configuration if already set up
        - Environment variable is updated for consistency
    """
    # Update environment variable to reflect enabled state
    os.environ["TabAPI_LOGGING_DISABLED"] = "false"

    # Reconfigure the logger with default settings
    _configure_logger()


def _configure_logger():
    """
    Internal function to configure the TabAPI logger with default settings.

    This function is automatically called when the module is imported. It sets up
    basic console logging with sensible defaults if no handlers are configured.

    Behavior:
        - If TabAPI_LOGGING_DISABLED=true, logging is completely disabled
        - If no handlers exist, configures console output to stdout
        - If handlers already exist, respects existing configuration
        - Default level: WARNING (can be overridden via TabAPI_LOGGING_LEVEL)
        - Default format: '%(asctime)s %(name)s %(levelname)s %(message)s'

    Environment Variables:
        TabAPI_LOGGING_DISABLED: Set to 'true' to disable all logging
        TabAPI_LOGGING_LEVEL: Set default logging level (DEBUG, INFO, WARNING, etc.)

    Note:
        - This is an internal function (prefix: _) not intended for direct use
        - Called automatically at module import time
        - Respects existing logger configuration to avoid conflicts
        - Users should use set_log_level() or setup_file_logging() for customization
    """
    # Check if logging is disabled via environment variable
    if os.environ.get("TabAPI_LOGGING_DISABLED", "False").lower() == "true":
        return

    # Only configure if no handlers exist (avoid overriding user configuration)
    if not logging.root.handlers and not _logger.handlers:
        logging.basicConfig(
            level=os.environ.get("TabAPI_LOGGING_LEVEL", "WARNING").upper(),
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
            stream=sys.stdout,
        )
        logging.setLoggerClass(logging.Logger)
        _logger.info(
            f"TabAPI library logging has been configured "
            f"(level: {_logger.getEffectiveLevel()}). "
            f"To change level, use set_log_level() or "
            "set TabAPI_LOGGING_LEVEL env var. To disable logging, "
            "set TabAPI_LOGGING_DISABLED=true or use disable_logging()"
        )
    else:
        _logger.debug("Existing logger configuration found, using that.")


if os.environ.get("TabAPI_LOGGING_DISABLED", "False").strip().lower() != "true":
    _configure_logger()
