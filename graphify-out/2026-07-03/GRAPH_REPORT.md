# Graph Report - D:\RAG Test  (2026-07-03)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 198 nodes · 325 edges · 17 communities (11 shown, 6 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5bafea10`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_deps.py|deps.py]]
- [[_COMMUNITY_search.py|search.py]]
- [[_COMMUNITY_ConversationRepository|ConversationRepository]]
- [[_COMMUNITY_DocumentRepository|DocumentRepository]]
- [[_COMMUNITY_BackendClient|BackendClient]]
- [[_COMMUNITY_app.py|app.py]]
- [[_COMMUNITY_get_conversation_repo|get_conversation_repo]]
- [[_COMMUNITY_EmbeddingService|EmbeddingService]]
- [[_COMMUNITY_GenerationService|GenerationService]]
- [[_COMMUNITY_get_session|get_session]]
- [[_COMMUNITY_health_check|health_check]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]

## God Nodes (most connected - your core abstractions)
1. `DocumentRepository` - 15 edges
2. `EmbeddingService` - 13 edges
3. `ConversationRepository` - 12 edges
4. `get_settings()` - 11 edges
5. `BackendClient` - 10 edges
6. `get_conversation_repo()` - 9 edges
7. `Conversation` - 9 edges
8. `Base` - 8 edges
9. `Document` - 8 edges
10. `RetrievalService` - 8 edges

## Surprising Connections (you probably didn't know these)
- `seed()` --calls--> `get_settings()`  [EXTRACTED]
  scripts/ingest.py → backend/config.py
- `seed()` --calls--> `DocumentRepository`  [EXTRACTED]
  scripts/ingest.py → backend/repositories/document_repo.py
- `AuditLog` --uses--> `Base`  [INFERRED]
  backend/models/db.py → backend/db/session.py
- `Document` --uses--> `Base`  [INFERRED]
  backend/models/db.py → backend/db/session.py
- `RetrievalService` --uses--> `EmbeddingService`  [INFERRED]
  backend/services/retrieval.py → backend/services/embeddings.py

## Import Cycles
- None detected.

## Communities (17 total, 6 thin omitted)

### Community 0 - "deps.py"
Cohesion: 0.13
Nodes (19): get_settings(), Centralised application configuration.  Single source of truth for all environme, Strongly-typed settings read from environment variables / .env file., Return a cached Settings instance.      Cached so the env file is parsed only on, Settings, SQLAlchemy 2.0 engine, session factory and declarative base.  Engine settings ar, get_db(), FastAPI dependency providers.  Thin wiring layer that gives route handlers acces (+11 more)

### Community 1 - "search.py"
Cohesion: 0.11
Nodes (26): AuditLog, Timestamped record of a search / ingest event for observability., ConversationCreate, ConversationDetail, ConversationResponse, HealthResponse, MessageCreate, QueryRequest (+18 more)

### Community 2 - "ConversationRepository"
Cohesion: 0.12
Nodes (19): Base, Declarative base shared by all ORM models in ``backend.models.db``., Conversation, Message, SQLAlchemy ORM models.  Each class maps 1:1 to a table defined in ``scripts/init, A chat session between the user and the RAG assistant., A single message within a conversation (user query or assistant answer)., ConversationRepository (+11 more)

### Community 3 - "DocumentRepository"
Cohesion: 0.10
Nodes (17): Document, A single text chunk stored with its embedding in pgvector., DocumentRepository, Any, Session, Document repository — pgvector similarity search and bulk insertion.  All vector, Read / write operations on the ``documents`` table., Insert a single document row and return the ORM instance. (+9 more)

### Community 4 - "BackendClient"
Cohesion: 0.14
Nodes (10): BackendClient, Any, Typed HTTP client for the secOwasp FastAPI backend.  Centralises all backend com, Typed wrapper around the secOwasp API., Ping /health.  Returns the JSON body or raises on failure., Return True if the backend is reachable and healthy., POST /api/v1/search — the RAG endpoint.          Returns { answer, sources[], qu, GET /api/v1/conversations (+2 more)

### Community 5 - "app.py"
Cohesion: 0.17
Nodes (13): secOwasp — Streamlit frontend for OWASP semantic RAG search.  Thin entry point:, Any, Reusable Streamlit UI components.  Each function renders one self-contained piec, Show the welcome / empty-state prompt., Render the synthesised RAG answer followed by expandable source cards.      The, Render a coloured status dot + label in the sidebar., render_answer(), render_empty_state() (+5 more)

### Community 6 - "get_conversation_repo"
Cohesion: 0.16
Nodes (14): get_conversation_repo(), get_document_repo(), get_retrieval_service(), Session, Return a DocumentRepository bound to the current request's DB session., Return a ConversationRepository bound to the current request's DB session., Return a RetrievalService bound to the current request's DB session., create_conversation() (+6 more)

### Community 7 - "EmbeddingService"
Cohesion: 0.18
Nodes (9): get_embedding_service(), Return the shared EmbeddingService., EmbeddingService, Client, Wrapper around the Google GenAI SDK for embedding generation., Embed a single query string and return the vector., Embed multiple documents and return a list of vectors., Embed and insert the seed records into Supabase. (+1 more)

### Community 8 - "GenerationService"
Cohesion: 0.20
Nodes (9): get_generation_service(), Return the shared GenerationService., _build_context_block(), GenerationService, Any, Client, Format retrieved documents into a numbered context block., Generate a RAG answer using Gemini. (+1 more)

### Community 9 - "get_session"
Cohesion: 0.67
Nodes (3): get_session(), Session, FastAPI dependency: yield a DB session and ensure it is closed.

### Community 10 - "health_check"
Cohesion: 0.67
Nodes (3): health_check(), Session, Readiness probe — verifies Supabase Postgres is reachable.

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DocumentRepository` connect `DocumentRepository` to `deps.py`, `get_conversation_repo`, `EmbeddingService`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `ConversationRepository` connect `ConversationRepository` to `deps.py`, `get_conversation_repo`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `EmbeddingService` connect `EmbeddingService` to `deps.py`, `DocumentRepository`, `get_conversation_repo`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `DocumentRepository` (e.g. with `Document` and `RetrievalService`) actually correct?**
  _`DocumentRepository` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ConversationRepository` (e.g. with `Conversation` and `Message`) actually correct?**
  _`ConversationRepository` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `secOwasp backend package — FastAPI + Supabase (Postgres + pgvector) RAG service.`, `Centralised application configuration.  Single source of truth for all environme`, `Strongly-typed settings read from environment variables / .env file.` to the rest of the system?**
  _86 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `deps.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12698412698412698 - nodes in this community are weakly interconnected._