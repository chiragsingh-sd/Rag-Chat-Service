# RAG Chat Service — Frozen Architecture

## 1. Architecture status

This is the final architecture for a 24-hour internship assignment. It is intentionally lean. The goal is readable, production-quality code that one engineer can build, test, and explain in a technical interview.

This is not an enterprise architecture. It does not include Domain Driven Design, Hexagonal Architecture, repositories, Unit of Work, ports, adapters, workers, queues, service buses, or other abstraction layers that do not help this assignment.

This document is the project's architecture contract. Once implementation begins:

- Do not rename folders.
- Do not move files.
- Do not introduce new architectural layers.
- Do not add enterprise patterns.
- Do not add background workers or queues.
- Do not change the request flow or responsibility boundaries.
- Any architectural change requires explicit approval.

Small bug fixes, tests, type annotations, validation improvements, and implementation details may be added inside the defined boundaries.

## 2. Scope

The service supports:

- User registration and JWT login.
- Authenticated document upload.
- PDF and plain-text document processing.
- Text chunking and embedding.
- Persistent local vector search.
- Grounded question answering.
- Source references in chat responses.
- Basic document listing and deletion.
- Request IDs and exception logging.

The chat API is stateless. It answers one question using the authenticated user's documents and does not persist conversation history. This keeps the data model and implementation small enough for the assignment.

Document indexing is synchronous during upload. This is acceptable for small assignment files. There is no worker process or queue.

## 3. Final project structure

~~~text
app/
│
├── main.py
│
├── routers/
│   ├── auth.py
│   ├── health.py
│   ├── documents.py
│   └── chat.py
│
├── services/
│   ├── auth_service.py
│   ├── document_service.py
│   ├── rag_service.py
│   └── chat_service.py
│
├── schemas/
│   ├── auth.py
│   ├── documents.py
│   └── chat.py
│
├── models/
│   ├── user.py
│   ├── document.py
│   └── error_log.py
│
├── database/
│   ├── connection.py
│   └── session.py
│
├── rag/
│   ├── chunker.py
│   ├── embedder.py
│   ├── retriever.py
│   └── generator.py
│
├── middleware/
│   ├── exception_logger.py
│   └── request_id.py
│
├── core/
│   ├── config.py
│   ├── security.py
│   └── logging.py
│
└── utils/
    └── files.py
~~~

Runtime data is stored outside the application package:

~~~text
data/
├── app.db
├── chroma/
└── uploads/
~~~

The data directory is local runtime state and must not be committed. Package marker files may be added where Python packaging requires them; they contain no application logic.

## 4. Folder responsibilities

### app/

The app/ folder contains the complete application. It is the only source package and is organized by practical responsibility rather than by an enterprise architecture pattern.

### routers/

The routers/ folder contains HTTP endpoints. Routers define paths, status codes, dependencies, request parsing, and response schemas. They do not contain database queries, file parsing, embedding logic, prompt construction, or business workflows. Each router calls the appropriate service function.

### services/

The services/ folder contains application use cases. Services coordinate database operations, validation, file handling, and RAG calls. A service may call models, database sessions, utilities, and RAG modules directly. There is no repository or Unit of Work layer between a service and the database.

### schemas/

The schemas/ folder contains Pydantic request and response models. Schemas define the public API contract and validate input. They are separate from SQLAlchemy models so database implementation details are not exposed directly in API responses.

### models/

The models/ folder contains the three SQLAlchemy database models: users, documents, and error logs. Models describe stored data and relationships only. They do not contain API logic or calls to the LLM provider.

### database/

The database/ folder contains the SQLAlchemy engine, declarative base, session factory, and FastAPI database-session dependency. It is intentionally small. Services use the session directly for straightforward queries and commits.

### rag/

The rag/ folder contains the four concrete stages of document question answering: chunking, embedding, retrieval, and generation. It contains direct calls to the selected RAG libraries and provider SDKs. There is no generic vector-store interface or provider abstraction.

### middleware/

The middleware/ folder contains cross-cutting HTTP behavior that applies to requests and responses: assigning request IDs and logging unexpected exceptions. Authentication is not middleware; it is a FastAPI dependency in core/security.py because protected routes need a current user.

