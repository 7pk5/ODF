import os

import pytest

from search_engine.file_indexer import FileIndexer
from tests.helpers import bump_mtime, make_docx


def index(vs, paths):
    """Run the same index pipeline the UI uses (_index_thread)."""
    docs = FileIndexer().process_files(paths, existing_ids=vs.get_all_ids())
    vs.add_documents(docs)


def chunk_ids_for(vs, path):
    return vs.collection.get(where={"source": path}, include=[])["ids"]


@pytest.fixture
def two_docs(tmp_path):
    finance = make_docx(tmp_path / "2023_Financial_Review.docx",
                        paragraphs=["Quarterly budget report: marketing spend rose 12 percent."])
    recipe = make_docx(tmp_path / "pasta.docx",
                       paragraphs=["Boil water, add salt, cook spaghetti for nine minutes."])
    return finance, recipe


def test_empty_index_returns_no_results(vector_search):
    assert vector_search.search("anything") == []


def test_index_then_search_ranks_relevant_file_first(vector_search, two_docs):
    finance, _ = two_docs
    index(vector_search, list(two_docs))

    hits = vector_search.search("budget report", top_k=2)
    assert hits[0]["file_path"] == finance
    assert hits[0]["filename"] == "2023_Financial_Review.docx"
    assert 0.0 <= hits[-1]["similarity"] <= hits[0]["similarity"] <= 1.0


def test_filename_match_is_boosted(vector_search, two_docs):
    index(vector_search, list(two_docs))
    [hit] = [h for h in vector_search.search("pasta", top_k=2) if h["filename"] == "pasta.docx"]
    assert hit["boosted"] is True
    assert hit["similarity"] >= hit["base_score"] + 0.25 or hit["similarity"] == 1.0


def test_get_all_ids_returns_file_ids_not_chunk_ids(vector_search, two_docs):
    index(vector_search, list(two_docs))
    ids = vector_search.get_all_ids()
    assert len(ids) == 2
    assert not any("_chunk_" in i for i in ids)


def test_reindexing_unchanged_files_adds_nothing(vector_search, two_docs):
    index(vector_search, list(two_docs))
    before = vector_search.get_stats()["count"]
    index(vector_search, list(two_docs))
    assert vector_search.get_stats()["count"] == before


def test_cleanup_removes_deleted_files(vector_search, two_docs):
    finance, recipe = two_docs
    index(vector_search, list(two_docs))
    os.remove(recipe)

    assert vector_search.cleanup_deleted_files() == 1
    assert vector_search.get_all_source_paths() == {finance}


def test_delete_by_source_removes_all_chunks_of_a_file(vector_search, tmp_path):
    long_doc = make_docx(tmp_path / "long.docx", paragraphs=["lorem ipsum dolor " * 300])
    index(vector_search, [long_doc])
    n = len(chunk_ids_for(vector_search, long_doc))
    assert n > 1
    assert vector_search.delete_by_source(long_doc) == n
    assert chunk_ids_for(vector_search, long_doc) == []


# ── Known bugs (Phase 0). Remove the xfail marker when fixed. ──────

@pytest.mark.xfail(strict=True, reason="B1: re-indexing a modified file leaves its old chunks in the index")
def test_modified_file_replaces_old_chunks(vector_search, tmp_path):
    path = tmp_path / "notes.docx"
    make_docx(path, paragraphs=["Old content about zebras."])
    index(vector_search, [str(path)])

    make_docx(path, paragraphs=["New content about giraffes."])
    bump_mtime(path)
    index(vector_search, [str(path)])

    stored = vector_search.collection.get(where={"source": str(path)}, include=["documents"])
    assert not any("zebras" in d for d in stored["documents"])


@pytest.mark.xfail(strict=True, reason="B3: results are per chunk, so one long file can fill every slot")
def test_results_are_one_per_file(vector_search, tmp_path):
    long_doc = make_docx(tmp_path / "handbook.docx", paragraphs=["employee leave policy details " * 400])
    short_doc = make_docx(tmp_path / "memo.docx", paragraphs=["Updated leave policy for employees."])
    index(vector_search, [long_doc, short_doc])

    hits = vector_search.search("leave policy", top_k=5)
    filenames = [h["filename"] for h in hits]
    assert len(filenames) == len(set(filenames))


@pytest.mark.xfail(strict=True, reason="B4: clear() recreates the collection without cosine distance")
def test_clear_keeps_cosine_distance(vector_search):
    vector_search.clear()
    assert (vector_search.collection.metadata or {}).get("hnsw:space") == "cosine"
