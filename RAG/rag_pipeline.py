import re
from rag.embeddings import EmbeddingModel
from rag.retriever import Retriever
from agents.response_agent import get_response


def _sanitize(text: str) -> str:
    text = text.encode("ascii", errors="ignore").decode("ascii")
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', text)
    return text


class RAGPipeline:

    def __init__(self):
        self.embedder = EmbeddingModel()
        self.retriever = Retriever()

    def ask(self, question):

        query_embedding = self.embedder.create_embeddings([question])[0]
        retrieved_docs = self.retriever.retrieve(query_embedding)

        if not retrieved_docs:
            return "I couldn't find the answer in the uploaded documents."

        print("\n========== RETRIEVED CHUNKS ==========")

        contexts = []
        sources = set()

        for i, doc in enumerate(retrieved_docs, start=1):

            print(f"\nChunk {i}")
            print(f"Document : {doc['document']}")
            print(f"Page     : {doc['page']}")
            print(f"Distance : {doc['distance']:.4f}")
            print(_sanitize(doc["text"][:300]))

            contexts.append(
                f"Document: {doc['document']}\n"
                f"Page: {doc['page']}\n"
                f"Content:\n{_sanitize(doc['text'])}\n"
            )

            sources.add(f"{doc['document']} (Page {doc['page']})")

        context = "\n\n".join(contexts)

        prompt = (
            "Use the following context to answer the user's question.\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{question}\n\n"
            "ANSWER:\n"
        )

        print("\n========== PROMPT ==========\n")
        print(_sanitize(prompt[:500]))

        answer = get_response(prompt)

        if sources:
            answer += "\n\nSources:\n"
            for source in sorted(sources):
                answer += f"- {source}\n"

        return answer