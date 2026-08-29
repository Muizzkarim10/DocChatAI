import sys, os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "..", "ingestion"))
from parser import parse_pdf

data_path = os.path.join(current_dir, "..", "..", "data", "llm_notes.pdf")
pages = parse_pdf(data_path)

for page in pages:
    if "RAG" in page["text"] or "Retrieval-Augmented" in page["text"] or "Retrieval Augmented" in page["text"]:
        print(f"Page {page['page']}: ...{page['text'][:200]}...")
        print()