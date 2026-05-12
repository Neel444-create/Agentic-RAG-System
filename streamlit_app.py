from __future__ import annotations

from pathlib import Path

import streamlit as st

from rag_agent.agent import RagAgent


st.set_page_config(page_title="Agentic RAG Assignment", layout="wide")
st.title("Agentic RAG System")

agent = RagAgent()

with st.sidebar:
    st.header("Index")
    docs_path = st.text_input("Document folder", "data/sample_docs")
    if st.button("Rebuild index", type="primary"):
        with st.spinner("Ingesting and embedding documents..."):
            chunks = agent.ingest(Path(docs_path), reset=True)
        st.success(f"Indexed {len(chunks)} chunks.")

question = st.chat_input("Ask a question grounded in the indexed documents")
if "messages" not in st.session_state:
    st.session_state.messages = []

for role, content in st.session_state.messages:
    with st.chat_message(role):
        st.markdown(content)

if question:
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
