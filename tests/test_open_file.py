import os

import pytest

from utils import open_file as opener


@pytest.fixture
def existing_file(tmp_path):
    p = tmp_path / "doc.pdf"
    p.write_bytes(b"x")
    return str(p)


def test_missing_file_is_not_opened(tmp_path):
    assert opener.open_file(str(tmp_path / "nope.pdf")) is False


def test_linux_uses_xdg_open(existing_file, monkeypatch):
    calls = []
    monkeypatch.setattr(opener.platform, "system", lambda: "Linux")
    monkeypatch.setattr(opener.subprocess, "run", lambda cmd, **kw: calls.append(cmd))
    assert opener.open_file(existing_file) is True
    assert calls == [["xdg-open", existing_file]]


def test_windows_uses_startfile(existing_file, monkeypatch):
    calls = []
    monkeypatch.setattr(opener.platform, "system", lambda: "Windows")
    monkeypatch.setattr(os, "startfile", calls.append, raising=False)
    assert opener.open_file(existing_file) is True
    assert calls == [existing_file]


def test_opener_failure_returns_false(existing_file, monkeypatch):
    def boom(cmd, **kw):
        raise FileNotFoundError("xdg-open not installed")

    monkeypatch.setattr(opener.platform, "system", lambda: "Linux")
    monkeypatch.setattr(opener.subprocess, "run", boom)
    assert opener.open_file(existing_file) is False
