import pytest

from tests.helpers import index, make_docx


def test_empty_index_returns_no_results(searcher):
    assert searcher.search("anything") == []


def test_index_then_search_ranks_relevant_file_first(store, searcher, two_docs):
    finance, _ = two_docs
    index(store, list(two_docs))

    hits = searcher.search("budget report", top_k=2)
    assert hits[0]["file_path"] == finance
    assert hits[0]["filename"] == "2023_Financial_Review.docx"
    assert 0.0 <= hits[-1]["similarity"] <= hits[0]["similarity"] <= 1.0


def test_filename_match_is_boosted(store, searcher, two_docs):
    index(store, list(two_docs))
    [hit] = [h for h in searcher.search("pasta", top_k=2) if h["filename"] == "pasta.docx"]
    assert hit["boosted"] is True
    assert hit["similarity"] >= hit["base_score"] + 0.25 or hit["similarity"] == 1.0


@pytest.mark.xfail(strict=True, reason="B3: results are per chunk, so one long file can fill every slot")
def test_results_are_one_per_file(store, searcher, tmp_path):
    long_doc = make_docx(tmp_path / "handbook.docx", paragraphs=["employee leave policy details " * 400])
    short_doc = make_docx(tmp_path / "memo.docx", paragraphs=["Updated leave policy for employees."])
    index(store, [long_doc, short_doc])

    hits = searcher.search("leave policy", top_k=5)
    filenames = [h["filename"] for h in hits]
    assert len(filenames) == len(set(filenames))
