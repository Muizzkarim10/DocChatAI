import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "embeddings"))

from embedder import get_embedder, embed_query
from vector_store import VectorStore

store_path = os.path.join(current_dir, "..", "..", "vector_store")

model = get_embedder()
store = VectorStore(dimension=768)
store.load(store_path)

query = "What is overfitting?"
query_vector = embed_query(query, model)

results = store.search(query_vector, k=5)

print(f"\nQuery: {query}\n")
for i, r in enumerate(results, 1):
    print(f"--- Result {i} (distance: {r['distance']:.4f}) ---")
    print(f"Source: {r['source']}, Pages: {r['page_start']}-{r['page_end']}")
    print(r["text"][:200])
    print()