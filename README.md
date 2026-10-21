# Agentic RAG Assignment

Lightweight Retrieval-Augmented Generation system for ingesting documents, chunking text,
creating embeddings, storing vectors in Chroma, retrieving relevant context, and answering
questions strictly from indexed sources.

## Features

- Multi-format ingestion for TXT, Markdown, CSV, and PDF.
- Recursive document discovery.
- Overlapping text chunking with source metadata.
- Chroma vector database persistence.
- OpenAI embeddings and chat completion when `OPENAI_API_KEY` is set.
- Offline deterministic embedding and extractive answer fallback for demos without credentials.
- CLI query interface and optional Streamlit web UI.
- Unknown-query handling through similarity thresholding and grounded answer prompts.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

Index the included sample documents:

```bash
rag-agent ingest --path data/sample_docs
```

Ask a question:

```bash
rag-agent ask "What is the SLA for priority 1 incidents?"
```

Run the web UI:

```bash
streamlit run streamlit_app.py
```

## Architecture

```text
Documents -> loaders -> chunker -> embedder -> Chroma vector DB
                                                  |
Question -> embedder -> retriever -> grounded answerer -> cited response
```

The agent is intentionally conservative. It retrieves the top matching chunks, filters out weak
matches using `RAG_MIN_SIMILARITY`, and instructs the LLM to answer only from supplied context.
When no sufficiently relevant context is found, it returns: `I do not know based on the ingested documents.`

## Repository Structure

```text
Agentic-RAG-System/
│
├── src/rag_agent/          # Core RAG implementation
│   ├── agent.py            # Main workflow coordinator
│   ├── loaders.py          # Loads PDF, TXT, MD, CSV
│   ├── chunking.py         # Splits documents into chunks
│   ├── embeddings.py       # Creates vector embeddings
│   ├── vector_store.py     # Chroma and JSON storage
│   ├── llm.py              # Generates grounded answers
│   ├── config.py           # Configuration and settings
│   ├── models.py           # Data structures
│   └── cli.py              # Terminal commands
│
├── data/sample_docs/       # Example knowledge base
├── tests/                  # Unit tests
├── scripts/                # Demo query examples
├── streamlit_app.py        # Web chat interface
├── pyproject.toml          # Dependencies and package setup
├── requirements.txt        # Dependency list
├── .env.example            # Environment configuration example
├── README.md               # Overview and setup guide
└── WRITEUP.md              # Architecture, limitations, improvements
```

## Configuration

Environment variables can be placed in `.env`:

- `OPENAI_API_KEY`: enables OpenAI embeddings and answer generation.
- `RAG_EMBEDDING_MODEL`: defaults to `text-embedding-3-small`.
- `RAG_CHAT_MODEL`: defaults to `gpt-4o-mini`.
- `RAG_TOP_K`: number of retrieved chunks, default `5`.
- `RAG_MIN_SIMILARITY`: relevance cutoff, default `0.18`.

## Evaluation Queries

- `What is the SLA for priority 1 incidents?`
- `How should customer data be handled?`
- `Can employees approve their own expense reports?`
- `What documents are required before vendor onboarding?`
- `What is the company's policy on space travel reimbursement?`

The last query is intentionally out of scope and should produce an unknown answer.

## Notes

The local fallback is provided so the assignment can be demonstrated without paid API access.
For production-quality semantic retrieval, set `OPENAI_API_KEY` or replace the embedder with a
local sentence-transformer model.

Neel Prajapati 
Btech Undergrad IIT Hyderabad

