"""Logging setup: odf.log in the data dir, plus the console when run from source."""

import logging
import sys

from odf import paths

LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'

# Libraries that log every HTTP request of the first-run model download at INFO
QUIET_LOGGERS = ('httpx', 'huggingface_hub')


def setup_logging():
    """Route all log records to odf.log (and stdout in script mode). Returns the log path."""
    log_path = paths.log_path()
    frozen = getattr(sys, 'frozen', False)

    # In windowed EXE mode sys.stdout/stderr are None.
    # Redirect both to the log file so tqdm/fastembed/chromadb don't crash
    # when they try to print download progress or status messages.
    if frozen and sys.stdout is None:
        _f = open(log_path, 'a', encoding='utf-8', buffering=1)
        sys.stdout = _f
        sys.stderr = _f

    handlers = [logging.FileHandler(log_path, encoding='utf-8')]
    if not frozen:
        handlers.append(logging.StreamHandler(sys.stdout))

    # Attach handlers directly: logging.basicConfig() silently does nothing
    # if a library has already added a handler to the root logger.
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)
    for handler in handlers:
        handler.setFormatter(formatter)
        root.addHandler(handler)
    for name in QUIET_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    return log_path
