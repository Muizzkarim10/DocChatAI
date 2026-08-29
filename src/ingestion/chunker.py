def chunk_pages(pages: list[dict], chunk_size: int = 1500, overlap: int = 200) -> list[dict]:
    """
    Takes parsed pages and re-chunks them into fixed-size overlapping chunks,
    while preserving page/source metadata.
    """
    # Step 1: merge all pages into one continuous text stream,
    # but remember which page each character index belongs to.
    full_text = ""
    char_to_page = []  # char_to_page[i] = page number of character i

    for page in pages:
        full_text += page["text"] + "\n"
        char_to_page.extend([page["page"]] * (len(page["text"]) + 1))

    source = pages[0]["source"] if pages else "unknown"

    # Step 2: slide a window across the text with overlap
    chunks = []
    start = 0
    while start < len(full_text):
        end = start + chunk_size
        chunk_text = full_text[start:end].strip()

        if chunk_text:
            # figure out which page(s) this chunk spans
            page_start = char_to_page[start]
            page_end = char_to_page[min(end, len(full_text) - 1)]

            chunks.append({
                "text": chunk_text,
                "source": source,
                "page_start": page_start,
                "page_end": page_end
            })

        start += chunk_size - overlap  # move forward, but re-include the overlap

    return chunks


if __name__ == "__main__":
    from parser import parse_pdf

    pages = parse_pdf("data/llm_notes.pdf")
    chunks = chunk_pages(pages)

    print(f"Created {len(chunks)} chunks from {len(pages)} pages")
    print("\n--- Sample chunk ---")
    print(chunks[5]["text"][:300])
    print(f"\nSource: {chunks[5]['source']}, Pages: {chunks[5]['page_start']}-{chunks[5]['page_end']}")