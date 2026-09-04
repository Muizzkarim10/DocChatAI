# DocuChat-AI

A full-stack Retrieval-Augmented Generation (RAG) system for chatting with your own PDF documents — upload files, ask questions in natural language, and get answers grounded in your documents with page-level source citations.

Built end-to-end: document ingestion → semantic search → LLM generation → a React chat interface, fully containerized with Docker.

## Features

- **Multi-document Q&A** — upload multiple PDFs and ask questions across all of them at once
- **Source-cited answers** — every answer links back to the exact document and page it came from
- **Multi-turn conversation** — follow-up questions ("what about its types?") are automatically reformulated with context before retrieval
- **Fully local & free** — runs entirely on local models (BGE embeddings + Ollama/Llama 3.2), no API costs
- **Duplicate-upload protection** — re-uploading an already-indexed document is safely rejected
- **Dockerized** — one command spins up both frontend and backend

## Architecture

PDF Upload → Parse (pdfplumber) → Heading-aware chunking
→ Embed (BAAI/bge-base-en-v1.5) → FAISS vector index
→ [Query] → Reformulate (Ollama) → Retrieve → Generate (Ollama) → Cited answer


**Backend:** FastAPI, FAISS, sentence-transformers, Ollama
**Frontend:** React (Vite), vanilla CSS
**Deployment:** Docker Compose (multi-stage builds)

## Tech Stack

| Layer | Technology |
|---|---|
| Parsing | pdfplumber |
| Chunking | Custom heading-aware splitter |
| Embeddings | BAAI/bge-base-en-v1.5 (768-dim) |
| Vector Search | FAISS |
| LLM | Llama 3.2 via Ollama |
| Backend API | FastAPI |
| Frontend | React + Vite |
| Deployment | Docker, Docker Compose |

## Running Locally

**Prerequisites:** Python 3.11, Node.js, [Ollama](https://ollama.com) with `llama3.2` pulled, Docker Desktop (optional, for containerized run)

### Option 1 — Docker (recommended)
```bash
docker compose up --build
```
Frontend: `http://localhost:3000` · Backend: `http://localhost:8000/docs`

*Note: Ollama runs on the host machine, not in a container — make sure `ollama serve` is running before starting the containers.*

### Option 2 — Manual
```bash
# Backend
pip install -r requirements.txt
python src/ingestion/build_index.py   # build the initial index from data/
uvicorn src.api.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Server + index status |
| GET | `/documents` | List indexed documents |
| POST | `/upload` | Upload and index a new PDF |
| POST | `/ask` | Ask a question, get a cited answer |

## Engineering Notes

A few real issues found and fixed during development (rather than a "happy path only" build):

- **Chunking > embedding model for retrieval quality** — swapping to a larger embedding model didn't improve a bad retrieval ranking; the actual root cause was fixed-size chunking splitting unrelated topics into the same chunk. Rewrote chunking to be heading-aware instead.
- **Source mislabeling bug** — a hardcoded file path in the parser silently mislabeled every chunk's source as the first-ever test file. Invisible with one document, only surfaced once a second document was added — caught via systematic multi-document testing before it reached production.
- **Duplicate ingestion bug** — re-uploading an indexed file silently doubled its chunks in the vector index, degrading retrieval. Fixed with a pre-upload duplicate check.