### core/

The core/ folder contains application-wide configuration, JWT security, password hashing, and logging setup. It holds shared infrastructure that is used by several modules but does not represent a business workflow.

### utils/

The utils/ folder contains small stateless helpers that do not belong to a specific service, such as file-name sanitization, file-type validation, and upload-size checks. Utilities must remain small; complex business behavior belongs in services.

## 5. File responsibilities

| File | Responsibility |
|---|---|
| app/main.py | Create the FastAPI app, initialize database tables and local vector storage, register middleware and routers |
| routers/auth.py | Register, login, and current-user endpoints |
| routers/health.py | Public health endpoint |
| routers/documents.py | Authenticated upload, list, inspect, and delete endpoints |
| routers/chat.py | Authenticated question-answering endpoint |
| services/auth_service.py | Validate credentials, hash passwords, create users, and issue JWTs |
| services/document_service.py | Validate ownership, save files, create document records, and index documents |
| services/rag_service.py | Coordinate chunking, embedding, retrieval, and generation for documents and questions |
| services/chat_service.py | Validate questions, load the user's documents, call rag_service, and shape the answer |
| schemas/auth.py | Registration, login, token, and user response schemas |
| schemas/documents.py | Document upload metadata, document response, and document list schemas |
| schemas/chat.py | Question, source, and answer response schemas |
| models/user.py | User table |
| models/document.py | Document table |
| models/error_log.py | Unexpected exception log table |
| database/connection.py | SQLAlchemy engine and declarative base |
| database/session.py | Session factory and request-scoped session dependency |
| rag/chunker.py | Extracted-text chunking |
| rag/embedder.py | Direct embedding-provider calls |
| rag/retriever.py | ChromaDB persistence, indexing, similarity search, and deletion |
| rag/generator.py | Prompt construction and direct LLM answer generation |
| middleware/exception_logger.py | Catch unexpected exceptions, log them, and return safe HTTP 500 responses |
| middleware/request_id.py | Generate, propagate, and return request IDs |
| core/config.py | Environment-backed settings |
| core/security.py | Password hashing, JWT creation/decoding, and current-user dependency |
| core/logging.py | Standard Python logging configuration |
| utils/files.py | File validation, safe names, generated storage paths, and local saving |

No additional service, repository, interface, manager, factory, or provider layer is permitted without explicit architectural approval.

## 6. High-level request flow

~~~text
Client
  |
  v
FastAPI application
  |
  +--> request_id middleware
  |
  +--> exception_logger middleware
  |
  +--> router
          |
          +--> JWT current-user dependency for protected routes
          |
          +--> service
                  |
                  +--> SQLAlchemy session and models
                  +--> local filesystem
                  +--> rag_service
                          |
                          +--> chunker
                          +--> embedder
                          +--> retriever
                          +--> generator
~~~

The normal code path is:

~~~text
Router -> Service -> Database/RAG module -> Response schema
~~~

## 7. Request lifecycle

### 7.1 Every request

1. The request enters the FastAPI application.
2. request_id middleware reads X-Request-ID or generates a UUID.
3. exception_logger middleware wraps the downstream request.
4. FastAPI matches the route.
5. Protected routes execute the JWT current-user dependency.
6. FastAPI validates path, query, form, and JSON inputs against schemas.
7. The router calls one service function.
8. The service performs the use case using the database session, utilities, and RAG modules.
9. The router returns a schema-based response.
10. The request ID is added to the response header.
11. If an unexpected exception escapes the route, exception middleware logs it and returns a safe error response.

### 7.2 Document upload

1. The user sends a multipart file request with a JWT.
2. The documents router validates the request and obtains the current user.
3. document_service.py checks file type and size through utils/files.py.
4. The file is saved under data/uploads/ using a generated UUID filename.
5. A document row is inserted with status processing.
6. rag_service.py extracts text, chunks it, creates embeddings, and indexes the chunks.
7. The document row is updated to indexed.
8. The API returns the document ID, original filename, status, and creation time.
9. If processing fails, the document is marked failed where possible and the client receives a clear error.

Processing is synchronous by design. The expected assignment files are small enough that a single request can finish within a reasonable time.

