"""
Shared test fixtures.

Tests never download the real embedding model and never touch the real
data dir: `FakeEmbedder` replaces FastEmbed and `isolated_data_dir`
redirects odf.paths to a temp folder.
"""

import pytest

from tests.helpers import FakeEmbedder, make_docx
from odf import paths


@pytest.fixture
def isolated_data_dir(tmp_path, monkeypatch):
    """Point every ODF data path (index, models, log) at a temp dir."""
    data_root = tmp_path / "odf-data"
    monkeypatch.setattr(paths, "app_data_dir", lambda: str(data_root))
    return data_root


@pytest.fixture
def store(isolated_data_dir):
    """A real ChromaDB-backed VectorStore using the fake embedder."""
    from odf.index.store import VectorStore

    return VectorStore(FakeEmbedder())


@pytest.fixture
def searcher(store):
    from odf.search.service import SearchService

    return SearchService(store, store.embedder)


@pytest.fixture
def two_docs(tmp_path):
    finance = make_docx(tmp_path / "2023_Financial_Review.docx",
                        paragraphs=["Quarterly budget report: marketing spend rose 12 percent."])
    recipe = make_docx(tmp_path / "pasta.docx",
                       paragraphs=["Boil water, add salt, cook spaghetti for nine minutes."])
    return finance, recipe
