from __future__ import annotations

import argparse
from pathlib import Path

from .agent import RagAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agentic RAG assignment CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Index documents into the vector database")
    ingest.add_argument("--path", type=Path, default=None, help="Document file or folder to ingest")
    ingest.add_argument("--append", action="store_true", help="Append instead of rebuilding the index")
    ingest.add_argument("--json-store", action="store_true", help="Use local JSON vector store fallback")

    query = subparsers.add_parser("ask", help="Ask a grounded question")
    query.add_argument("question", help="Question to answer from indexed documents")
    query.add_argument("--json-store", action="store_true", help="Use local JSON vector store fallback")

    chat = subparsers.add_parser("chat", help="Interactive grounded chat")
    chat.add_argument("--json-store", action="store_true", help="Use local JSON vector store fallback")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    agent = RagAgent(use_json_store=getattr(args, "json_store", False))

    if args.command == "ingest":
        chunks = agent.ingest(args.path, reset=not args.append)
        print(f"Indexed {len(chunks)} chunks.")
        return

    if args.command == "ask":
        _print_answer(agent.ask(args.question))
        return

    if args.command == "chat":
        print("Grounded RAG chat. Type 'exit' to quit.")
        while True:
            question = input("\nQuestion: ").strip()
            if question.lower() in {"exit", "quit"}:
                break
            _print_answer(agent.ask(question))


def _print_answer(answer) -> None:
    print("\nAnswer:")
    print(answer.answer)
    print("\nSources:")
    if not answer.sources:
        print("- No sufficiently relevant source found.")
    for result in answer.sources:
        name = result.chunk.metadata.get("source_name", result.chunk.source)
        print(f"- {name} | chunk {result.chunk.chunk_index} | similarity {result.similarity:.3f}")
    print(f"\nMode: {'LLM' if answer.used_llm else 'local extractive fallback'}")


if __name__ == "__main__":
    main()

