from __future__ import annotations

import csv
from pathlib import Path

from .models import Document


SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv", ".pdf"}

#loaders.py is responsible for reading and cleaning documents — it does not create embeddings or answer questions.


# Finds supported files (.txt, .md, .csv, .pdf) inside a folder or accepts a single supported file.
def discover_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED_EXTENSIONS else []
    return sorted(
        file for file in path.rglob("*") if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS
    )


# Reads one file and extracts its text based on its format.
def load_document(path: Path) -> Document:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
    elif suffix == ".csv":
        text = _load_csv(path)
    elif suffix == ".pdf":
        text = _load_pdf(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    return Document(text=normalize_text(text), source=path, metadata={"file_type": suffix.lstrip(".")})


# Loads all supported documents found in a folder.
def load_documents(path: Path) -> list[Document]:
    return [load_document(file) for file in discover_files(path)]


# Cleans the text by removing extra spaces, blank lines, and unwanted characters.
def normalize_text(text: str) -> str:
    lines = [" ".join(line.strip().split()) for line in text.replace("\x00", " ").splitlines()]
    return "\n".join(line for line in lines if line)


# Reads a CSV file row by row and converts each row into readable text.
def _load_csv(path: Path) -> str:
    rows: list[str] = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=1):
            rendered = "; ".join(f"{key}: {value}" for key, value in row.items() if value)
            rows.append(f"Row {index}: {rendered}")
    return "\n".join(rows)


# Extracts text from PDF pages using the pypdf library.
def _load_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to ingest PDF files.") from exc

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)
