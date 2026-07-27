import os
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional

from rag.document_loader import DocumentLoader
from rag.text_splitter import TextSplitter
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from database.document_manager import document_manager

router = APIRouter()

embedder = EmbeddingModel()
splitter = TextSplitter()
vector_store = VectorStore()


def _process_upload(content: bytes, filename: str, session_id: str):
    file_hash = document_manager.compute_content_hash(content)

    duplicate_check = document_manager.check_duplicate(file_hash)
    if duplicate_check["is_duplicate"]:
        existing = duplicate_check["existing_doc"]
        return {
            "success": True,
            "status": "duplicate",
            "existing_document": {
                "filename": existing["filename"],
                "version": existing["version"],
                "chunk_count": existing["chunk_count"],
                "upload_date": existing["upload_date"]
            }
        }

    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    file_size = os.path.getsize(file_path)
    pages = DocumentLoader.load_pdf(file_path)
    page_count = len(pages)
    chunks = splitter.split_pages(pages)

    if not chunks:
        os.remove(file_path)
        return {"success": False, "error": "No text could be extracted. PDF may be image-based or scanned. Try a text-based PDF."}

    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = embedder.create_embeddings(chunk_texts)

    version = document_manager.get_next_version(filename)

    doc_metadata = document_manager.save_document_metadata(
        filename=filename,
        file_hash=file_hash,
        session_id=session_id,
        chunk_count=len(chunks),
        file_size=file_size,
        page_count=page_count,
        version=version
    )

    doc_id = doc_metadata["id"] if doc_metadata else None

    vector_store.add_documents(
        filename=filename,
        chunks=chunks,
        embeddings=embeddings,
        version=version,
        doc_id=doc_id
    )

    return {
        "success": True,
        "status": "new",
        "filename": filename,
        "version": version,
        "chunks": len(chunks),
        "pages": page_count,
        "file_size": file_size,
        "doc_id": doc_id
    }


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: str = Form(default="default-session")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, _process_upload, content, file.filename, session_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    message = "Document already exists" if result["status"] == "duplicate" else "PDF uploaded and indexed"
    return {"success": True, "message": message, "data": result}


def _process_batch(files_data: list, session_id: str):
    results = []

    for filename, content in files_data:
        if not filename.lower().endswith(".pdf"):
            results.append({"filename": filename, "success": False, "error": "Only PDF files allowed"})
            continue

        try:
            result = _process_upload(content, filename, session_id)
            if result["success"]:
                results.append({"filename": filename, **result})
            else:
                results.append({"filename": filename, "success": False, "error": result["error"]})
        except Exception as e:
            results.append({"filename": filename, "success": False, "error": str(e)})

    successful = sum(1 for r in results if r.get("success"))
    duplicates = sum(1 for r in results if r.get("status") == "duplicate")

    return {
        "success": True,
        "message": f"Batch complete: {successful} successful, {duplicates} duplicates",
        "data": {"total": len(files_data), "successful": successful, "duplicates": duplicates, "results": results}
    }


@router.post("/upload/batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    session_id: str = Form(default="default-session")
):
    files_data = []
    for file in files:
        content = await file.read()
        files_data.append((file.filename, content))

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _process_batch, files_data, session_id)


@router.get("/upload/list")
async def list_documents(session_id: Optional[str] = None):
    if session_id:
        documents = document_manager.get_session_documents(session_id)
    else:
        documents = document_manager.get_all_documents()
    return {"success": True, "data": documents, "count": len(documents)}


@router.get("/documents")
async def list_documents_v2(session_id: Optional[str] = None):
    if session_id:
        documents = document_manager.get_session_documents(session_id)
    else:
        documents = document_manager.get_all_documents()
    return {"success": True, "data": {"documents": documents, "count": len(documents)}}


@router.get("/documents/stats")
async def document_stats():
    stats = document_manager.get_storage_stats()
    vector_stats = vector_store.get_stats()
    return {"success": True, "data": {"database": stats, "vectors": vector_stats}}


@router.get("/documents/{filename}/history")
async def document_history(filename: str):
    history = document_manager.get_document_history(filename)
    return {"success": True, "data": {"filename": filename, "versions": history, "version_count": len(history)}}


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    deleted_chunks = vector_store.delete_by_filename(filename)
    deleted_metadata = document_manager.delete_document(filename)
    return {"success": True, "message": f"Document '{filename}' deleted", "data": {"deleted_chunks": deleted_chunks, "deleted_metadata": deleted_metadata}}
