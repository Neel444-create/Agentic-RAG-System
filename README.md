# Agentic RAG Assignment

A lightweight Retrieval-Augmented Generation (RAG) system for ingesting documents, chunking text, generating embeddings, storing vectors, retrieving relevant context, and answering questions grounded strictly in the indexed sources.

## Features

- Multi-format ingestion for TXT, Markdown, CSV, and PDF files
- Recursive document discovery across the knowledge base
- Overlapping chunking with source metadata preservation
- Chroma vector database persistence for local retrieval
- OpenAI embeddings and chat completions when `OPENAI_API_KEY` is set
- Offline deterministic embedding and extractive answer fallback for demos without API access
- CLI-based query interface and optional Streamlit web UI
- Conservative answer generation with similarity thresholding and grounded prompts

## Project Structure

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
├── WRITEUP.md              # Architecture, limitations, and improvements
└── .gitignore              # Git ignore rules
```

## Quick Start

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or
.venv\Scripts\activate      # Windows
```

### 2. Install dependencies

```bash
pip install -e ".[dev]"
```

If you are using the plain requirements file:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Or on Windows:

```bash
copy .env.example .env
```

### 4. Ingest example documents

```bash
rag-agent ingest --path data/sample_docs
```

### 5. Ask a question

```bash
rag-agent ask "What is the SLA for priority 1 incidents?"
```

### 6. Run the web UI

```bash
streamlit run streamlit_app.py
```

## Architecture

```text
Documents -> loaders -> chunker -> embedder -> Chroma vector DB
                                                  |
Question -> embedder -> retriever -> grounded answerer -> cited response
```

The system is intentionally conservative:
- It retrieves the top matching chunks.
- It filters out weak matches using `RAG_MIN_SIMILARITY`.
- It prompts the LLM to answer only from the retrieved context.
- If no relevant context is found, it returns:
  `I do not know based on the ingested documents.`

## Configuration

Environment variables can be placed in `.env`:

- `OPENAI_API_KEY`: Enables OpenAI embeddings and answer generation.
- `RAG_EMBEDDING_MODEL`: Defaults to `text-embedding-3-small`
- `RAG_CHAT_MODEL`: Defaults to `gpt-4o-mini`
- `RAG_TOP_K`: Number of retrieved chunks, default `5`
- `RAG_MIN_SIMILARITY`: Relevance cutoff, default `0.18`

## Evaluation Queries

These are example questions the system is designed to answer:

- `What is the SLA for priority 1 incidents?`
- `How should customer data be handled?`
- `Can employees approve their own expense reports?`
- `What documents are required before vendor onboarding?`
- `What is the company's policy on space travel reimbursement?`

The final question is intentionally out of scope and should return an unknown-answer response.

## Notes

This project includes a local fallback so it can be demonstrated without paid API access. For production-grade semantic retrieval, you can set `OPENAI_API_KEY` or replace the default embedder with a stronger sentence-transformer model.

## Author

Neel Prajapati  
B.Tech Undergrad, IIT Hyderabad
