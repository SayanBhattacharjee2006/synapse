# Synapse

> An end-to-end AI assistant built with FastAPI and LangGraph that intelligently routes user questions across direct LLM reasoning, uploaded-document retrieval, web search, or a combination of both.

Synapse is a full-stack AI application designed around **retrieval-aware orchestration** rather than a single LLM call.

For every question, a LangGraph workflow determines which information sources are required:

- `none` — answer directly
- `rag` — retrieve information from uploaded documents
- `web` — search the web for current information
- `both` — combine uploaded-document retrieval and web search

The backend exposes the workflow through a **server-sent events (SSE) streaming API**, allowing the frontend to display execution status, streamed tokens, source provenance, titles, and errors in real time.

---

## Why Synapse?

Most AI assistants treat every question the same way.

Synapse instead separates the problem into **routing, retrieval, generation, and evaluation**.

A question such as:

> "What does the uploaded paper say about multi-head attention?"

can be routed to document retrieval.

A question such as:

> "What happened in the latest OpenAI announcement?"

can be routed to web search.

Questions requiring both private and current information can use both sources.

This makes Synapse a practical example of building a **stateful AI backend around an LLM**, rather than simply wrapping an API call.

---

## Key Engineering Features

### 🧠 Retrieval-Aware LangGraph Orchestration

The application uses LangGraph to coordinate the AI workflow.

The router can select:

```text
NONE
RAG
WEB
BOTH
```

The selected route determines which retrieval and generation stages execute.

The graph maintains state across the workflow, including:

- conversation information
- messages
- summaries
- retrieval context
- retrieval status
- web context
- web sources
- retrieved document names
- optimized RAG queries
- optimized web queries
- routing decisions

### 📚 Document RAG Pipeline

Users can upload documents to a conversation and ask questions against their private content.

Supported document types include:

- PDF
- DOC
- DOCX
- TXT
- Markdown

The retrieval pipeline uses Qdrant and performs multi-stage retrieval.

At a high level:

```text
User Query
    │
    ▼
Query Embeddings
    │
    ├── Dense representation
    ├── Sparse representation
    └── Late-interaction representation
    │
    ▼
Document Summary Retrieval
    │
    ▼
Candidate Document Filtering
    │
    ▼
Chunk-Level Retrieval
    │
    ▼
Ranking / Threshold Check
    │
    ▼
Retrieved Context
    │
    ▼
LLM
```

The document-summary stage is used to narrow the candidate document set before performing chunk-level retrieval.

Chunk retrieval uses multiple representations with Qdrant-based filtering and fusion.

Retrieved document provenance is preserved through the pipeline so the frontend can display the filenames used to answer a question.

### 🌐 Web Retrieval

Questions requiring current information can be routed to web retrieval.

Synapse uses Tavily for web search and preserves the URLs returned by the search process.

```text
User Query
    │
    ▼
Router
    │
    ▼
Web Retrieval
    │
    ▼
Tavily Search
    │
    ├── Web Context
    └── Web Sources
    │
    ▼
LLM
```

When web retrieval is used, the frontend can expose the relevant web sources to the user.

### 🔀 Combined Document + Web Retrieval

The `both` route allows the model to use both private uploaded documents and current web information.

```text
                    ┌──► Document Retrieval ──► RAG Context
                    │
User Query ─► Router
                    │
                    └──► Web Retrieval ───────► Web Context
                                      │
                                      ▼
                                     LLM
                                      │
                                      ▼
                                    Answer
```

This allows Synapse to combine private conversational knowledge with externally retrieved information.

### ⚡ Real-Time SSE Streaming

Chat responses are delivered through Server-Sent Events (SSE).

The backend doesn't wait until the entire workflow finishes before responding.

The frontend can receive structured events such as:

- `status`
- `title`
- `retrieval_found`
- `web_found`
- `error`
- streamed token data
- `[DONE]`

Status events allow the UI to display workflow progress such as:

