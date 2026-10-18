import hashlib
import os

from odf.index import file_indexer
from tests.helpers import bump_mtime, make_docx


def test_process_files_returns_documents_with_metadata(tmp_path):
    path = make_docx(tmp_path / "plan.docx", paragraphs=["Roadmap for next year"])
    [doc] = list(file_indexer.process_files([path]))

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


def test_process_files_skips_already_indexed_and_reprocesses_modified(tmp_path):
    path = make_docx(tmp_path / "plan.docx", paragraphs=["Roadmap"])
    [first] = list(file_indexer.process_files([path]))

    assert list(file_indexer.process_files([path], existing_ids={first["id"]})) == []

    bump_mtime(path)
    [again] = list(file_indexer.process_files([path], existing_ids={first["id"]}))
    assert again["id"] != first["id"]


def test_process_files_drops_files_without_text(tmp_path):
    empty = make_docx(tmp_path / "empty.docx")
    gone = str(tmp_path / "deleted.pdf")
    assert list(file_indexer.process_files([empty, gone])) == []


def test_document_id_is_md5_of_path_and_mtime():
    assert file_indexer.document_id("/docs/a.pdf", 12.5) == hashlib.md5(b"/docs/a.pdf_12.5").hexdigest()
