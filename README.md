# RAG Chat Service

RAG Chat Service is a FastAPI backend for authenticated, document-grounded chat. It
accepts plain-text documents, creates overlapping text chunks and embeddings, stores
them in PostgreSQL, and uses relevant chunks plus conversation history to answer
questions through Groq.

## Setup Instructions

1. Clone the repository:

   ```powershell
   git clone <repository-url>
   cd rag-chat-service
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
4. Copy the environment template:

   ```powershell
   Copy-Item .env.example .env
   ```
5. Configure the required values in `.env`. Set a reachable PostgreSQL
   `DATABASE_URL`, a strong `SECRET_KEY`, and the Groq API key in
   `OPENAI_API_KEY`. The example file contains the Groq base URL and model
   configuration.
6. Make sure PostgreSQL is running, then apply the migrations:

   ```powershell
   alembic upgrade head
   ```
7. Start the FastAPI server:

   ```powershell
   python -m uvicorn app.main:app --reload
   ```
8. Open Swagger at:

   ```text
   http://localhost:8000/docs
   ```

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
| `DATABASE_ECHO`      | Enables SQLAlchemy SQL logging when`true`.               |
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



## Notes

This project was developed as part of a backend engineering assignment and demonstrates a production-style RAG backend built with FastAPI.
