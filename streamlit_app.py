from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from rag_agent.agent import RagAgent


st.set_page_config(page_title="Agentic RAG Assignment", layout="wide")
st.title("Agentic RAG System")

agent = RagAgent()
summary_source: str | None = None


def save_uploaded_pdf(uploaded_file) -> Path:
    """Persist an uploaded PDF locally so the standard loader can parse and index it."""
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", uploaded_file.name)
    upload_dir = agent.settings.resolve("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / safe_name
    destination.write_bytes(uploaded_file.getvalue())
    return destination

with st.sidebar:
    st.header("Index")
    docs_path = st.text_input("Document folder", "data/sample_docs")
    if st.button("Rebuild index", type="primary"):
        with st.spinner("Ingesting and embedding documents..."):
            chunks = agent.ingest(Path(docs_path), reset=True)
        st.success(f"Indexed {len(chunks)} chunks.")

    st.divider()
    st.subheader("Upload a PDF")
    uploaded_pdf = st.file_uploader(
        "Add a document for this session",
        type=["pdf"],
        help="The PDF is parsed and added to the current index. It is not committed to GitHub.",
    )
    if uploaded_pdf and st.button("Index uploaded PDF", use_container_width=True):
        with st.spinner(f"Parsing and indexing {uploaded_pdf.name}..."):
            uploaded_path = save_uploaded_pdf(uploaded_pdf)
            chunks = agent.ingest(uploaded_path, reset=False)
        if chunks:
            st.success(f"Added {uploaded_pdf.name} ({len(chunks)} chunks).")
        else:
            st.warning("No readable text was found. This may be a scanned PDF that needs OCR.")

    st.divider()
    st.subheader("Document summary")
    indexed_sources = agent.indexed_sources()
    if indexed_sources:
        selected_summary_source = st.selectbox("Indexed document", indexed_sources)
        if st.button("Summarize selected document", use_container_width=True):
            summary_source = selected_summary_source
    else:
        selected_summary_source = None
        st.caption("Index or upload a document before summarizing it. If you just upgraded, rebuild the index.")

    st.divider()
    st.subheader("Quick questions")
    st.caption("Ask questions like:")
    if st.button("What is Neel's CGPA?", use_container_width=True):
        st.session_state["suggested_question"] = "What is Neel Prajapati's CGPA?"
    if st.button("Which projects has Neel worked on?", use_container_width=True):
        st.session_state["suggested_question"] = "Which projects has Neel Prajapati worked on?"

question = st.chat_input("Ask a question grounded in the indexed documents")
question = question or st.session_state.pop("suggested_question", None)
if "messages" not in st.session_state:
    st.session_state.messages = []

if (
    question
    and re.match(r"^\s*(summarize|summary|summarise|summarisation|summarization)\b", question, re.I)
    and selected_summary_source
):
    summary_source = selected_summary_source
    question = None

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

if summary_source:
    summary_request = f"Summarize {summary_source}"
    st.session_state.messages.append(("user", summary_request))
    with st.chat_message("user"):
        st.markdown(summary_request)

    summary_cache = st.session_state.setdefault("document_summaries", {})
    with st.chat_message("assistant"):
        if summary_source in summary_cache:
            summary = summary_cache[summary_source]
        else:
            with st.spinner("Summarizing the indexed document..."):
                summary = agent.summarize_document(summary_source)
            summary_cache[summary_source] = summary
        st.markdown(summary)
    st.session_state.messages.append(("assistant", summary))

elif question:
    st.session_state.messages.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving context..."):
            answer = agent.ask(question)
        st.markdown(answer.answer)
        if answer.sources:
            with st.expander("Retrieved sources"):
                for result in answer.sources:
                    st.write(
                        f"{result.chunk.metadata.get('source_name', result.chunk.source)} "
                        f"(chunk {result.chunk.chunk_index}, similarity {result.similarity:.3f})"
                    )
                    st.caption(result.chunk.text[:700])
    st.session_state.messages.append(("assistant", answer.answer))
