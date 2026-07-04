"""
Generation service — synthesises a natural-language answer from retrieved context.

This is the "G" in RAG.  It takes the user query and the top-K retrieved
documents, builds a prompt that forces citation-by-number, and calls
the configured Gemini model to produce the final answer.

No LangChain — direct ``google-genai`` SDK call.

Retries: a single 429 (RESOURCE_EXHAUSTED) shouldn't fail the whole
request — the free tier's RPM ceiling is easy to hit while testing. We
retry a couple of times with backoff before giving up. ``tenacity`` is
already a transitive dependency of ``google-genai``, so no new package
is required.
"""

from __future__ import annotations

import logging
from typing import Any

from google import genai
from google.genai.errors import ClientError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from backend.config import get_settings

logger = logging.getLogger("owasp-api")

_settings = get_settings()


def _is_rate_limit_error(exc: BaseException) -> bool:
    """True only for 429s — don't retry on 4xx auth/validation errors."""
    return isinstance(exc, ClientError) and getattr(exc, "code", None) == 429

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
            response = self._call_gemini(user_prompt)
            answer = response.text
            logger.info(
                "GenerationService: synthesized %d chars for query: %s",
                len(answer), query[:60],
            )
            return answer

        except Exception:
            logger.exception("LLM generation failed.")
            raise

    @retry(
        retry=retry_if_exception(_is_rate_limit_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True,
    )
    def _call_gemini(self, user_prompt: str):
        """
        The actual API call, isolated so it can be retried on 429s only.

        Up to 3 attempts total, exponential backoff (2s, 4s, ... capped at
        20s). Any non-429 error (auth, invalid request, etc.) is raised
        immediately with no retry — retrying those just wastes time and
        hides real bugs.
        """
        return self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.2,   # factual, low hallucination
                "max_output_tokens": 2048,
            },
        )