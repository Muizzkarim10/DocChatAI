import ollama


PROMPT_TEMPLATE = """You are a helpful assistant answering questions using ONLY the provided context.

Context:
{context}

Question: {question}

Instructions:
- Answer using only the information in the context above.
- If the context doesn't contain enough information to answer, say so clearly — don't guess or use outside knowledge.
- After your answer, cite which source/page(s) you used.
"""


def build_context(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into a single context string,
    labeled so the model can tell them apart and cite them.
    """
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[Chunk {i} — {chunk['source']}, pages {chunk['page_start']}-{chunk['page_end']}]\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(parts)


def generate_answer(question: str, chunks: list[dict], model: str = "llama3.2") -> str:
    context = build_context(chunks)
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]


if __name__ == "__main__":
    import sys, os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(current_dir, "..", "ingestion"))
    sys.path.append(os.path.join(current_dir, "..", "embeddings"))
    sys.path.append(os.path.join(current_dir, "..", "retrieval"))

    from embedder import get_embedder
    from vector_store import VectorStore

    # Load the already-saved vector store instead of rebuilding it —
    # this is why we called store.save() earlier
    store = VectorStore(dimension=384)
    store.load(os.path.join(current_dir, "..", "retrieval", "vector_store"))

    model = get_embedder()

    question = "What is fine-tuning?"
    query_vector = model.encode(question)
    chunks = store.search(query_vector, k=3)

    print("Retrieved chunks:")
    for c in chunks:
        print(f"  - {c['source']} pages {c['page_start']}-{c['page_end']} (distance: {c['distance']:.4f})")

    print("\nGenerating answer...\n")
    answer = generate_answer(question, chunks)
    print("=== Answer ===")
    print(answer)