import pdfplumber
from pathlib import Path

def parse_pdf(file_path: str) -> list[dict]:
    pages = []
    file_name = Path(file_path).name

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "text": text,
                    "page": page_num,
                    "source": file_name
                })

    return pages


if __name__ == "__main__":
    result = parse_pdf("data/llm_notes.pdf")
    print(f"Extracted {len(result)} pages")
    print(result[0])