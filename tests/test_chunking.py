from odf.index.vector_search import VectorSearch

# The splitter doesn't use instance state, so call it without building a VectorSearch
split = VectorSearch._recursive_text_split


def test_empty_text_gives_no_chunks():
    assert split(None, "") == []


def test_short_text_is_one_chunk():
    assert split(None, "short document") == ["short document"]


def test_long_text_chunks_are_bounded_and_cover_everything():
    text = " ".join(f"word{i}" for i in range(2000))  # ~13k chars, spaces only
    chunks = split(None, text, chunk_size=1000, chunk_overlap=100)

    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)
    assert chunks[0] == text[: len(chunks[0])]
    assert text.endswith(chunks[-1])
    # Every word survives chunking
    joined = " ".join(chunks)
    assert all(f"word{i}" in joined for i in range(0, 2000, 97))


def test_consecutive_chunks_overlap():
    text = ". ".join(f"Sentence number {i} is here" for i in range(300))
    chunks = split(None, text, chunk_size=500, chunk_overlap=50)
    for prev, nxt in zip(chunks, chunks[1:]):
        assert prev[-50:] == nxt[:50]


def test_text_without_separators_is_force_split():
    text = "x" * 2500
    chunks = split(None, text, chunk_size=1000, chunk_overlap=100)
    assert [len(c) for c in chunks] == [1000, 1000, 700]
