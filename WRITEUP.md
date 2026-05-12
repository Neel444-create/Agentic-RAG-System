# Write-up

## Architecture Decisions

The system is split into small modules so each RAG stage can be evaluated independently:
loading, preprocessing, chunking, embedding, vector storage, retrieval, and response generation.
Chroma is used as the primary vector database because it is lightweight, persistent, and easy to
run locally for an internship assignment. A JSON vector-store fallback exists for restricted
environments and tests.

The response layer is deliberately grounded. Retrieved chunks are filtered by similarity before
being passed to the answerer. The OpenAI prompt requires answers to use only the retrieved
context and to admit when the answer is missing. Without an API key, the system uses an
extractive answerer that quotes matching sentences from retrieved chunks.

## Hallucination Controls

- Similarity threshold rejects weak retrieval matches.
- Prompt instructs the model to answer only from context.
- Temperature is set to `0.0`.
- Source metadata is returned with every answer.
- Unknown questions return a fixed "I do not know" response.

## Limitations

- The local hashing embedder is useful for demos but is less semantic than model embeddings.
- CSV ingestion renders rows as text, which is simple but not optimized for analytical queries.
- The current UI supports manual re-indexing, not scheduled sync from external sources.
- Conversation memory is limited to the Streamlit session display; retrieval is still per-query.

## Scaling Suggestions

- Add background ingestion jobs with document checksums and incremental updates.
- Move Chroma to a managed vector database or deploy Weaviate/Qdrant for team-scale usage.
- Add hybrid retrieval with BM25 plus vector search.
- Store page numbers and exact spans for stronger citations.
- Add an evaluation set measuring answer faithfulness, retrieval recall, and unknown-query refusal.
- Add Google Drive or S3 connectors for multi-source ingestion.