- Understanding your question...
- Searching your uploaded documents...
- Searching the web...
- Generating answer...

LLM output is streamed incrementally as tokens arrive.

The stream therefore provides both:

- AI output
- structured workflow state

### 🔎 Source Provenance

Synapse preserves retrieval provenance from the retrieval layer through the SSE response and into the frontend.

For document retrieval, the system collects the filenames associated with retrieved chunks.

For web retrieval, it preserves the URLs returned by web search.

The frontend exposes this information through a collapsible **Sources** section.

Example:

```text
Sources
────────────────────────

Documents
  📄 attention-is-all-you-need.pdf

Web
  🔗 example.com/article
  🔗 example.org/reference
```

Sources are only displayed when provenance is actually available.

This keeps the response UI clean while still allowing users to inspect where retrieved information came from.

### 🛡️ Streaming Error Handling

Streaming failures require different handling from traditional request/response APIs.

If an exception occurs while processing the LangGraph workflow, the backend emits a structured SSE error event instead of leaving the frontend waiting indefinitely.

Example:

```text
event: error
data: {
  "status": "error",
  "message": "Something went wrong while processing your request."
}
```

The stream is then terminated with:

```text
data: [DONE]
```

This allows the frontend to distinguish between:

- normal completion
- streamed generation
- retrieval events
- backend failures

and prevents the UI from remaining stuck in a loading state after a backend failure.

### 🧠 Conversational Memory

Synapse maintains conversation state and supports summarization-based memory.

Conversation information is persisted through PostgreSQL and LangGraph checkpoints.

The system tracks:

- conversation messages
- conversation summaries
- summary state
- last summarized message
- conversation metadata

This allows longer conversations to be handled without relying entirely on the complete raw message history.

### 📊 Evaluation & Observability

Synapse includes an evaluation pipeline instead of relying solely on manual testing.

The evaluation system uses a golden dataset and runs the actual Synapse LangGraph application against it.

Evaluation covers:

- routing behavior
- retrieval behavior
- answer quality

LangSmith is used for tracing and observability.

This makes it possible to inspect the actual execution path rather than evaluating only the final generated text.

The repository currently records an evaluation baseline of:

- Router accuracy: **~98%**
- Average answer quality: **~4.6 / 5**

These figures should be regenerated whenever the evaluation dataset or methodology changes.

---

## 🏗️ Architecture

```text
                          React / Vite
                               │
                               │ HTTP / SSE
                               ▼
                         FastAPI Backend
                               │
                               ▼
                            LangGraph
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
         Direct LLM      RAG Retrieval      Web Search
                               │                │
                               ▼                ▼
                            Qdrant            Tavily
                               │                │
                               └──────┬─────────┘
                                      │
                                      ▼
                                     LLM
                                      │
                                      ▼
                                 SSE Response
                                      │
                        ┌─────────────┼─────────────┐
                        │             │             │
                     Tokens        Status        Sources
                        │             │             │
                        └─────────────┼─────────────┘
                                      ▼
                                React Frontend
```

### Infrastructure

```text
PostgreSQL
├── Users
├── Conversations
├── Messages
└── LangGraph checkpoints

Qdrant
├── Document summaries
└── Document chunks

S3-compatible storage
└── Uploaded documents

LangSmith
└── Tracing / evaluation observability

Tavily
└── Web retrieval
```

---

## 🧰 Tech Stack

### Backend

- Python
- FastAPI
- LangGraph
- LangChain
- SQLAlchemy
- Alembic
- PostgreSQL
- Qdrant
- Pydantic
- SSE

### AI / Retrieval

- OpenAI
- LangGraph
- Qdrant
- Dense embeddings
- Sparse retrieval
- Late-interaction retrieval
- Tavily web search
- LangSmith

### Frontend

- React
- Vite
- JavaScript
- SSE streaming

### Infrastructure

- Docker
- Docker Compose
- PostgreSQL
- Qdrant
- S3-compatible object storage

---

## 🚀 Getting Started

### Prerequisites

