"""
Engine
Builds the backend — embedding model, index and services — in one place.
"""

from dataclasses import dataclass

from odf.embedder import Embedder
from odf.index.service import IndexService
from odf.index.store import VectorStore
from odf.search.service import SearchService


@dataclass
class Engine:
    indexer: IndexService
    searcher: SearchService


def create_engine(embedder=None):
    """Load the embedding model (downloaded on first run) and open the index."""
    embedder = embedder or Embedder()
    store = VectorStore(embedder)
    return Engine(indexer=IndexService(store), searcher=SearchService(store, embedder))
