from __future__ import annotations

import re

from .config import Settings
from .models import SearchResult


class GroundedAnswerer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        if settings.openai_api_key:
            from openai import OpenAI

            self.client = OpenAI(api_key=settings.openai_api_key)

    @property
    def uses_llm(self) -> bool:
        return self.client is not None

    def answer(self, question: str, contexts: list[SearchResult]) -> str:
        if not contexts:
            return "I do not know based on the ingested documents."
        if self.client:
            return self._openai_answer(question, contexts)
        return self._extractive_answer(question, contexts)

    def _openai_answer(self, question: str, contexts: list[SearchResult]) -> str:
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
        response = self.client.chat.completions.create(
            model=self.settings.chat_model,
            messages=[
                {"role": "system", "content": "You are a grounded RAG assistant. Do not hallucinate."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content or "I do not know based on the ingested documents."

    def _extractive_answer(self, question: str, contexts: list[SearchResult]) -> str:
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
        lines = [f"- {sentence} ({source})" for _, sentence, source in best if sentence]
        return "Based on the retrieved documents:\n" + "\n".join(lines)