### 7.3 Chat question

1. The user sends a question with a JWT.
2. The chat router obtains the current user and validates the question schema.
3. chat_service.py confirms that the user has indexed documents.
4. rag_service.py embeds the question and asks retriever.py for relevant chunks filtered by the user's document IDs.
5. generator.py builds a grounded prompt and calls the configured chat model.
6. The service returns the answer and source metadata.
7. No conversation or message row is stored.

If no relevant context is found, the service returns a safe answer stating that the uploaded documents do not contain enough information.

## 8. JWT authentication

### 8.1 Responsibilities

JWT authentication is split into two small pieces:

- services/auth_service.py handles registration, credential verification, and token issuance.
- core/security.py handles password hashing, JWT encoding/decoding, and the FastAPI get_current_user dependency.

routers/auth.py exposes the public authentication endpoints. Other routers use the current-user dependency to require authentication.

### 8.2 Authentication endpoints

| Method | Route | Purpose | Auth |
|---|---|---|---|
| POST | /api/auth/register | Create a user account | Public |
| POST | /api/auth/login | Verify credentials and return a JWT | Public |
| GET | /api/auth/me | Return the current user | JWT |

### 8.3 Login flow

1. The client posts an email and password to /api/auth/login.
2. auth_service.py loads the user by email.
3. core/security.py verifies the password against the stored password hash.
4. core/security.py creates a signed JWT containing the user ID and expiration time.
5. The auth router returns the token and basic user information.

### 8.4 Protected request flow

Clients send:

~~~text
Authorization: Bearer <jwt>
~~~

1. A protected router declares the current-user dependency.
2. core/security.py extracts the bearer token.
3. It verifies the signature, algorithm, issuer if configured, and expiration.
4. It loads the user from the database.
5. It returns the current user to the router.
6. The service uses current_user.id for document ownership filters.

JWT secrets and expiration settings come from environment configuration. Passwords are never stored in plaintext. There is no refresh-token system, role hierarchy, OAuth provider, email verification, or password reset flow in the assignment scope.

## 9. RAG pipeline

The RAG pipeline is coordinated by services/rag_service.py and implemented by four small modules.

~~~text
Document upload
  -> rag_service
      -> chunker
      -> embedder
      -> retriever

User question
  -> rag_service
      -> embedder
      -> retriever
      -> generator
~~~

### 9.1 rag/chunker.py

Receives extracted text and returns deterministic overlapping chunks. The first version should use a simple character or token limit with a small overlap. It should preserve page numbers and chunk indexes when the parser provides them.

### 9.2 rag/embedder.py

Calls the configured embedding provider directly. It exposes one function for embedding document chunks and one for embedding a user question. The same embedding model must be used for both indexing and querying.

### 9.3 rag/retriever.py

Owns the direct ChromaDB usage. It creates or opens the persistent collection, stores chunk text with metadata, performs similarity search, filters results by user-owned document IDs, and deletes chunks when a document is deleted. There is no vector-store interface.

### 9.4 rag/generator.py

Builds the prompt and calls the configured chat model directly. The prompt instructs the model to answer only from the retrieved context, treat document instructions as untrusted text, and state when the context is insufficient.

### 9.5 services/rag_service.py

Coordinates the four RAG modules. It does not contain provider implementations beyond passing data between the modules. It exposes two practical use cases:

- Index one uploaded document.
- Answer one question using the user's indexed documents.

### 9.6 Ingestion flow

~~~text
File
  -> text extraction in document_service
  -> chunker
  -> embedder
  -> retriever.index_chunks
~~~

Supported formats are PDF and plain text. File parsing stays simple and explicit. Additional formats require an explicit scope decision.

### 9.7 Query flow

~~~text
Question
  -> embedder
  -> retriever.search
  -> relevance threshold
  -> generator
  -> answer plus sources
~~~

Use a small fixed top_k, a configurable similarity threshold, and a bounded prompt size. Do not add reranking, hybrid search, query rewriting, agents, or tools.

## 10. Database design

Use SQLAlchemy with SQLite by default. SQLite avoids a separate service and is sufficient for the assignment. The database URL remains configurable so PostgreSQL can be used later if required.

