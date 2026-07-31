from pypdf import PdfReader

class DocumentLoader:

    @staticmethod
    def load_pdf(file_path):

        reader = PdfReader(file_path)

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):

            text = page.extract_text()

            if text is None:
                text = ""

            pages.append({
                "page": page_number,
                "text": text.strip()
            })

        return pages