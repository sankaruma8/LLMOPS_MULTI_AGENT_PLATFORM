from langchain.text_splitter import RecursiveCharacterTextSplitter

class TextSplitter:

    def __init__(self):

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

    def split_pages(self, pages):

        chunks = []

        for page in pages:

            texts = self.splitter.split_text(page["text"])

            for text in texts:

                chunks.append({
                    "page": page["page"],
                    "text": text
                })

        return chunks