Install:

- Docker
- Docker Compose
- Node.js
- npm
- Python 3.13+
- `uv`

You will also need credentials for:

- OpenAI
- Tavily
- S3-compatible object storage

LangSmith credentials are required when tracing and evaluation are enabled.

### 1. Configure Environment Variables

From the repository root:

#### Linux / macOS

```bash
cp .env.example .env
```

#### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

Update `.env` with the required credentials and configuration.

The application configuration is defined in:

```text
backend/app/core/config.py
```

Additional configuration used by the application includes:

```dotenv
QDRANT_DOCUMENT_SUMMARY_COLLECTION=document_summaries
MAX_FILE_SIZE=10485760
CHUNK_SIZE=1000
RAG_CHUNK_SIZE=1000
RAG_OVERLAP=100
SUMMARY_CHUNK_GROUPING_THRESHOLD=10
INTERMEDIATE_SUMMARY_THRESOLD=5
SENTRY_DSN=
SENTRY_ENVIRONMENT=development
EVAL_CONVO_ID=
```

Use strong private values for `SECRET_KEY` and provider credentials.

Never commit `.env` or expose credentials in issues or pull requests.

### 2. Start Backend Infrastructure

From the repository root:

```bash
docker compose up --build -d
```

Apply database migrations:

```bash
docker compose exec backend uv run alembic upgrade head
```

The main services are available at:

| Service | Address |
|---|---|
| API | `http://localhost:8000` |
| OpenAPI | `http://localhost:8000/docs` |
| Health | `http://localhost:8000/api/v1/health` |
| Qdrant Dashboard | `http://localhost:6333/dashboard` |
| PostgreSQL | `localhost:5432` |

### 3. Start the Frontend

The frontend runs separately from Docker Compose.

Open another terminal:

```bash
cd frontend

npm install

npm run dev
```

Then open:

```text
http://localhost:5173
```

Vite proxies `/api` requests to the local backend.

To use a different API origin, configure:

```text
VITE_API_BASE_URL
```

in the frontend environment.

### 4. Use Synapse

1. Register an account.
2. Sign in.
3. Create or select a conversation.
4. Upload documents if the question requires private context.
5. Ask a question.
6. Observe the routing/retrieval status.
7. Receive the streamed answer.
8. Expand **Sources** when provenance is available.

### Example API Request

Chat requests are sent to:

```text
POST /api/v1/conversations/{conversation_id}/chat
```

Example:

```bash
curl -X POST http://localhost:8000/api/v1/conversations/<conversation-id>/chat   -H "Authorization: Bearer <access-token>"   -H "Content-Type: application/json"   -d '{"content":"Summarize the uploaded document."}'
```

The response is an SSE stream.

Possible events include:

```text
event: status
event: title
event: retrieval_found
event: web_found
event: error
data: <streamed token>
data: [DONE]
```

---

## 🧪 Testing

### Backend

From `backend/`:

```bash
uv run pytest
```

The backend tests currently focus on application health and conversation behavior.

The test environment requires PostgreSQL and the configured test settings.

### Frontend

From `frontend/`:

```bash
npm run lint
npm run build
```

---

## 📈 Evaluation

The end-to-end evaluation pipeline can be run from `backend/`:

```bash
uv run python -m evals.eval_orchestrator
```

The pipeline:

1. Loads the golden dataset.
2. Validates the dataset.
3. Runs the real Synapse LangGraph workflow.
4. Evaluates routing behavior.
5. Evaluates retrieval behavior.
6. Evaluates generated answers.
7. Produces evaluation artifacts.
8. Traces runs through LangSmith when configured.

Golden dataset:

```text
backend/evals/datasets/golden.jsonl
```

Evaluation results:

```text
backend/evals/results/
```

---

## 🔌 API Surface

The API is versioned under:

```text
/api/v1
```

Interactive API documentation is available through FastAPI's OpenAPI interface:

```text
http://localhost:8000/docs
```

### Main Resources

