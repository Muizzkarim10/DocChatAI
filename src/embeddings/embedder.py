from sentence_transformers import SentenceTransformer
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
ingestion_dir = os.path.join(current_dir, "..", "ingestion")
sys.path.append(ingestion_dir)

def get_embedder():
    """
    Loads the embedding model once. We wrap this in a function so later
    (in the FastAPI app) we load it a single time at startup, not per-request.
    """
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_chunks(chunks: list[dict], model) -> list[dict]:
    """
    Adds an 'embedding' field to each chunk dict.
    """
    texts = [chunk["text"] for chunk in chunks]

    # encode() batches internally — much faster than embedding one at a time
    embeddings = model.encode(texts, show_progress_bar=True)

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    return chunks


if __name__ == "__main__":
    from parser import parse_pdf
    from chunker import chunk_pages

    data_path = os.path.join(current_dir, "..", "..", "data", "llm_notes.pdf")
    pages = parse_pdf(data_path)
    chunks = chunk_pages(pages)

    model = get_embedder()
    chunks = embed_chunks(chunks, model)

    print(f"Embedded {len(chunks)} chunks")
    print(f"Embedding dimension: {len(chunks[0]['embedding'])}")
    print(f"First few values: {chunks[0]['embedding'][:5]}")