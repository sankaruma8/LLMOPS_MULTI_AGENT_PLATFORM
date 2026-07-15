from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextSplitter:

    @staticmethod
    def split_text(text: str):

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = splitter.split_text(text)

        return chunks