# 🛡️ secOwasp — Secure Semantic Intelligence for OWASP Top 10

Production-grade, context-aware **Retrieval-Augmented Generation (RAG)** application. Uses Google Gemini embeddings for semantic search and LLM-powered answer synthesis over OWASP vulnerability documentation, backed by Supabase (Postgres + pgvector).

---

## Architecture

```mermaid
graph TD
    classDef client fill:#1E293B,stroke:#00E676,stroke-width:2px,color:#F8FAFC;
    classDef backend fill:#1E293B,stroke:#3B82F6,stroke-width:2px,color:#F8FAFC;
    classDef database fill:#1E293B,stroke:#EC4899,stroke-width:2px,color:#F8FAFC;

    Streamlit[Streamlit Frontend<br>frontend/]:::client
    FastAPI[FastAPI Backend<br>backend/]:::backend
    GeminiAPI[Google Gemini<br>embeddings + LLM]:::backend
    Supabase[(Supabase<br>Postgres + pgvector)]:::database

    Streamlit -->|HTTP| FastAPI
    FastAPI -->|Embed query| GeminiAPI
    GeminiAPI -->|768-dim vector| FastAPI
    FastAPI -->|Cosine search <=> | Supabase
    FastAPI -->|Generate answer| GeminiAPI
    GeminiAPI -->|Synthesised answer| FastAPI
    FastAPI -->|Persist conversation| Supabase
```

### RAG Flow
```
User query
  → Gemini embeds query (768-dim vector)
  → pgvector cosine similarity search (top-K docs)
  → Gemini synthesises answer from retrieved context + cites sources
  → Answer + sources returned to frontend
  → Conversation persisted to Supabase
```

---

## Features

- **True RAG Pipeline** — Not just vector search; actually synthesises natural-language answers from retrieved context, with citation numbers.
- **Supabase + pgvector** — Production database with HNSW-indexed vector similarity, relational data (conversations, audit logs), all in one hosted Postgres instance.
- **Gemini Embeddings (768-dim MRL)** — Uses `gemini-embedding-2` with Matryoshka Representation Learning truncation — 1/4 the storage with negligible quality loss.
- **Gemini Flash Generation** — `gemini-2.0-flash` for fast, low-cost answer synthesis.
- **No LangChain** — Direct `google-genai` SDK calls. Transparent, lightweight, no abstraction overhead.
- **Clean Architecture** — Separated layers: config → db → models → repositories → services → routes → frontend.
- **Persistent Conversations** — Chat history stored in Supabase with source references.
- **Audit Logging** — Every search query logged with latency and status.

---

## Project Structure

```
.
├── backend/                     # FastAPI application
│   ├── __init__.py
│   ├── main.py                  # App factory + lifespan
│   ├── config.py                # Centralised settings (pydantic-settings)
│   ├── deps.py                  # FastAPI dependency injection
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py           # SQLAlchemy engine + session factory
│   ├── models/
│   │   ├── __init__.py
│   │   ├── db.py                # ORM models (Document, Conversation, Message, AuditLog)
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── document_repo.py     # pgvector similarity search
│   │   └── conversation_repo.py # Conversation + message CRUD
│   ├── services/
│   │   ├── __init__.py
│   │   ├── embeddings.py        # Gemini embedding wrapper (768-dim)
│   │   ├── retrieval.py         # Embed → search orchestrator
│   │   └── generation.py        # RAG answer synthesis
│   └── routes/
│       ├── __init__.py
│       ├── health.py            # GET /health
│       ├── search.py            # POST /api/v1/search (RAG endpoint)
│       └── conversations.py    # GET/POST /api/v1/conversations
├── frontend/                    # Streamlit UI
│   ├── app.py                   # Thin entry point (~90 lines)
│   ├── api_client.py            # Typed backend HTTP client
│   ├── components.py            # Reusable UI components
│   └── styles.py                # Theme constants + CSS
├── scripts/
│   ├── ingest.py                # Seed OWASP sample data into Supabase
│   └── init_db.sql              # One-time schema (run in Supabase SQL Editor)
├── .env                         # Your secrets (not committed)
├── .env.example                 # Template for .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Prerequisites
- Python 3.10 – 3.12
- A [Supabase](https://supabase.com) account (free tier works)
- A Google Gemini API key from [AI Studio](https://aistudio.google.com/)

### 2. Create Supabase Project
1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Note your **Project Reference** and **Region**
3. Go to **Database → Extensions** → ensure **`vector`** is enabled
4. Go to **Settings → Database** → copy the **Session pooler** connection string

### 3. Initialise Database Schema
1. Open your Supabase project → **SQL Editor** → New query
2. Paste the contents of `scripts/init_db.sql`
3. Click **Run**

### 4. Configure Environment
Create a `.env` file in the project root (see `.env.example`):

```ini
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql+psycopg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIM=768
LLM_MODEL=gemini-2.0-flash
BACKEND_URL=http://127.0.0.1:8000
```

### 5. Install Dependencies
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# or: source .venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

### 6. Seed Sample Data
```bash
python scripts/ingest.py
```

---

## Running

### Backend (FastAPI)
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### Frontend (Streamlit)
In a separate terminal:
```bash
streamlit run frontend/app.py
```
Opens at http://localhost:8501

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Readiness probe (checks DB connection) |
| POST | `/api/v1/search` | RAG search — embeds query, retrieves docs, synthesises answer |
| GET | `/api/v1/conversations` | List recent conversations |
| POST | `/api/v1/conversations` | Create a new conversation |
| GET | `/api/v1/conversations/{id}` | Get conversation with full message history |
| DELETE | `/api/v1/conversations/{id}` | Delete a conversation and its messages |