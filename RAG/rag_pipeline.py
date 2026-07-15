from rag.embeddings import EmbeddingModel
from rag.retriever import Retriever
from agents.response_agent import get_response


class RAGPipeline:

    def __init__(self):
        self.embedder = EmbeddingModel()
        self.retriever = Retriever()

    def ask(self, question):

        query_embedding = self.embedder.create_embeddings([question])[0]

        documents = self.retriever.retrieve(query_embedding)

        context = "\n\n".join(documents)

        prompt = f"""
You are an AI assistant.

Answer ONLY from the context below.

If the answer is not present, say:
"I couldn't find the answer in the uploaded document."

Context:
{context}

Question:
{question}
"""

        return get_response(prompt)