# Demo Script

1. Install dependencies and index sample documents:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
rag-agent ingest --path data/sample_docs
```

2. Ask grounded questions:

```bash
rag-agent ask "What is the SLA for priority 1 incidents?"
rag-agent ask "How should customer data be handled?"
rag-agent ask "Can employees approve their own expense reports?"
rag-agent ask "What is the company's policy on space travel reimbursement?"
```

3. Launch the optional UI:

```bash
streamlit run streamlit_app.py
```

