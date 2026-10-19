import logging

import pytest

from odf import paths
from odf.logging_setup import setup_logging


@pytest.fixture
def restore_root_logger():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    for h in root.handlers[:]:
        if h not in handlers:
            root.removeHandler(h)
            h.close()
    root.setLevel(level)
    for name in ("httpx", "huggingface_hub"):
        logging.getLogger(name).setLevel(logging.NOTSET)


def test_setup_logging_writes_to_odf_log(isolated_data_dir, restore_root_logger):
    log_path = setup_logging()
    assert log_path == paths.log_path()

    logging.getLogger("odf.test").info("hello from a test")
    for h in logging.getLogger().handlers:
        h.flush()

    with open(log_path, encoding="utf-8") as f:
        assert "INFO odf.test: hello from a test" in f.read()


def test_http_request_noise_is_kept_out_of_the_log(isolated_data_dir, restore_root_logger):
    setup_logging()
    assert not logging.getLogger("httpx").isEnabledFor(logging.INFO)
    assert logging.getLogger("huggingface_hub.utils._http").isEnabledFor(logging.WARNING)
    assert logging.getLogger("odf.index.store").isEnabledFor(logging.INFO)
