import sys
import os
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


def test_vector_store_init():
    from rag.vector_store import VectorStore

    store = VectorStore()
    assert store is not None


def test_vector_store_add():
    from rag.vector_store import VectorStore
    from rag.embeddings import EmbeddingModel

    store = VectorStore()
    embedder = EmbeddingModel()
    chunks = [
        {"page": 1, "text": "test chunk 1"},
        {"page": 2, "text": "test chunk 2"},
    ]
    embeddings = embedder.create_embeddings([c["text"] for c in chunks])
    store.add_documents("test.pdf", chunks, embeddings)
    assert store.count() >= 2


def test_vector_store_count():
    from rag.vector_store import VectorStore

    store = VectorStore()
    count = store.count()
    assert isinstance(count, int)


@pytest.mark.skipif(
    not os.path.exists("dataset/pdfs/deep_learning_notes.pdf"),
    reason="PDF file not available"
)
def test_vector_store_full_pipeline():
    from rag.document_loader import DocumentLoader
    from rag.text_splitter import TextSplitter
    from rag.embeddings import EmbeddingModel
    from rag.vector_store import VectorStore

    pages = DocumentLoader.load_pdf("dataset/pdfs/deep_learning_notes.pdf")
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    chunk_texts = [chunk["text"] for chunk in chunks]
    embedder = EmbeddingModel()
    embeddings = embedder.create_embeddings(chunk_texts)
    vector_db = VectorStore()
    vector_db.add_documents("deep_learning_notes.pdf", chunks, embeddings)
    assert vector_db.count() >= len(chunks)


def test_vector_store_search():
    from rag.vector_store import VectorStore
    from rag.embeddings import EmbeddingModel

    store = VectorStore()
    embedder = EmbeddingModel()
    chunks = [
        {"page": 1, "text": "Deep learning is a subset of machine learning"},
        {"page": 2, "text": "Neural networks have multiple layers"},
    ]
    embeddings = embedder.create_embeddings([c["text"] for c in chunks])
    store.add_documents("test.pdf", chunks, embeddings)
    query_embedding = embedder.create_embeddings(["deep learning"])[0]
    results = store.retrieve(query_embedding, top_k=1)
    assert len(results) >= 1
