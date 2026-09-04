import sys
import os
import shutil
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "embeddings"))
sys.path.append(os.path.join(current_dir, "..", "retrieval"))
sys.path.append(os.path.join(current_dir, "..", "generation"))
sys.path.append(os.path.join(current_dir, "..", "ingestion"))

from embedder import get_embedder, embed_query, embed_chunks
from chunker import chunk_pages
from parser import parse_pdf
from vector_store import VectorStore
from generator import generate_answer, reformulate_query

app = FastAPI(title="DocuChat-AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React's default dev server port
    allow_methods=["*"],
    allow_headers=["*"],
)

# Loaded once at server startup, not per-request — same principle as
# batch-encoding chunks earlier: expensive resources get loaded once and reused.
model = get_embedder()
store = VectorStore(dimension=768)
store_path = os.path.join(current_dir, "..", "..", "vector_store")
store.load(store_path)


sessions: dict[str, list[dict]] = {}

class AskRequest(BaseModel):
    question: str
    k: int = 5
    session_id: str = "default"


@app.get("/health")
def health():
    return {"status": "ok", "chunks_indexed": len(store.metadata)}


@app.post("/ask")
def ask(request: AskRequest):
    history = sessions.get(request.session_id, [])

    # Step 1: reformulate the question using conversation context
    search_query = reformulate_query(request.question, history)

    # Step 2: retrieve using the reformulated (standalone) query
    query_vector = embed_query(search_query, model)
    chunks = store.search(query_vector, k=request.k)

    # Step 3: generate the answer using the ORIGINAL question (more natural
    # for the user-facing answer) but with retrieved chunks + history as context
    answer = generate_answer(request.question, chunks, history=history)

    # Step 4: update session history
    sessions.setdefault(request.session_id, []).append({
        "question": request.question,
        "answer": answer
    })

    return {
        "question": request.question,
        "search_query_used": search_query,  # exposed for debugging/transparency
        "answer": answer,
        "sources": [
            {"source": c["source"], "pages": f"{c['page_start']}-{c['page_end']}", "distance": c["distance"]}
            for c in chunks
        ]
    }



@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Reject if this filename is already indexed
    existing_sources = set(m["source"] for m in store.metadata)
    if file.filename in existing_sources:
        return {
            "error": f"'{file.filename}' is already indexed. Upload skipped to avoid duplicates.",
            "total_chunks_in_index": len(store.metadata)
        }

    data_dir = os.path.join(current_dir, "..", "..", "data")
    save_path = os.path.join(data_dir, file.filename)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    pages = parse_pdf(save_path)
    chunks = chunk_pages(pages)
    chunks = embed_chunks(chunks, model)

    store.add_chunks(chunks)
    store.save(store_path)

    return {
        "filename": file.filename,
        "pages": len(pages),
        "chunks_added": len(chunks),
        "total_chunks_in_index": len(store.metadata)
    }

@app.get("/documents")
def list_documents():
    doc_chunk_counts = {}
    for m in store.metadata:
        doc_chunk_counts[m["source"]] = doc_chunk_counts.get(m["source"], 0) + 1

    return {
        "documents": [
            {"name": name, "chunks": count} for name, count in doc_chunk_counts.items()
        ]
    }