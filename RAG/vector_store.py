import chromadb
from chromadb.config import Settings


class VectorStore:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="documents"
        )

    def add_documents(self, chunks, embeddings):

        ids = [str(i) for i in range(len(chunks))]

        self.collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings
        )

    def count(self):

        return self.collection.count()