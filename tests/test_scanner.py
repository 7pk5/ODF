import logging
import os
import sys

import pytest

from odf.index import scanner


def _rel(paths, root):
    return sorted(os.path.relpath(p, root).replace(os.sep, "/") for p in paths)


def test_scan_finds_supported_files_case_insensitively(tmp_path):
    for name in ("a.pdf", "B.PDF", "c.docx", "notes.txt", "sheet.xlsx", "old.doc"):
        (tmp_path / name).write_bytes(b"x")
    assert _rel(scanner.scan_directory(str(tmp_path)), tmp_path) == ["B.PDF", "a.pdf", "c.docx"]


def test_scan_recurses_but_skips_hidden_and_dev_folders(tmp_path):
    for folder in ("reports/2024", ".git", "node_modules/pkg", "__pycache__", "venv"):
        (tmp_path / folder).mkdir(parents=True)
        (tmp_path / folder / "doc.pdf").write_bytes(b"x")
    assert _rel(scanner.scan_directory(str(tmp_path)), tmp_path) == ["reports/2024/doc.pdf"]


def test_scan_logs_how_many_files_it_found(tmp_path, caplog):
    (tmp_path / "a.pdf").write_bytes(b"x")
    with caplog.at_level(logging.INFO, logger="odf"):
        scanner.scan_directory(str(tmp_path))
    assert "Found 1 supported files to scan." in caplog.messages


def test_scan_missing_folder_raises(tmp_path):
    with pytest.raises(ValueError):
        scanner.scan_directory(str(tmp_path / "does-not-exist"))


@pytest.mark.skipif(sys.platform == "win32", reason="creating symlinks needs admin/dev mode on Windows")
@pytest.mark.xfail(strict=True, reason="B7: os.walk(followlinks=True) re-scans the same files through symlink loops")
def test_symlink_loop_does_not_duplicate_files(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "report.pdf").write_bytes(b"x")
    os.symlink("..", tmp_path / "docs" / "loop")
    assert len(scanner.scan_directory(str(tmp_path))) == 1
