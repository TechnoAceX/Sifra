import pymupdf  # Instead of import fitz

def extract_text_from_pdf(pdf_path):
    try:
        with pymupdf.open(pdf_path) as doc:  # Use pymupdf.open()
            text = [page.get_text("text") for page in doc]
        return "\n".join(text)
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None
