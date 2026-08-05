Backend Assignment – FastAPI + AI (RAG)
Problem Statement
Build a FastAPI backend that demonstrates good backend development practices while
implementing a basic Retrieval-Augmented Generation (RAG) pipeline. Requirements
 Implement JWT authentication with signup and login endpoints. Passwords must be
securely hashed.  Use either PostgreSQL or MongoDB as the primary database.  Design appropriate schemas and create suitable indexes. Mention your indexing choices
in the README.  Create an endpoint to ingest text documents. Store the document, chunk it, generate
embeddings, and store the chunks and embeddings.  Implement a /chat endpoint that retrieves relevant chunks and uses an LLM to answer
user queries.  Create custom FastAPI middleware that catches unhandled exceptions and logs them to
a PostgreSQL table or MongoDB collection. Log timestamp, endpoint, HTTP method, error message, stack trace, and authenticated user ID (if available). Return a proper
JSON error response.  Organize the project using a clean, modular structure. Good to Have
 Redis  Kafka or another message broker  Docker / Docker Compose
 Background jobs for document ingestion
 Streaming LLM responses  Unit tests
Submission
Share a GitHub repository with a README containing setup instructions and a .env.example
file. Timeline
 You have a maximum of 1 day (24 hours) to complete this assignment.  Please push your final code to GitHub and share the repository link before the
deadline. All
