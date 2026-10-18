import hashlib
import os
import sys

import pytest

from odf.index.file_indexer import FileIndexer
from tests.helpers import bump_mtime, make_docx, make_pdf


@pytest.fixture
def indexer():
    return FileIndexer()


def _rel(paths, root):
    return sorted(os.path.relpath(p, root).replace(os.sep, "/") for p in paths)


# ── Scanning ─────────────────────────────────────────────────────

def test_scan_finds_supported_files_case_insensitively(indexer, tmp_path):
    for name in ("a.pdf", "B.PDF", "c.docx", "notes.txt", "sheet.xlsx", "old.doc"):
        (tmp_path / name).write_bytes(b"x")
    assert _rel(indexer.scan_directory(str(tmp_path)), tmp_path) == ["B.PDF", "a.pdf", "c.docx"]


def test_scan_recurses_but_skips_hidden_and_dev_folders(indexer, tmp_path):
    for folder in ("reports/2024", ".git", "node_modules/pkg", "__pycache__", "venv"):
        (tmp_path / folder).mkdir(parents=True)
        (tmp_path / folder / "doc.pdf").write_bytes(b"x")
    assert _rel(indexer.scan_directory(str(tmp_path)), tmp_path) == ["reports/2024/doc.pdf"]


def test_scan_missing_folder_raises(indexer, tmp_path):
    with pytest.raises(ValueError):
        indexer.scan_directory(str(tmp_path / "does-not-exist"))


@pytest.mark.skipif(sys.platform == "win32", reason="creating symlinks needs admin/dev mode on Windows")
@pytest.mark.xfail(strict=True, reason="B7: os.walk(followlinks=True) re-scans the same files through symlink loops")
def test_symlink_loop_does_not_duplicate_files(indexer, tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "report.pdf").write_bytes(b"x")
    os.symlink("..", tmp_path / "docs" / "loop")
    assert len(indexer.scan_directory(str(tmp_path))) == 1


# ── Extraction ───────────────────────────────────────────────────

def test_extracts_docx_paragraphs_and_tables(indexer, tmp_path):
    path = make_docx(
        tmp_path / "invoice.docx",
        paragraphs=["Invoice INV-2024-001", "Payment due in 30 days"],
        table=[["Item", "Price"], ["Consulting", "1200"]],
    )
    text = indexer._extract_content(path, ".docx")
    for expected in ("INV-2024-001", "Payment due in 30 days", "Consulting", "1200"):
        assert expected in text


def test_extracts_pdf_text(indexer, tmp_path):
    path = make_pdf(tmp_path / "memo.pdf", "Quarterly budget report for marketing")
    assert "Quarterly budget report for marketing" in indexer._extract_content(path, ".pdf")


def test_corrupt_file_extracts_to_empty_string(indexer, tmp_path):
    bad = tmp_path / "broken.pdf"
    bad.write_bytes(b"not really a pdf")
    assert indexer._extract_content(str(bad), ".pdf") == ""


def test_clean_text_collapses_whitespace_strips_control_chars_and_caps_length(indexer):
    assert indexer._clean_text("a \n\n b\t\x00c\x07") == "a b c"
    assert len(indexer._clean_text("x" * 150_000)) == 100_000


# ── process_files ────────────────────────────────────────────────

def test_process_files_returns_documents_with_metadata(indexer, tmp_path):
    path = make_docx(tmp_path / "plan.docx", paragraphs=["Roadmap for next year"])
    [doc] = list(indexer.process_files([path]))

    st = os.stat(path)
    assert doc["id"] == hashlib.md5(f"{path}_{st.st_mtime}".encode()).hexdigest()
    assert "Roadmap for next year" in doc["content"]
    assert doc["metadata"] == {
        "source": path,
        "filename": "plan.docx",
        "modified": st.st_mtime,
        "size": st.st_size,
        "type": ".docx",
    }


def test_process_files_skips_already_indexed_and_reprocesses_modified(indexer, tmp_path):
    path = make_docx(tmp_path / "plan.docx", paragraphs=["Roadmap"])
    [first] = list(indexer.process_files([path]))

    assert list(indexer.process_files([path], existing_ids={first["id"]})) == []

    bump_mtime(path)
    [again] = list(indexer.process_files([path], existing_ids={first["id"]}))
    assert again["id"] != first["id"]


def test_process_files_drops_files_without_text(indexer, tmp_path):
    empty = make_docx(tmp_path / "empty.docx")
    gone = str(tmp_path / "deleted.pdf")
    assert list(indexer.process_files([empty, gone])) == []
