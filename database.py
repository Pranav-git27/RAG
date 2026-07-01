import os
from dotenv import load_dotenv
import chromadb

load_dotenv()


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Initialize and return a local persistent Chroma DB client.
    """
    client = chromadb.PersistentClient(path="./chroma_data")
    return client


def get_or_create_collection(name: str = "owasp_vulnerabilities"):
    """
    Retrieve or create a Chroma DB collection for storing OWASP vulnerability data.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)


def get_metadata_example() -> dict:
    """
    Return a reference metadata structure for document blocks in the
    'owasp_vulnerabilities' collection.

    Metadata fields explained:
      - owasp_category: The OWASP Top 10 category identifier (e.g., "A01:2021-Broken Access Control").
      - chunk_type: The type of security document chunk (e.g., "description", "remediation", "code_example").
      - target_language: The programming language or technology stack the guidance applies to (e.g., "python", "javascript").
      - cwe_id: Optional CWE identifier linked to the vulnerability.
      - severity: Optional severity rating (e.g., "high", "medium", "low").
      - source: URL or document reference where the content was extracted from.
    """
    return {
        "owasp_category": "A01:2021-Broken Access Control",
        "chunk_type": "remediation",
        "target_language": "python",
        "cwe_id": "CWE-284",
        "severity": "high",
        "source": "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
    }
