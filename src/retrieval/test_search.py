import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "ingestion"))
sys.path.append(os.path.join(current_dir, "..", "embeddings"))

from parser import parse_pdf
from chunker import chunk_pages
from embedder import get_embedder, embed_chunks
from vector_store import VectorStore

# Build the pipeline end to end
data_path = os.path.join(current_dir, "..", "..", "data", "llm_notes.pdf")
pages = parse_pdf(data_path)
chunks = chunk_pages(pages)

model = get_embedder()
chunks = embed_chunks(chunks, model)

store = VectorStore(dimension=384)
store.add_chunks(chunks)
store.save()  # persist to disk for later reuse

# Now try a real query
query = "Retrieval-Augmented Generation"
query_vector = model.encode(query)

results = store.search(query_vector, k=3)

print(f"\nQuery: {query}\n")
for i, r in enumerate(results, 1):
    print(f"--- Result {i} (distance: {r['distance']:.4f}) ---")
    print(f"Source: {r['source']}, Pages: {r['page_start']}-{r['page_end']}")
    print(r["text"][:200])
    print()