| Feature | Endpoint |
|---|---|
| Registration | `/auth/register` |
| Login | `/auth/login` |
| Current user | `/auth/me` |
| Conversations | `/conversations` |
| Streaming chat | `/conversations/{conversation_id}/chat` |
| Documents | `/conversations/{conversation_id}/documents` |
| Health | `/health` |

Conversation, chat, and document operations require bearer authentication.

---

## 📁 Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── graph/
│   │   │   ├── rag/
│   │   │   └── ...
│   │   ├── features/
│   │   ├── core/
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── evals/
│   │   ├── datasets/
│   │   └── results/
│   ├── tests/
│   └── pyproject.toml
│
├── frontend/
│   └── src/
│       ├── features/
│       ├── routes/
│       └── ...
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔍 Backend Development

For backend-only development:

```bash
cd backend

uv sync --dev

uv run alembic upgrade head

uv run uvicorn app.main:app   --reload   --host 0.0.0.0   --port 8000
```

When running outside Docker, use host-accessible infrastructure values such as:

```dotenv
POSTGRES_HOST=localhost
QDRANT_URL=http://localhost:6333
DATABASE_URL=<local-database-url>
```

The backend reads its environment configuration from the repository root.

---

## 📝 Design Principles

Synapse is built around several principles:

### 1. Route before retrieve

Not every question requires RAG or web search.

The router determines the required information sources before retrieval begins.

### 2. Keep retrieval state explicit

Retrieval results are represented explicitly in graph state rather than hidden inside a single opaque generation call.

### 3. Stream execution state

The frontend receives structured workflow events instead of only a final response.

### 4. Preserve provenance

Retrieved document and web source information is carried through the pipeline and exposed to the user.

### 5. Fail explicitly

Backend exceptions during streaming generate structured SSE error events so the client can terminate the loading state correctly.

### 6. Evaluate the actual system

Evaluation runs against the real application graph rather than testing an isolated mock pipeline.

---

## 🛠️ Observability

LangSmith tracing can be enabled to inspect:

- graph execution
- routing decisions
- retrieval calls
- LLM calls
- workflow metadata
- evaluation runs

Application logging is also used throughout the retrieval and streaming pipeline.

Backend logs can be viewed with:

```bash
docker compose logs -f backend
```

---

## 📚 Documentation & Development Resources

Useful project files:

```text
.env.example
docker-compose.yml
backend/app/core/config.py
backend/pyproject.toml
```

FastAPI's generated OpenAPI documentation is available while the backend is running:

```text
http://localhost:8000/docs
```

---

## 🚧 Current Status

Synapse currently provides a functional full-stack AI assistant with:

- Retrieval-aware LangGraph routing
- Direct LLM responses
- Uploaded-document RAG
- Dense + sparse + late-interaction retrieval
- Qdrant document and chunk search
- Tavily web retrieval
- Combined RAG + web retrieval
- Conversation memory and summarization
- SSE token streaming
- Streaming workflow status updates
- Streaming error handling
- Document and web provenance
- Collapsible frontend Sources UI
- PostgreSQL persistence
- S3-compatible document storage
- LangSmith observability
- Automated evaluation

The project is currently considered a completed portfolio project, with future experimentation kept separate from the core Synapse implementation.

---

## 📌 Evaluation Baseline

Current recorded baseline:

| Metric | Result |
|---|---:|
| Router accuracy | ~98% |
| Average answer quality | ~4.6 / 5 |

These numbers are tied to the current evaluation dataset and methodology and should be regenerated whenever either changes.

---

## 🤝 Contributing

Contributions are welcome.

For substantial changes:

1. Open an issue describing the change.
2. Keep pull requests focused.
3. Add or update tests for behavioral changes.
4. Run backend tests.
5. Run frontend lint/build checks.
6. Document significant architectural changes.

A dedicated `CONTRIBUTING.md` and `LICENSE` can be added when the project is prepared for external contributions.

---

## 📄 License

A formal project license has not yet been added.
