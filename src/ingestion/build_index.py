import sys
import os
import glob

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "embeddings"))
sys.path.append(os.path.join(current_dir, "..", "retrieval"))

from parser import parse_pdf
from chunker import chunk_pages
from embedder import get_embedder, embed_chunks
from vector_store import VectorStore


def build_index():
    data_dir = os.path.join(current_dir, "..", "..", "data")
    store_path = os.path.join(current_dir, "..", "..", "vector_store")

    pdf_paths = glob.glob(os.path.join(data_dir, "*.pdf"))
    print(f"Found {len(pdf_paths)} PDF(s): {[os.path.basename(p) for p in pdf_paths]}")

    model = get_embedder()
    store = VectorStore(dimension=768)

    for pdf_path in pdf_paths:
        file_name = os.path.basename(pdf_path)
        print(f"\nProcessing {file_name}...")

        pages = parse_pdf(pdf_path)
        chunks = chunk_pages(pages)
    
        chunks = embed_chunks(chunks, model)
        store.add_chunks(chunks)

    store.save(store_path)
    print(f"\nIndex built: {len(store.metadata)} total chunks across {len(pdf_paths)} document(s)")
    print(f"Saved to {store_path}")


if __name__ == "__main__":
    build_index()