"""
Shared test fixtures.

Tests never download the real embedding model and never touch the real
data dir: `FakeEmbedder` replaces FastEmbed and `isolated_data_dir`
redirects platform_paths to a temp folder.
"""

import pytest

from tests.helpers import FakeEmbedder
from utils import platform_paths


@pytest.fixture
def isolated_data_dir(tmp_path, monkeypatch):
    """Point every ODF data path (index, models, log) at a temp dir."""
    data_root = tmp_path / "odf-data"
    monkeypatch.setattr(platform_paths, "app_data_dir", lambda: str(data_root))
    return data_root


@pytest.fixture
def vector_search(isolated_data_dir, monkeypatch):
    """A real ChromaDB-backed VectorSearch using the fake embedder."""
    import search_engine.vector_search as vs_module

    monkeypatch.setattr(vs_module, "Embedder", FakeEmbedder)
    return vs_module.VectorSearch()