ChromaDB stores vector data under data/chroma/. SQLite stores users, document metadata, and error logs.

### 10.1 users table

Defined in models/user.py.

| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| email | String | Unique, indexed |
| password_hash | String | Never store plaintext passwords |
| created_at | DateTime | UTC creation time |

### 10.2 documents table

Defined in models/document.py.

| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| user_id | Integer | Owner foreign key |
| filename | String | Original display filename |
| stored_path | String | Local upload path |
| status | String | processing, indexed, or failed |
| error_message | Text nullable | Safe processing error |
| created_at | DateTime | UTC upload time |

Every document query must filter by user_id. This is the assignment's ownership boundary.

### 10.3 error_logs table

Defined in models/error_log.py.

| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| request_id | String | Correlates with the HTTP request |
| path | String | Request path |
| method | String | HTTP method |
| exception_type | String | Exception class name |
| message | Text | Sanitized error message |
| created_at | DateTime | UTC error time |

Do not store passwords, JWTs, full document contents, prompts, or provider secrets in this table.

### 10.4 Database files

- database/connection.py creates the SQLAlchemy engine and declarative base.
- database/session.py creates the session factory and exposes the request-scoped get_db dependency.
- main.py calls SQLAlchemy metadata creation at startup.

There is no repository layer, migration layer, or Unit of Work. Services perform direct, readable queries through the injected SQLAlchemy session.

## 11. API routes

All API routes use the /api prefix except health.

### Authentication

| Method | Route | Purpose |
|---|---|---|
| POST | /api/auth/register | Register a user |
| POST | /api/auth/login | Return a JWT |
| GET | /api/auth/me | Return the authenticated user |

### Health

| Method | Route | Purpose |
|---|---|---|
| GET | /health | Public liveness check |

### Documents

| Method | Route | Purpose |
|---|---|---|
| POST | /api/documents | Upload, process, and index a document |
| GET | /api/documents | List the current user's documents |
| GET | /api/documents/{document_id} | Get one owned document |
| DELETE | /api/documents/{document_id} | Delete an owned document and its vector chunks |

### Chat

| Method | Route | Purpose |
|---|---|---|
| POST | /api/chat/query | Answer one question using the current user's indexed documents |

Example response shape:

~~~json
{
  "answer": "...",
  "sources": [
    {
      "document_id": 1,
      "filename": "handbook.pdf",
      "page": 3,
      "chunk_index": 2
    }
  ]
}
~~~

All protected endpoints return HTTP 401 for missing or invalid JWTs and HTTP 404 when a requested document does not belong to the current user.

## 12. Middleware and exception logging

### 12.1 middleware/request_id.py

This middleware runs for every request. It:

1. Reads X-Request-ID when supplied.
2. Generates a UUID when it is absent.
3. Stores the value on request.state.request_id.
4. Adds the value to the response header.

The request ID is used in logs and error responses so a reviewer can trace one request through the application.

### 12.2 middleware/exception_logger.py

This middleware wraps the entire downstream application:

~~~text
Request
  -> request_id middleware
  -> exception_logger middleware
  -> router
  -> service
  -> response
~~~

When an unexpected exception escapes the route, it:

1. Reads the request ID, method, and path.
2. Writes the full technical exception to the application logger.
3. Writes a sanitized record to the error_logs table using a short-lived database session.
4. Returns a generic HTTP 500 JSON response containing the request ID.

Expected client errors such as invalid credentials, unsupported file types, missing documents, and invalid input should be raised as normal HTTP exceptions and should not be treated as unexpected server failures.

If database logging itself fails, the middleware must still return the safe 500 response and preserve the original exception in the application log. Error logging must never create a second failure that hides the original problem.

## 13. Configuration and logging

### core/config.py

Contains a small settings object loaded from environment variables:

- DATABASE_URL, defaulting to a local SQLite file.
- CHROMA_PATH, defaulting to data/chroma.
- UPLOAD_DIR, defaulting to data/uploads.
- JWT_SECRET.
- JWT_ALGORITHM.
- JWT_EXPIRE_MINUTES.
- LLM_MODEL.
- EMBEDDING_MODEL.
- MAX_UPLOAD_SIZE_MB.
- TOP_K.
- SIMILARITY_THRESHOLD.

