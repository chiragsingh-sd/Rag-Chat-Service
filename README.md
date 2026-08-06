
# RAG Chat Service

RAG Chat Service is a FastAPI backend for authenticated, document-grounded chat. It
accepts plain-text documents, creates overlapping text chunks and embeddings, stores
them in PostgreSQL, and uses relevant chunks plus conversation history to answer
questions through Groq.

## Tech Stack

- Python, FastAPI, SQLAlchemy, Alembic, and PostgreSQL
- Sentence Transformers for document embeddings
- OpenAI-compatible Groq client for answer generation
- Docker and Docker Compose

## Project Structure

```text
app/                  Application code
alembic/              Database migrations
Dockerfile            Application image definition
docker-compose.yml    Application and PostgreSQL services
pyproject.toml        Project metadata and dependencies
```

## Quick Start

Run the commands below from the repository root. The local setup targets Python
3.12 or 3.13 and PostgreSQL 16. Docker users need Docker Desktop with Docker
Compose v2.

### Local Development

1. Clone the repository and enter the project directory:

   ```powershell
   git clone https://github.com/chiragsingh-sd/Rag-Chat-Service.git
   cd Rag-Chat-Service
   ```
2. Create and activate a virtual environment:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install the dependencies:

   ```powershell
   python -m pip install -e ".[dev]"
   ```
4. Create the environment file:

   ```powershell
   Copy-Item .env.example .env
   ```
5. Edit `.env` for local PostgreSQL. Change `DATABASE_URL` from the Docker
   hostname to `postgresql+psycopg://postgres:postgres@localhost:5432/rag_chat`.
   Also replace the `SECRET_KEY` placeholder and set a real Groq API key in
   `OPENAI_API_KEY`. This is the exact variable name used by the application;
   `GROQ_API_KEY` is not read by the current code. `LLM_MODEL` and `LLM_BASE_URL`
   already contain the example Groq configuration.
6. Start PostgreSQL 16, then create the application database if it does not
   already exist:

   ```powershell
   createdb -U postgres rag_chat
   ```
7. Apply the migrations:

   ```powershell
   alembic upgrade head
   ```
8. Start the FastAPI server:

   ```powershell
   python -m uvicorn app.main:app --reload
   ```

### Running with Docker

1. Install and start [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Clone the repository and enter the project directory:

   ```powershell
   git clone https://github.com/chiragsingh-sd/Rag-Chat-Service.git
   cd Rag-Chat-Service
   ```
3. Create `.env`:

   ```powershell
   Copy-Item .env.example .env
   ```

   The example is configured for Compose's `db` service. Set a real Groq key
   in `OPENAI_API_KEY`; keep `DATABASE_URL` pointed at `db:5432`.
4. Build the containers:

   ```powershell
   docker compose build
   ```
5. Start the application and PostgreSQL services:

   ```powershell
   docker compose up
   ```

   Alembic migrations run automatically when the application container starts.
6. Open Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).
7. Stop the services with:

   ```powershell
   docker compose down
   ```

### Test the API

After either setup is running, check the public health endpoint:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```text
status
------
healthy
```

Register and authenticate a test user:

```powershell
$body = @{ email = "recruiter@example.com"; password = "Password123!" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/register -ContentType "application/json" -Body $body
$login = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/login -ContentType "application/x-www-form-urlencoded" -Body @{ username = "recruiter@example.com"; password = "Password123!" }
$headers = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Uri http://localhost:8000/api/auth/me -Headers $headers
```

For the full RAG flow, use the token in Swagger's **Authorize** dialog, upload
a UTF-8 `.txt` file through `POST /documents/upload`, then submit a question to
`POST /chat`. Document uploads require the embedding model, and chat responses
require the configured Groq key.

## Environment Variables

The project includes a `.env.example` file with placeholders. Copy it to `.env`
and replace the placeholders locally. Do not commit `.env` or put secrets in source
control.

