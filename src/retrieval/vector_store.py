import faiss
import numpy as np
import pickle
import os


class VectorStore:
    def __init__(self, dimension: int = 384):
        # IndexFlatL2 = brute-force exact search using L2 (Euclidean) distance.
        # "Flat" means no approximation — it checks every vector. Fine for our
        # scale (hundreds/thousands of chunks). Approximate indexes (e.g. IVF, HNSW)
        # only matter once you have millions of vectors.
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []  # parallel list: metadata[i] describes vector i in the index

    def add_chunks(self, chunks: list[dict]):
        """
        Adds embedded chunks to the index. Strips the 'embedding' field into
        FAISS itself, keeps everything else (text, source, pages) as metadata.
        """
        vectors = np.array([chunk["embedding"] for chunk in chunks]).astype("float32")
        self.index.add(vectors)

        for chunk in chunks:
            meta = {k: v for k, v in chunk.items() if k != "embedding"}
            self.metadata.append(meta)

    def search(self, query_vector, k: int = 3) -> list[dict]:
        """
        Returns the top-k most similar chunks to the query vector.
        """
        query_vector = np.array([query_vector]).astype("float32")
        distances, indices = self.index.search(query_vector, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 if fewer than k results exist
                continue
            result = self.metadata[idx].copy()
            result["distance"] = float(dist)
            results.append(result)

        return results

    def save(self, path: str = "vector_store"):
        os.makedirs(path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "metadata.pkl"), "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self, path: str = "vector_store"):
        self.index = faiss.read_index(os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "metadata.pkl"), "rb") as f:
            self.metadata = pickle.load(f)