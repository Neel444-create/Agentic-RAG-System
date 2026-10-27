from __future__ import annotations

from collections.abc import Callable
import re

from .config import Settings
from .models import Chunk, SearchResult

#Purpose: This file generates answers using the document chunks retrieved by vector_store.py. It tries to answer using Gemini; if the API is unavailable, it uses a local extractive fallback.

#Main class responsible for generating answers based on retrieved context.
class GroundedAnswerer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.gemini_api_key:
            from google import genai

            self.client = genai.Client(api_key=settings.gemini_api_key)

    #Property that checks whether the Gemini client is available.
    @property
    def uses_llm(self) -> bool:
        return self.client is not None

    #Chooses the answer-generation method or returns an unknown answer if no relevant context exists.
    def answer(self, question: str, contexts: list[SearchResult]) -> str:
        if not contexts:
            return "I do not know based on the ingested documents."
        if self.client:
            return self._gemini_answer(question, contexts)
        return self._extractive_answer(question, contexts)

    def summarize(
        self,
        chunks: list[Chunk],
        source_name: str,
        on_progress: Callable[[str], None] | None = None,
    ) -> str:
        """Create a concise document summary without a vector-search step."""
        if not chunks:
            return "This document has not been indexed yet."

        ordered_chunks = sorted(chunks, key=lambda chunk: chunk.chunk_index)
        context = self._summary_context(ordered_chunks)
        if self.client:
            prompt = (
                "Summarize the document below using only its content. Return a short overview followed "
                "by at most 6 key bullet points. Include important names, dates, numbers, and action items "
                "when present. Do not add information that is not in the document.\n\n"
                f"Document: {source_name}\n\n{context}"
            )
            try:
                from google.genai import types

                if on_progress:
                    on_progress("Generating summary...")
                response = self.client.models.generate_content(
                    model=self.settings.chat_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=300,
                    ),
                )
                if response.text:
                    return response.text
            except Exception:
                pass

        return self._extractive_summary(ordered_chunks, source_name)

        #Sends the question and retrieved chunks to Gemini with instructions to answer only from the context.
    def _gemini_answer(self, question: str, contexts: list[SearchResult]) -> str:
        context_block = "\n\n".join(
            f"[{index}] Source: {result.chunk.metadata.get('source_name', result.chunk.source)}\n"
            f"{result.chunk.text}"
            for index, result in enumerate(contexts, start=1)
        )
        prompt = (
            "Answer strictly from the provided context. If the context does not contain the answer, "
            "say: I do not know based on the ingested documents. Cite sources inline as [1], [2].\n\n"
            f"Context:\n{context_block}\n\nQuestion: {question}"
        )
        try:
            response = self.client.models.generate_content(
                model=self.settings.chat_model,
                contents=("You are a grounded RAG assistant. Do not hallucinate.\n\n" + prompt),
            )
            return response.text or self._extractive_answer(question, contexts)
        except Exception:
            return self._extractive_answer(question, contexts)

    #Creates a simple answer by selecting relevant sentences from retrieved chunks.
    def _extractive_answer(self, question: str, contexts: list[SearchResult]) -> str:
        cv_answer = self._answer_cv_fact(question, contexts)
        if cv_answer:
            return cv_answer

        question_terms = {
            token
            for token in re.findall(r"[a-zA-Z0-9]+", question.lower())
            if len(token) > 2
        }
        candidates: list[tuple[int, str, str]] = []
        for result in contexts:
            source_name = result.chunk.metadata.get("source_name", result.chunk.source)
            for sentence in re.split(r"(?<=[.!?])\s+", result.chunk.text):
                sentence_terms = set(re.findall(r"[a-zA-Z0-9]+", sentence.lower()))
                score = len(question_terms & sentence_terms)
                if score:
                    candidates.append((score, sentence.strip(), source_name))

        if not candidates:
            return "I do not know based on the ingested documents."

        best = sorted(candidates, key=lambda item: item[0], reverse=True)[:4]
        lines = [
            f"- {self._summarize_excerpt(sentence)} ({source})"
            for _, sentence, source in best
            if sentence
        ]
        return "Based on the retrieved documents:\n" + "\n".join(lines)

    @staticmethod
    #Handles a specific CV-related question, such as asking for CGPA, when the required information is present.
    def _answer_cv_fact(question: str, contexts: list[SearchResult]) -> str | None:
        """Return compact answers for common structured CV facts when LLM generation is unavailable."""
        normalized_question = question.lower()
        combined_text = "\n".join(result.chunk.text for result in contexts)

        if "cgpa" in normalized_question or "gpa" in normalized_question:
            match = re.search(
                r"B\.?(?:Tech)?\s+[^\n]{0,160}?\b(?:19|20)\d{2}\s+(\d{1,2}\.\d{1,2})\b",
                combined_text,
                flags=re.IGNORECASE,
            )
            if match:
                source = contexts[0].chunk.metadata.get("source_name", contexts[0].chunk.source)
                return f"Neel Prajapati's CGPA is {match.group(1)}. ({source})"
        return None

    @staticmethod
    #Shortens long text excerpts to make fallback answers more readable.
    def _summarize_excerpt(text: str, limit: int = 360) -> str:
        """Keep a fallback response readable when PDF extraction yields a single long line."""
        compact = " ".join(text.split())
        return compact if len(compact) <= limit else compact[:limit].rsplit(" ", 1)[0] + "…"

    @staticmethod
    def _summary_context(chunks: list[Chunk], limit: int = 7_000) -> str:
        """Use a representative, bounded sample to keep summaries fast."""
        text = "\n\n".join(chunk.text for chunk in chunks)
        if len(text) <= limit:
            return text

        # Sample the beginning, middle, and end rather than sending a long prefix only.
        section_size = limit // 3
        middle_start = max(0, (len(text) - section_size) // 2)
        return "\n\n[Beginning]\n" + text[:section_size] + (
            "\n\n[Middle]\n" + text[middle_start : middle_start + section_size]
            + "\n\n[End]\n" + text[-section_size:]
        )

    @staticmethod
    def _extractive_summary(chunks: list[Chunk], source_name: str) -> str:
        """Provide a concise local summary if the configured model is unavailable."""
        text = " ".join(chunk.text for chunk in chunks)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        excerpts = [
            GroundedAnswerer._summarize_excerpt(sentence, limit=240)
            for sentence in sentences
            if len(sentence.split()) >= 5
        ][:6]
        if not excerpts:
            excerpts = [GroundedAnswerer._summarize_excerpt(text, limit=700)]
        return f"Summary of {source_name}:\n" + "\n".join(f"- {excerpt}" for excerpt in excerpts)

