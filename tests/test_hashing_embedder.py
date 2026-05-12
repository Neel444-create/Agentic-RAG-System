from rag_agent.embeddings import HashingEmbedder


def test_hashing_embedder_is_deterministic():
    embedder = HashingEmbedder(dimensions=32)
    first = embedder.embed(["refund policy"])[0]
    second = embedder.embed(["refund policy"])[0]
    assert first == second
    assert len(first) == 32

