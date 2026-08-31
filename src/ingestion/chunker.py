import re

HEADING_PATTERN = re.compile(r'^[A-Z][A-Za-z0-9 \-–()/]{2,60}$')


def is_likely_heading(line: str) -> bool:
    """
    Crude heuristic: short, capitalized, no terminal punctuation.
    Tuned by eyeballing this document's actual heading style
    (e.g. 'Parameter–Efficient Fine–Tuning').
    """
    line = line.strip()
    if not line or len(line) > 60:
        return False
    if line.isdigit():  # standalone page numbers
        return False
    if line.endswith((".", ",")):
        return False
    return bool(HEADING_PATTERN.match(line))


def chunk_pages(pages: list[dict], chunk_size: int = 1500) -> list[dict]:
    """
    Chunks text line-by-line, starting a new chunk when a likely heading
    is detected (topic boundary) or when the current chunk grows past
    chunk_size (safety limit for very long sections).
    """
    source = pages[0]["source"] if pages else "unknown"

    lines = []  # (line_text, page_number)
    for page in pages:
        for line in page["text"].split("\n"):
            lines.append((line, page["page"]))

    chunks = []
    current_lines = []
    current_pages = set()

    def flush():
        if not current_lines:
            return
        text = "\n".join(current_lines).strip()
        if text:
            chunks.append({
                "text": text,
                "source": source,
                "page_start": min(current_pages),
                "page_end": max(current_pages),
            })

    for line, page_num in lines:
        stripped = line.strip()

        # Only break on a heading if we already have a meaningful amount
        # of content — avoids creating tiny fragment chunks from every
        # short line that happens to match the heuristic
        if is_likely_heading(stripped) and current_lines and len("\n".join(current_lines)) > 200:
            flush()
            current_lines = []
            current_pages = set()

        current_lines.append(line)
        current_pages.add(page_num)

        if len("\n".join(current_lines)) > chunk_size:
            flush()
            current_lines = []
            current_pages = set()

    flush()
    return chunks


if __name__ == "__main__":
    from parser import parse_pdf

    pages = parse_pdf("data/llm_notes.pdf")
    chunks = chunk_pages(pages)

    print(f"Created {len(chunks)} chunks from {len(pages)} pages")
    print("\n--- Sample chunk ---")
    print(chunks[5]["text"][:300])
    print(f"\nSource: {chunks[5]['source']}, Pages: {chunks[5]['page_start']}-{chunks[5]['page_end']}")