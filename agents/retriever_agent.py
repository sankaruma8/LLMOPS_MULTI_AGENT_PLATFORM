from rag.embeddings import EmbeddingModel
from rag.retriever import Retriever


class RetrieverAgent:

    def __init__(self):
        self.embedder = EmbeddingModel()
        self.retriever = Retriever()

    def retrieve_chunks(self, question: str, top_k: int = 5):

        query_embedding = self.embedder.create_embeddings([question])[0]
        return self.retriever.retrieve(query_embedding, top_k=top_k)

    def format_context(self, chunks: list) -> str:

        contexts = []
        sources = set()

        for chunk in chunks:
            contexts.append(
                f"Document: {chunk['document']}\n"
                f"Page: {chunk['page']}\n"
                f"Content: {chunk['text']}\n"
            )
            sources.add(f"{chunk['document']} (Page {chunk['page']})")

        return "\n---\n".join(contexts), sources
