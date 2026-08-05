# RAG Chat Service

## Project Overview

RAG Chat Service is a FastAPI backend for authenticated document-grounded chat. It
accepts plain-text documents, splits them into overlapping chunks, stores normalized
embeddings in PostgreSQL, retrieves relevant chunks for questions, and sends a
context-aware prompt to the configured Groq-compatible LLM.

## Features

- JWT authentication and protected API routes
- Plain-text document upload and normalization
- Configurable text chunking with overlap
- Sentence-transformers embeddings
- PostgreSQL vector storage and similarity retrieval
- Retrieval-augmented generation (RAG)
- User-owned chat sessions
- Database-backed conversation memory for follow-up questions
- OpenAPI/Swagger documentation

## Tech Stack

- Python 3.12 or 3.13
- FastAPI and Uvicorn
- PostgreSQL and SQLAlchemy
- Alembic database migrations
- `sentence-transformers/all-MiniLM-L6-v2` by default for embeddings
- OpenAI-compatible client configured for Groq by default
- Pydantic settings and JWT authentication

## Project Structure

```text
app/
├── core/       # Settings, security, and exception handling
├── database/   # SQLAlchemy engine, session, and base metadata
├── models/     # ORM models
├── rag/        # Chunking, embeddings, retrieval, and prompt generation
├── routers/    # Thin HTTP endpoint handlers
├── schemas/    # Request and response validation models
└── services/   # Authentication, ingestion, chat, and session business logic
alembic/
├── versions/   # Database migrations
└── env.py      # Alembic metadata/configuration
README.md
pyproject.toml
```

## Installation

1. Create and activate a virtual environment:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the project and development tools:

   ```powershell
   python -m pip install -e ".[dev]"
   ```

3. Copy `.env.example` to `.env` and set a strong `SECRET_KEY`, a reachable
   `DATABASE_URL`, and your Groq API key in `OPENAI_API_KEY`.

   ```powershell
   Copy-Item .env.example .env
   ```

4. Ensure PostgreSQL is running and the configured database exists.

## Environment Variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_NAME` | FastAPI application name | `rag-chat-service` |
| `ENVIRONMENT` | Runtime environment label | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL | local PostgreSQL URL |
| `DATABASE_ECHO` | Enable SQLAlchemy SQL logging | `false` |
| `SECRET_KEY` | JWT signing secret; use a strong production value | development-only fallback |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | JWT lifetime | `30` |
| `OPENAI_API_KEY` | Groq API key used by the OpenAI-compatible client | unset |
| `LLM_MODEL` | Groq model name | `gpt-4o-mini` |
| `LLM_BASE_URL` | OpenAI-compatible LLM base URL | unset |
| `EMBEDDING_MODEL` | Sentence-transformers model | `sentence-transformers/all-MiniLM-L6-v2` |
| `CHUNK_SIZE` | Chunk size in characters | `1000` |
| `CHUNK_OVERLAP` | Chunk overlap in characters | `200` |
| `RAG_TOP_K` | Maximum retrieved chunks | `5` |
| `CHAT_HISTORY_LIMIT` | Maximum prior messages included in prompts | `10` |

Never commit `.env` or place passwords, JWT secrets, or API keys in source code.
The development secret fallback is intended only for local development and must be
overridden outside development.

## Running Locally

Apply migrations and start the API:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload
```

The API is then available at `http://127.0.0.1:8000`.

## Database Migration

```powershell
# Apply all migrations
alembic upgrade head

# Show the current revision
alembic current

# Show migration history
alembic history

# Roll back one revision when needed
alembic downgrade -1
```

Do not run a downgrade in production without a tested backup and rollback plan.

## API Documentation

With the server running, open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

Use `POST /api/auth/login` to obtain a JWT, then use Swagger's **Authorize** button
with the token value as `Bearer <token>` for protected routes.

## Example Workflow

The same flow can be executed from Swagger or with an HTTP client:

1. Register with `POST /api/auth/register`.
2. Login with `POST /api/auth/login` and save the returned access token.
3. Authorize Swagger with `Bearer <token>`.
4. Upload a `.txt` file with `POST /documents/upload`.
5. Create a session with `POST /chat/sessions`.
6. Ask a document-grounded question with `POST /chat` using the session ID.
7. Ask a follow-up question with the same session ID.
8. Read the session and stored messages with `GET /chat/sessions/{id}`.

Example chat request body:

```json
{
  "question": "What does the document say about onboarding?",
  "session_id": 1
}
```

The response includes the answer, source documents, chunk indexes, and `session_id`.

## Future Improvements

Possible future work includes pgvector-backed indexing, explicit upload-size limits,
rate limiting, automated tests in CI, richer observability, and background ingestion.
These are intentionally outside the current milestone.
