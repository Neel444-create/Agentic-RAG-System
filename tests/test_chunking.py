from rag_agent.chunking import split_text


def test_split_text_preserves_short_text():
    assert split_text("hello world", chunk_size=50, chunk_overlap=5) == ["hello world"]


def test_split_text_chunks_long_text():
    text = "alpha " * 80
    chunks = split_text(text, chunk_size=80, chunk_overlap=10)
    assert len(chunks) > 1
    assert all(len(chunk) <= 80 for chunk in chunks)