| Variable               | Purpose                                                    |
| ---------------------- | ---------------------------------------------------------- |
| `APP_NAME`           | FastAPI application name.                                  |
| `ENVIRONMENT`        | Runtime environment name.                                  |
| `LOG_LEVEL`          | Application logging level.                                 |
| `DATABASE_URL`       | PostgreSQL connection URL used by SQLAlchemy.              |
| `DATABASE_ECHO`      | Enables SQLAlchemy SQL logging when `true`.              |
| `POSTGRES_DB`        | Database name used by the Docker PostgreSQL service.      |
| `POSTGRES_USER`      | User used by the Docker PostgreSQL service.               |
| `POSTGRES_PASSWORD`  | Password used by the Docker PostgreSQL service.           |
| `SECRET_KEY`         | Secret used to sign JWT access tokens.                     |
| `JWT_ALGORITHM`      | JWT signing algorithm.                                     |
| `JWT_EXPIRE_MINUTES` | JWT access-token lifetime.                                 |
| `OPENAI_API_KEY`     | API key used by the OpenAI-compatible Groq client.         |
| `LLM_MODEL`          | LLM model name sent to Groq.                               |
| `LLM_BASE_URL`       | OpenAI-compatible provider URL.                            |
| `EMBEDDING_MODEL`    | Sentence-transformers model used for indexing and queries. |
| `CHUNK_SIZE`         | Maximum text chunk size in characters.                     |
| `CHUNK_OVERLAP`      | Overlap between adjacent chunks.                           |
| `RAG_TOP_K`          | Maximum number of chunks retrieved for a question.         |
| `CHAT_HISTORY_LIMIT` | Maximum previous messages included in a prompt.            |

## Project Timeline

The project was built incrementally through milestones: authentication, database setup,
document upload, chunking, embeddings, semantic retrieval, chat sessions, conversation
memory, validation and error handling, followed by final cleanup and documentation.

## Database Schema

- `users`
  Stores user accounts, email addresses, password hashes, and timestamps.
- `documents`
  Stores metadata for uploaded documents and their owning users.
- `document_chunks`
  Stores normalized text chunks, chunk indexes, and embeddings as PostgreSQL float arrays.
- `chat_sessions`
  Stores conversation sessions belonging to authenticated users.
- `chat_messages`
  Stores user and assistant messages belonging to chat sessions.

## Indexing Choices

- `users.email`
  A unique constraint prevents duplicate accounts. The email index speeds up
  authentication lookups.
- `documents.user_id`
  Speeds up filtering documents owned by the authenticated user.
- `document_chunks.document_id`
  Speeds up lookup of chunks belonging to a document.
- `document_chunks(document_id, chunk_index)`
  A unique constraint prevents duplicate chunk positions within one document.
- `chat_sessions.user_id`
  Supports efficient listing and ownership filtering for a user's sessions.
- `chat_messages.session_id`
  Supports efficient loading of conversation history for one session.

The project does not use `pgvector` or a database vector index. Embeddings are stored
as PostgreSQL float arrays, and the current retriever calculates cosine similarity in
Python before returning the configured top-k chunks.

## API Documentation

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

Every endpoint can be tested directly through Swagger. Protected endpoints require a
JWT obtained from `POST /api/auth/login`, entered in Swagger's **Authorize** dialog.

## Troubleshooting

- **Missing Groq API key:** Set `OPENAI_API_KEY` to a valid Groq key in `.env`,
  then restart the application. The current code does not read `GROQ_API_KEY`.
- **Docker is not running:** Start Docker Desktop and retry `docker compose up`.
- **PostgreSQL connection failure:** Local development must use a reachable
  `localhost` PostgreSQL URL and an existing `rag_chat` database. Docker must
  use `postgresql+psycopg://postgres:postgres@db:5432/rag_chat` so the app reaches
  the Compose `db` service.
- **Port 8000 or 5432 is already in use:** Check the ports with
  `Get-NetTCPConnection -LocalPort 8000,5432 -ErrorAction SilentlyContinue`.
  Stop the conflicting process, or change the host-side port mapping in
  `docker-compose.yml` before starting Docker.
- **First document upload is slow:** Sentence Transformers may download the
  configured embedding model the first time it is used; the container needs
  network access for that download.

## Notes

This project was developed as part of a backend engineering assignment and demonstrates a production-style RAG backend built with FastAPI.