### core/security.py

Contains password hashing, JWT creation and decoding, bearer-token extraction, and get_current_user. It is the only module that knows JWT implementation details.

### core/logging.py

Configures standard Python logging with timestamps, log levels, module names, and request IDs where available. Logs must not include passwords, tokens, full files, or full prompts.

## 14. Recommended dependencies

### Runtime

- FastAPI.
- Uvicorn.
- SQLAlchemy.
- Pydantic Settings.
- python-multipart.
- PyJWT.
- pwdlib with Argon2 support.
- ChromaDB.
- OpenAI SDK or the selected compatible LLM SDK.
- pypdf.

### Development

- pytest.
- httpx.
- ruff.

Use direct library calls. Do not add LangChain, LlamaIndex, Celery, Redis, a cloud storage SDK, or a separate authentication platform unless the assignment explicitly requires it.

## 15. Correctness and security rules

- Passwords are hashed and never stored in plaintext.
- JWT secrets come from environment configuration.
- Every protected document query includes the current user's ID.
- Uploaded filenames are sanitized; stored filenames use generated IDs.
- File type and size are checked before processing.
- Only supported file types are parsed.
- Document status changes from processing to indexed only after all chunks are stored.
- Failed processing marks the document failed and does not expose a traceback to the client.
- Retrieved chunks are filtered to the current user's documents.
- The generator receives only retrieved context and the user question.
- Document text is treated as untrusted input.
- Source references come only from retrieved chunk metadata.
- Logs and error records exclude secrets and raw sensitive content.
- Local data directories are excluded from version control.

## 16. Testing plan

The minimum test suite should cover:

- Health endpoint returns 200.
- Registration creates a user and hashes the password.
- Login returns a valid JWT.
- Invalid credentials return 401.
- Protected endpoints reject missing JWTs.
- A user cannot read or delete another user's document.
- Unsupported files and oversized files are rejected.
- A supported document is saved, indexed, and listed.
- Retrieval returns relevant source metadata.
- Chat returns an answer and sources.
- No-context questions return a safe abstention response.
- Unexpected exceptions create an error log with a request ID.
- Document deletion removes both metadata and vector chunks.

External embedding and generation calls should be mocked in automated tests. Use temporary SQLite, upload, and ChromaDB paths.

## 17. One-day implementation sequence

### Hours 1–2: application foundation

- Create the fixed folder structure.
- Add configuration and logging.
- Add the database engine, session dependency, and three models.
- Create the FastAPI app, health route, and middleware.

### Hours 3–5: authentication

- Implement password hashing.
- Implement registration and login.
- Implement JWT creation and current-user dependency.
- Protect document and chat routes.

### Hours 6–9: document management

- Implement file validation and local saving.
- Implement document upload, listing, inspection, and deletion.
- Add document ownership checks.

### Hours 10–14: RAG

- Implement PDF and text extraction.
- Implement chunking.
- Implement embeddings.
- Implement ChromaDB indexing and retrieval.
- Implement prompt generation and answer generation.

### Hours 15–17: chat

- Implement the chat service and query endpoint.
- Add source metadata.
- Add no-context behavior and provider error handling.

### Hours 18–21: tests

- Test authentication and ownership.
- Test document lifecycle.
- Test RAG functions with mocked providers.
- Test exception logging.

### Hours 22–24: review

- Run tests and linting.
- Check OpenAPI documentation.
- Verify the complete upload-to-answer flow.
- Write setup and environment instructions.
- Remove dead code and keep each module focused.

## 18. Frozen architecture contract

The following boundaries are final:

- routers/ handles HTTP only.
- services/ handles use-case coordination.
- schemas/ defines API input and output.
- models/ defines database tables.
- database/ provides SQLAlchemy connectivity and sessions.
- rag/ implements the four direct RAG stages.
- middleware/ handles request IDs and unexpected exception logging.
- core/ handles settings, JWT security, and logging.
- utils/ contains small file helpers.

The application must remain a single FastAPI service with synchronous ingestion and stateless chat. No new layer, pattern, worker, queue, repository, adapter, or folder may be introduced without explicit approval.

This architecture is now frozen.
