import hashlib
import os
from datetime import datetime
from database.supabase_client import supabase


class DocumentManager:

    def __init__(self):
        self.chunk_size = 500
        self.chunk_overlap = 50

    def compute_file_hash(self, file_path: str) -> str:

        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def compute_content_hash(self, content: bytes) -> str:

        return hashlib.sha256(content).hexdigest()

    def check_duplicate(self, file_hash: str) -> dict:

        response = (
            supabase
            .table("documents")
            .select("*")
            .eq("file_hash", file_hash)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if response.data:
            return {
                "is_duplicate": True,
                "existing_doc": response.data[0]
            }

        return {"is_duplicate": False, "existing_doc": None}

    def get_next_version(self, filename: str) -> int:

        response = (
            supabase
            .table("documents")
            .select("version")
            .eq("filename", filename)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]["version"] + 1

        return 1

    def save_document_metadata(
        self,
        filename: str,
        file_hash: str,
        session_id: str,
        chunk_count: int,
        file_size: int,
        page_count: int,
        version: int = 1
    ) -> dict:

        data = {
            "filename": filename,
            "file_hash": file_hash,
            "session_id": session_id,
            "chunk_count": chunk_count,
            "version": version,
            "file_size": file_size,
            "page_count": page_count,
            "upload_date": datetime.utcnow().isoformat()
        }

        response = supabase.table("documents").insert(data).execute()

        return response.data[0] if response.data else None

    def get_document_history(self, filename: str) -> list:

        response = (
            supabase
            .table("documents")
            .select("*")
            .eq("filename", filename)
            .order("version", desc=True)
            .execute()
        )

        return response.data if response.data else []

    def get_session_documents(self, session_id: str) -> list:

        response = (
            supabase
            .table("documents")
            .select("*")
            .eq("session_id", session_id)
            .order("upload_date", desc=True)
            .execute()
        )

        return response.data if response.data else []

    def get_all_documents(self) -> list:

        response = (
            supabase
            .table("documents")
            .select("*")
            .order("upload_date", desc=True)
            .execute()
        )

        return response.data if response.data else []

    def delete_document(self, doc_id: str) -> bool:

        try:
            supabase.table("documents").delete().eq("id", doc_id).execute()
            return True
        except Exception as e:
            print(f"Failed to delete document: {e}")
            return False

    def get_unique_documents(self) -> list:

        response = (
            supabase
            .table("documents")
            .select("filename, file_hash, chunk_count, version, upload_date")
            .order("upload_date", desc=True)
            .execute()
        )

        if not response.data:
            return []

        seen_hashes = {}
        unique_docs = []

        for doc in response.data:
            if doc["file_hash"] not in seen_hashes:
                seen_hashes[doc["file_hash"]] = doc
                unique_docs.append(doc)

        return unique_docs

    def get_storage_stats(self) -> dict:

        all_docs = self.get_all_documents()

        total_chunks = sum(d.get("chunk_count", 0) for d in all_docs)
        total_size = sum(d.get("file_size", 0) for d in all_docs)
        unique_files = len(set(d["file_hash"] for d in all_docs))

        return {
            "total_documents": len(all_docs),
            "unique_files": unique_files,
            "total_chunks": total_chunks,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }


document_manager = DocumentManager()
