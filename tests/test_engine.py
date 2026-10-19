from odf.engine import create_engine
from tests.helpers import FakeEmbedder, index, make_docx


def test_engine_wires_indexer_and_searcher_to_one_index(isolated_data_dir, tmp_path):
    engine = create_engine(embedder=FakeEmbedder())
    path = make_docx(tmp_path / "budget.docx", paragraphs=["Quarterly budget report"])

    index(engine.indexer.store, [path])

    assert engine.indexer.chunk_count() > 0
    assert engine.searcher.search("budget report")[0]["file_path"] == path


def test_model_is_cached_reflects_model_dir(isolated_data_dir):
    from odf import paths
    from odf.embedder import model_is_cached

    assert model_is_cached() is False
    open(f"{paths.model_cache_dir()}/model.onnx", "w").close()
    assert model_is_cached() is True
