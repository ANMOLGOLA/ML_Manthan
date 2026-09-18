import io
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

class OCREngine:
    @staticmethod
    def extract_text(file_bytes: bytes, filename: str) -> str:
        text = ""
        filename = filename.lower()
        if filename.endswith(".pdf"):
            if not PyPDF2:
                raise RuntimeError("PyPDF2 is not installed.")
            
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            except Exception as e:
                text = f"UNREADABLE PDF: {str(e)}"
                
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            # Placeholder for image OCR (pytesseract)
            text = "UNREADABLE IMAGE - OCR for images not fully implemented. Please upload a PDF."
        else:
            # Assume text or json
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = "UNREADABLE FILE TYPE"

        return text.strip()
