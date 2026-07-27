import chromadb
import uuid
from typing import Optional


class VectorStore:

    def __init__(self):

        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        self.collection = self.client.get_or_create_collection(
            name="documents"
        )

    def add_documents(self, filename: str, chunks: list, embeddings: list, version: int = 1, doc_id: str = None):

        prefix = f"v{version}_" if version > 1 else ""

        ids = [f"{prefix}{uuid.uuid4()}" for _ in chunks]

        documents = [chunk["text"] for chunk in chunks]

        metadata = [
            {
                "document": filename,
                "page": chunk["page"],
                "version": version,
                "doc_id": doc_id or str(uuid.uuid4())
            }
            for chunk in chunks
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadata
        )

        print(f"Stored {len(chunks)} chunks from {filename} (v{version})")
        return ids

    def retrieve(self, query_embedding: list, top_k: int = 5, filename: Optional[str] = None, version: Optional[int] = None):

        where_filter = None

        if filename and version:
            where_filter = {"$and": [{"document": filename}, {"version": version}]}
        elif filename:
            where_filter = {"document": filename}
        elif version:
            where_filter = {"version": version}

        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }

        if where_filter:
            query_params["where"] = where_filter

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
                "doc_id": meta.get("doc_id", ""),
                "distance": distance
            })

        return retrieved_docs

    def delete_by_filename(self, filename: str) -> int:

        results = self.collection.get(
            where={"document": filename},
            include=["metadatas"]
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])

        return 0

    def delete_by_doc_id(self, doc_id: str) -> int:

        results = self.collection.get(
            where={"doc_id": doc_id},
            include=["metadatas"]
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])

        return 0

    def count(self) -> int:
        return self.collection.count()

    def count_by_filename(self, filename: str) -> int:

        results = self.collection.get(
            where={"document": filename},
            include=["metadatas"]
        )

        return len(results["ids"]) if results["ids"] else 0

    def list_filenames(self) -> list:

        all_docs = self.collection.get(include=["metadatas"])

        if not all_docs["metadatas"]:
            return []

        filenames = set()
        for meta in all_docs["metadatas"]:
            filenames.add(meta["document"])

        return sorted(list(filenames))

    def get_stats(self) -> dict:

        all_docs = self.collection.get(include=["metadatas"])

        if not all_docs["metadatas"]:
            return {"total_chunks": 0, "files": 0, "file_details": {}}

        file_stats = {}
        for meta in all_docs["metadatas"]:
            filename = meta["document"]
            if filename not in file_stats:
                file_stats[filename] = {"chunks": 0, "versions": set()}
            file_stats[filename]["chunks"] += 1
            file_stats[filename]["versions"].add(meta.get("version", 1))

        for filename in file_stats:
            file_stats[filename]["versions"] = list(file_stats[filename]["versions"])

        return {
            "total_chunks": len(all_docs["ids"]),
            "files": len(file_stats),
            "file_details": file_stats
        }
