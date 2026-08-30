from sentence_transformers import SentenceTransformer
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
ingestion_dir = os.path.join(current_dir, "..", "ingestion")
sys.path.append(ingestion_dir)

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

def get_embedder():
    return SentenceTransformer("BAAI/bge-base-en-v1.5")


def embed_chunks(chunks: list[dict], model) -> list[dict]:
    """
    Embeds document chunks (no prefix needed — only queries get prefixed).
    """
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    return chunks


def embed_query(query: str, model):
    """
    Embeds a search query — BGE models expect a specific instruction
    prefix for queries, different from how documents are embedded.
    """
    return model.encode(QUERY_PREFIX + query)


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