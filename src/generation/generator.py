import ollama

OLLAMA_HOST = "http://host.docker.internal:11434"
client = ollama.Client(host=OLLAMA_HOST)

PROMPT_TEMPLATE = """You are a helpful assistant answering questions using ONLY the provided context.

Context:
{context}

Question: {question}

Instructions:
- Answer using only the information in the context above.
- If the context doesn't contain enough information to answer, say so clearly — don't guess or use outside knowledge.
- After your answer, cite which source/page(s) you used.
"""

REWRITE_PROMPT = """Given the conversation history and a follow-up question, rewrite the follow-up question to be a standalone question that includes all necessary context. If the follow-up question is already standalone, return it unchanged.

Conversation history:
{history}

Follow-up question: {question}

Standalone question:"""


def reformulate_query(question: str, history: list[dict], model: str = "llama3.2") -> str:
    if not history:
        return question  # first turn — nothing to reformulate against

    history_text = "\n".join(
        f"User: {turn['question']}\nAssistant: {turn['answer']}" for turn in history
    )
    prompt = REWRITE_PROMPT.format(history=history_text, question=question)

    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"].strip()


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


def generate_answer(question: str, chunks: list[dict], history: list[dict] = None, model: str = "llama3.2") -> str:
    context = build_context(chunks)

    history_text = ""
    if history:
        history_text = "\n\nPrevious conversation:\n" + "\n".join(
            f"User: {turn['question']}\nAssistant: {turn['answer']}" for turn in history
        )

    prompt = PROMPT_TEMPLATE.format(context=context, question=question) + history_text

    response = client.chat(
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

    from embedder import get_embedder, embed_query
    from vector_store import VectorStore

    # Load the already-saved vector store instead of rebuilding it —
    # this is why we called store.save() earlier
    store = VectorStore(dimension=768)
    store_path = os.path.join(current_dir, "..", "..", "vector_store")
    store.load(store_path)

    model = get_embedder()

    question = "What is fine-tuning?"
    query_vector = embed_query(question, model)
    chunks = store.search(query_vector, k=3)

    print("Retrieved chunks:")
    for c in chunks:
        print(f"  - {c['source']} pages {c['page_start']}-{c['page_end']} (distance: {c['distance']:.4f})")

    print("\nGenerating answer...\n")
    answer = generate_answer(question, chunks)
    print("=== Answer ===")
    print(answer)