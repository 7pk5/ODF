import logging
import os

import pytest

from tests.helpers import bump_mtime, index, make_docx


def chunk_ids_for(store, path):
    return store.collection.get(where={"source": path}, include=[])["ids"]


def test_get_all_ids_returns_file_ids_not_chunk_ids(store, two_docs):
    index(store, list(two_docs))
    ids = store.get_all_ids()
    assert len(ids) == 2
    assert not any("_chunk_" in i for i in ids)


def test_reindexing_unchanged_files_adds_nothing(store, two_docs):
    index(store, list(two_docs))
    before = store.get_stats()["count"]
    index(store, list(two_docs))
    assert store.get_stats()["count"] == before


def test_cleanup_removes_deleted_files(store, two_docs):
    finance, recipe = two_docs
    index(store, list(two_docs))
    os.remove(recipe)

    assert store.cleanup_deleted_files() == 1
    assert store.get_all_source_paths() == {finance}


def test_delete_by_source_removes_all_chunks_of_a_file(store, tmp_path):
    long_doc = make_docx(tmp_path / "long.docx", paragraphs=["lorem ipsum dolor " * 300])
    index(store, [long_doc])
    n = len(chunk_ids_for(store, long_doc))
    assert n > 1
    assert store.delete_by_source(long_doc) == n
    assert chunk_ids_for(store, long_doc) == []


def test_modified_file_replaces_old_chunks(store, tmp_path):
    path = tmp_path / "notes.docx"
    make_docx(path, paragraphs=["Old content about zebras."])
    index(store, [str(path)])

    make_docx(path, paragraphs=["New content about giraffes."])
    bump_mtime(path)
    index(store, [str(path)])

    stored = store.collection.get(where={"source": str(path)}, include=["documents"])
    assert not any("zebras" in d for d in stored["documents"])


def test_remove_stale_versions_repairs_indexes_built_before_the_fix(store, tmp_path):
    # Simulate a v1.2 index: two versions of notes.docx stored side by side
    path = str(tmp_path / "notes.docx")

    def chunk(version_id, mtime, text):
        meta = {
            "source": path,
            "filename": "notes.docx",
            "modified": mtime,
            "size": 1,
            "type": ".docx",
            "chunk_index": 0,
        }
        store._process_batch([f"{version_id}_chunk_0"], [text], [meta])

    chunk("old", 100.0, "Old content about zebras.")
    chunk("new", 200.0, "New content about giraffes.")
    other = make_docx(tmp_path / "other.docx", paragraphs=["Unrelated file"])
    index(store, [other])

    assert store.remove_stale_versions() == 1
    stored = store.collection.get(where={"source": path}, include=["documents"])
    assert stored["ids"] == ["new_chunk_0"]
    assert store.get_all_source_paths() == {path, other}
    assert store.remove_stale_versions() == 0


def test_remove_stale_versions_deletes_in_batches(store, tmp_path, monkeypatch):
    path = str(tmp_path / "big.docx")

    def meta(mtime, i):
        return {
            "source": path,
            "filename": "big.docx",
            "modified": mtime,
            "size": 1,
            "type": ".docx",
            "chunk_index": i,
        }

    store._process_batch(
        [f"old_chunk_{i}" for i in range(7)], [f"old text {i}" for i in range(7)], [meta(1.0, i) for i in range(7)]
    )
    store._process_batch(["new_chunk_0"], ["new text"], [meta(2.0, 0)])
    monkeypatch.setattr(store.client, "get_max_batch_size", lambda: 3)

    assert store.remove_stale_versions() == 1
    assert store.collection.get(include=[])["ids"] == ["new_chunk_0"]


def test_failed_batch_is_logged_with_traceback(store, monkeypatch, caplog):
    def upsert(**kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(store.collection, "upsert", upsert)

    with caplog.at_level(logging.ERROR, logger="odf"):
        store._process_batch(["a_chunk_0"], ["text"], [{"source": "a.pdf"}])

    [record] = [r for r in caplog.records if r.levelname == "ERROR"]
    assert record.exc_info and "disk full" in str(record.exc_info[1])


def test_chroma_telemetry_is_disabled(store):
    # chromadb 1.5.9 sends nothing, but keep it explicitly off so an
    # upgrade can't silently break ODF's "no telemetry" promise
    assert store.client.get_settings().anonymized_telemetry is False


@pytest.mark.xfail(strict=True, reason="B4: clear() recreates the collection without cosine distance")
def test_clear_keeps_cosine_distance(store):
    store.clear()
    assert (store.collection.metadata or {}).get("hnsw:space") == "cosine"
