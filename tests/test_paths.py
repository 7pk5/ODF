import os
import sys

import pytest

from odf import paths


@pytest.fixture
def frozen(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)


def test_script_mode_uses_project_root(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # tests/ is under the root
    assert paths.app_data_dir() == project_root


def test_frozen_windows_uses_appdata(frozen, monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert paths.app_data_dir() == os.path.join(str(tmp_path), "ODF")


def test_frozen_linux_uses_xdg_data_home(frozen, monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert paths.app_data_dir() == os.path.join(str(tmp_path), "ODF")


def test_frozen_linux_defaults_to_local_share(frozen, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    expected = os.path.join(os.path.expanduser("~"), ".local", "share", "ODF")
    assert paths.app_data_dir() == expected


def test_subdirs_are_created_under_data_root(isolated_data_dir):
    assert paths.model_cache_dir() == os.path.join(str(isolated_data_dir), "models")
    assert paths.chroma_db_dir() == os.path.join(str(isolated_data_dir), "data", "chroma_db")
    assert os.path.isdir(paths.model_cache_dir())
    assert os.path.isdir(paths.chroma_db_dir())
    assert paths.log_path() == os.path.join(str(isolated_data_dir), "odf.log")
