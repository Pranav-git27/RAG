"""
Production-grade FastAPI application integrating Chroma DB & Google Gemini Embeddings
for semantic search over OWASP vulnerability documentation.

Architecture:
  - Lifespan-based startup/shutdown lifecycle (no deprecated on_event decorators).
  - Custom GeminiEmbeddingWrapper adhering to Chroma's embedding function protocol.
  - Pydantic-v2 input validation with strict length/bounds guards.
  - Dependency injection for the Chroma collection with a 503 guard.
  - Catch-all exception handling in the search endpoint to prevent internal detail leakage.
"""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import chromadb
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from google import genai
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Logging (JSON-friendly, production-safe)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("owasp-api")

# ---------------------------------------------------------------------------
# Environment / secrets
# ---------------------------------------------------------------------------
load_dotenv()

GEMINI_API_KEY: str | None = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set. "
        "The application cannot start without a valid API key."
    )

# ---------------------------------------------------------------------------
# Global mutable state container (owned by the lifespan)
# ---------------------------------------------------------------------------
# Using a typed dict-like container so we don't pollute the module namespace
# with mutable globals that could be accidentally reassigned.
app_state: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Custom Chroma embedding wrapper (Gemini)
# ---------------------------------------------------------------------------
class GeminiEmbeddingWrapper:
    """Implements Chroma's embedding function interface using the modern Google GenAI SDK."""
    def __init__(self, client: genai.Client):
        self.client = client

    def __call__(self, input: list[str]) -> list[list[float]]:
        try:
            embeddings = []
            for text in input:
                response = self.client.models.embed_content(
                    model="gemini-embedding-2",  # Hardcoded locally to prevent NameErrors
                    contents=text,
                )
                
                # Dynamic property safe extraction
                if hasattr(response, 'embeddings') and response.embeddings:
                    embeddings.append(response.embeddings[0].values)
                elif hasattr(response, 'embedding') and response.embedding:
                    embeddings.append(response.embedding.values)
                else:
                    embeddings.append(response[0].values if isinstance(response, list) else response.values)
                    
            return embeddings
        except Exception as e:
            print(f"[SECURITY LOG ERROR]: {str(e)}")
            raise RuntimeError(f"Embedding generation failed securely: {str(e)}")

    def embed_query(self, input: list[str]) -> list[list[float]]:
        """Explicit query entry point required by Chroma during collection lookups."""
        return self.__call__(input)

    def name(self) -> str:
        return "gemini_embedding_2"


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, Any]:
    """
    FastAPI lifespan context manager.

    Startup:
        - Creates the genai.Client.
        - Builds the GeminiEmbeddingWrapper.
        - Opens a persistent Chroma client and retrieves the target collection.

    Shutdown:
        - Clears the global state container so the GC can collect resources.
    """
    logger.info("Starting up – initialising Gemini client & Chroma DB …")

    # ---- startup -----------------------------------------------------------
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    embedding_fn = GeminiEmbeddingWrapper(client=gemini_client)

    chroma_client = chromadb.PersistentClient(path="./chroma_data")
    collection = chroma_client.get_collection(
        name="owasp_vulnerabilities",
        embedding_function=embedding_fn,
    )

    # Persist references in the global state container.
    app_state["gemini_client"] = gemini_client
    app_state["embedding_fn"] = embedding_fn
    app_state["chroma_client"] = chroma_client
    app_state["collection"] = collection

    logger.info("Startup complete – collection '%s' ready.", collection.name)

    yield  # <-- application runs here

    # ---- shutdown ----------------------------------------------------------
    logger.info("Shutting down – cleaning up global state …")
    app_state.clear()


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OWASP Semantic Search API",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Pydantic request schema (hardened input validation)
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    """
    Strictly-validated search request body.

    Defences:
        - ``text``: 3 – 500 characters to limit payload size (DoS mitigation).
        - ``n_results``: 1 – 10 to prevent resource-exhaustion queries.
    """

    text: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural-language search query (3–500 characters).",
    )
    n_results: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Number of top-K results to return (1–10).",
    )


# ---------------------------------------------------------------------------
# Dependency injection – safe collection accessor
# ---------------------------------------------------------------------------
def get_vector_db() -> chromadb.Collection:
    """
    FastAPI dependency that injects the active Chroma ``Collection`` instance.

    Returns:
        The Chroma collection stored in ``app_state``.

    Raises:
        HTTPException (503): if the database has not been initialised yet
                             (e.g. during startup race or after a shutdown).
    """
    collection: chromadb.Collection | None = app_state.get("collection")
    if collection is None:
        raise HTTPException(
            status_code=503,
            detail="Vector database service is not available. Please try again shortly.",
        )
    return collection


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check(
    collection: chromadb.Collection = Depends(get_vector_db),
) -> dict[str, str]:
    """
    Readiness probe.  Returns a 200 only when the Chroma collection is
    fully initialised and reachable.
    """
    # A lightweight count() call verifies the collection is truly responsive.
    _ = collection.count()
    return {"status": "healthy"}


@app.post("/api/v1/search")
async def search(
    request: QueryRequest,
    collection: chromadb.Collection = Depends(get_vector_db),
) -> list[dict[str, Any]]:
    """
    Execute a semantic similarity search against the OWASP knowledge base.

    Request body:
        ``text``       – The natural-language search query.
        ``n_results``  – Number of top-K matches to return.

    Returns:
        A list of result dictionaries, each containing the keys ``id``,
        ``document``, ``metadata``, and ``distance``.

    Security:
        - All internal exceptions are caught and replaced with a generic
          message so that stack traces / DB internals are never leaked.
    """
    try:
        raw = collection.query(
            query_texts=[request.text],
            n_results=request.n_results,
        )
    except Exception:
        logger.exception("Chroma query execution failed.")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while evaluating your database request profile.",
        )

    # Explicitly extract and sanitise the raw output into clean dictionaries.
    results: list[dict[str, Any]] = []
    ids: list[str] = raw.get("ids", [[]])[0] if raw.get("ids") else []
    documents: list[str] = (
        raw.get("documents", [[]])[0] if raw.get("documents") else []
    )
    metadatas: list[dict[str, Any]] = (
        raw.get("metadatas", [[]])[0] if raw.get("metadatas") else []
    )
    distances: list[float] = (
        raw.get("distances", [[]])[0] if raw.get("distances") else []
    )

    for i in range(len(ids)):
        results.append(
            {
                "id": ids[i] if i < len(ids) else "",
                "document": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else 0.0,
            }
        )

    return results
