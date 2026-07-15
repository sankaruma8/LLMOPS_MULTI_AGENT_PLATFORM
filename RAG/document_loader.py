from pypdf import PdfReader


class DocumentLoader:

    @staticmethod
    def load_pdf(file_path: str):

        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text