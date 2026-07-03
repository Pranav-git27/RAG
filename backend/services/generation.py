"""
Generation service — synthesises a natural-language answer from retrieved context.

This is the "G" in RAG.  It takes the user query and the top-K retrieved
documents, builds a prompt that forces citation-by-number, and calls
``gemini-2.0-flash`` to produce the final answer.

No LangChain — direct ``google-genai`` SDK call.
"""

from __future__ import annotations

import logging
from typing import Any

from google import genai

from backend.config import get_settings

logger = logging.getLogger("owasp-api")

_settings = get_settings()

# -- System prompt (constant, doesn't change per request) -----------------------
SYSTEM_PROMPT = """\
You are secOwasp, an expert cybersecurity assistant specialising in the \
OWASP Top 10 vulnerability categories. Your role is to answer user questions \
about application security based ONLY on the retrieved context provided below.

Rules:
1. Answer using ONLY the information in the provided context. Do not invent \
or hallucinate details.
2. Cite your sources by placing a reference number in square brackets — e.g. \
"CORS misconfiguration [1]" — where the number corresponds to the document \
index in the context list.
3. If the context does not contain enough information to answer the question, \
say so clearly: "The available context does not contain sufficient information \
to fully answer this question."
4. Structure your answer with clear headings or bullet points where appropriate.
5. Keep the answer concise but thorough. Aim for a helpful, expert tone.
"""


def _build_context_block(documents: list[dict[str, Any]]) -> str:
    """Format retrieved documents into a numbered context block."""
    parts: list[str] = []
    for idx, doc in enumerate(documents, start=1):
        meta = []
        if doc.get("owasp_category"):
            meta.append(doc["owasp_category"])
        if doc.get("chunk_type"):
            meta.append(doc["chunk_type"])
        if doc.get("target_language"):
            meta.append(doc["target_language"])

        header = f"Document {idx}"
        if meta:
            header += f" ({', '.join(meta)})"
        header += f"  [Relevance: {doc.get('score', 0):.2%}]"

        parts.append(f"---\n{header}\n{doc.get('content', '')}")
    return "\n\n".join(parts)


class GenerationService:
    """Generate a RAG answer using Gemini."""

    def __init__(self, client: genai.Client | None = None) -> None:
        self.client = client or genai.Client(api_key=_settings.gemini_api_key)
        self.model = _settings.llm_model

    def synthesize(
        self,
        query: str,
        documents: list[dict[str, Any]],
    ) -> str:
        """
        Build a context-augmented prompt and call the LLM.

        Returns the generated answer as a plain-text string.
        """
        context_block = _build_context_block(documents)

        user_prompt = (
            f"## User Question\n{query}\n\n"
            f"## Retrieved Context\n{context_block}\n\n"
            f"## Instructions\nAnswer the question above using ONLY the "
            f"retrieved context. Cite sources by [document number]."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "temperature": 0.2,   # factual, low hallucination
                    "max_output_tokens": 2048,
                },
            )
            answer = response.text
            logger.info(
                "GenerationService: synthesized %d chars for query: %s",
                len(answer), query[:60],
            )
            return answer

        except Exception:
            logger.exception("LLM generation failed.")
            raise
