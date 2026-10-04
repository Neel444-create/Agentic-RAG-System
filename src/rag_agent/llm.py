from __future__ import annotations

import re

from .config import Settings
from .models import SearchResult


class GroundedAnswerer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.gemini_api_key:
            from google import genai

            self.client = genai.Client(api_key=settings.gemini_api_key)

    @property
    def uses_llm(self) -> bool:
        return self.client is not None

    def answer(self, question: str, contexts: list[SearchResult]) -> str:
        if not contexts:
            return "I do not know based on the ingested documents."
        if self.client:
            return self._gemini_answer(question, contexts)
        return self._extractive_answer(question, contexts)

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
    def _summarize_excerpt(text: str, limit: int = 360) -> str:
        """Keep a fallback response readable when PDF extraction yields a single long line."""
        compact = " ".join(text.split())
        return compact if len(compact) <= limit else compact[:limit].rsplit(" ", 1)[0] + "…"

