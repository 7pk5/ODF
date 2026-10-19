import os

import pytest

from odf.index.service import IndexResult, IndexService
from tests.helpers import make_docx


@pytest.fixture
def indexer(store):
    return IndexService(store)


@pytest.fixture
def folder(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    make_docx(docs / "a.docx", paragraphs=["Quarterly budget report"])
    make_docx(docs / "b.docx", paragraphs=["Travel policy for employees"])
    return docs


def test_index_folder_stores_every_supported_file(indexer, store, folder):
    result = indexer.index_folder(str(folder))

    assert result == IndexResult(files_found=2, removed_deleted=0, repaired_stale=0)
    assert {os.path.basename(p) for p in store.get_all_source_paths()} == {"a.docx", "b.docx"}
    assert indexer.chunk_count() == store.count() > 0


def test_progress_reports_each_stored_file_against_files_found(indexer, folder):
    calls = []
    indexer.index_folder(str(folder), on_progress=lambda done, total, name: calls.append((done, total)))
    assert calls == [(1, 2), (2, 2)]


def test_unchanged_files_are_skipped_on_reindex(indexer, folder):
    indexer.index_folder(str(folder))
    calls = []
    result = indexer.index_folder(str(folder), on_progress=lambda *a: calls.append(a))

    # Current behaviour (B6): files_found still counts the skipped files
    assert result.files_found == 2
    assert calls == []


def test_deleted_files_are_dropped_and_reported_before_scanning(indexer, store, folder):
    indexer.index_folder(str(folder))
    os.remove(folder / "b.docx")

    reported = []
    result = indexer.index_folder(str(folder), on_cleanup=reported.append)

    assert reported == [1]
    assert result.removed_deleted == 1
    assert {os.path.basename(p) for p in store.get_all_source_paths()} == {"a.docx"}


def test_folder_without_documents_finds_nothing(indexer, tmp_path):
    assert indexer.index_folder(str(tmp_path)).files_found == 0
    assert indexer.chunk_count() == 0


def test_missing_folder_raises(indexer, tmp_path):
    with pytest.raises(ValueError):
        indexer.index_folder(str(tmp_path / "nope"))
