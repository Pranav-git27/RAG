import os
import uuid
from dotenv import load_dotenv
import chromadb
from google import genai

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMBEDDING_MODEL = "gemini-embedding-2"

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

class GeminiEmbeddingWrapper:
    """
    Custom embedding wrapper so Chroma can call Gemini automatically.
    Implements the __call__ interface expected by Chroma's embedding function.
    """

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            response = gemini_client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
            )
            # Safely grab the vector list values from the plural response container
            embeddings.append(response.embeddings[0].values)
        return embeddings

    def name(self) -> str:
        return "gemini_embedding_2"


embedding_function = GeminiEmbeddingWrapper()

chroma_client = chromadb.PersistentClient(path="./chroma_data")

collection = chroma_client.get_or_create_collection(
    name="owasp_vulnerabilities",
    embedding_function=embedding_function,
)

def seed_owasp_data():
    """
    Inject sample OWASP records into the 'owasp_vulnerabilities' collection.
    Each record is tagged with structured metadata:
      - owasp_category : OWASP Top 10 category identifier
      - chunk_type     : Type of security document chunk (description, remediation, code_example)
      - target_language: Programming language the guidance applies to
    """
    records = [
        {
            "id": str(uuid.uuid4()),
            "document": (
                "## A01:2025 – Broken Access Control\n\n"
                "Access control enforces policy such that users cannot act outside of their intended permissions. "
                "Failures typically lead to unauthorized information disclosure, modification, or destruction of data. "
                "Common vectors include insecure direct object references (IDOR), missing function-level access control, "
                "and CORS misconfigurations."
            ),
            "metadata": {
                "owasp_category": "A01:2025-Broken Access Control",
                "chunk_type": "description",
                "target_language": "markdown",
            },
        },
        {
            "id": str(uuid.uuid4()),
            "document": (
                "## Remediation: Enforce Server-Side Access Checks\n\n"
                "Never rely solely on client-side controls. Every API endpoint and server-side route must "
                "verify the authenticated user's identity and role before performing any action. "
                "Use deny-by-default policies and log all access control failures."
            ),
            "metadata": {
                "owasp_category": "A01:2025-Broken Access Control",
                "chunk_type": "remediation",
                "target_language": "markdown",
            },
        },
        {
            "id": str(uuid.uuid4()),
            "document": (
                "from functools import wraps\n"
                "from fastapi import Depends, HTTPException\n\n"
                "def require_role(required_role: str):\n"
                "    \"\"\"Secure Python decorator to enforce role-based access control.\"\"\"\n"
                "    def decorator(func):\n"
                "        @wraps(func)\n"
                "        def wrapper(*args, current_user=Depends(get_current_user), **kwargs):\n"
                "            if current_user.role != required_role:\n"
                "                raise HTTPException(status_code=403, detail=\"Insufficient permissions\")\n"
                "            return func(*args, current_user=current_user, **kwargs)\n"
                "        return wrapper\n"
                "    return decorator"
            ),
            "metadata": {
                "owasp_category": "A01:2025-Broken Access Control",
                "chunk_type": "code_example",
                "target_language": "python",
            },
        },
    ]

    collection.add(
        ids=[r["id"] for r in records],
        documents=[r["document"] for r in records],
        metadatas=[r["metadata"] for r in records],
    )

    print(f"Seeded {len(records)} records into collection '{collection.name}'.")

if __name__ == "__main__":
    seed_owasp_data()