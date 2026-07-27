import chromadb
from typing import Optional


class Retriever:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_collection(
            "documents"
        )

    def retrieve(self, query_embedding: list, top_k: int = 5, filename: Optional[str] = None):

        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }

        if filename:
            query_params["where"] = {"document": filename}

        results = self.collection.query(**query_params)

        retrieved_docs = []

        if not results["documents"][0]:
            return retrieved_docs

        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):

            retrieved_docs.append({
                "text": doc,
                "document": meta["document"],
                "page": meta["page"],
                "version": meta.get("version", 1),
                "distance": distance
            })

        return retrieved_docs

    def get_all_documents(self):
        try:
            result = self.collection.get(include=["metadatas"])
            docs = set()
            for meta in result["metadatas"]:
                docs.add(meta.get("document", "unknown"))
            return list(docs)
        except Exception:
            return []
