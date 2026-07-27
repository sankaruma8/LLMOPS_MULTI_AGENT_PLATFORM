from rag.embeddings import EmbeddingModel
from rag.retriever import Retriever
from agents.response_agent import get_response


RETRIEVER_SYSTEM_PROMPT = (
    "You are a retrieval-augmented generation assistant. "
    "Answer questions based on the provided context from uploaded documents. "
    "Always cite the document name and page number. "
    "If the context doesn't contain enough information, say so clearly."
)


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

    def answer(self, question: str, top_k: int = 5):

        chunks = self.retrieve_chunks(question, top_k)

        if not chunks:
            return "I couldn't find relevant information in the uploaded documents.", set()

        context, sources = self.format_context(chunks)

        prompt = (
            f"CONTEXT FROM DOCUMENTS:\n{context}\n\n"
            f"USER QUESTION: {question}\n\n"
            f"Provide a detailed answer based on the context above:"
        )

        answer = get_response(prompt, system_prompt=RETRIEVER_SYSTEM_PROMPT)

        return answer, sources

    def retrieve_only(self, question: str, top_k: int = 5):

        chunks = self.retrieve_chunks(question, top_k)
        context, sources = self.format_context(chunks)
        return context, sources, chunks
