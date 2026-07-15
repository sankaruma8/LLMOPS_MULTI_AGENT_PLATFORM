import chromadb


class Retriever:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_collection(
            "documents"
        )

    def retrieve(self, query_embedding):

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        return result["documents"][0]