import sys
import os
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


def test_create_embedding():
    from rag.embeddings import EmbeddingModel

    embedder = EmbeddingModel()
    embeddings = embedder.create_embeddings(["test"])
    assert len(embeddings) == 1
    assert len(embeddings[0]) > 0


def test_embedding_dimension():
    from rag.embeddings import EmbeddingModel

    embedder = EmbeddingModel()
    embeddings = embedder.create_embeddings(["test text"])
    assert len(embeddings[0]) == 384


def test_batch_embeddings():
    from rag.embeddings import EmbeddingModel

    embedder = EmbeddingModel()
    embeddings = embedder.create_embeddings(["text1", "text2", "text3"])
    assert len(embeddings) == 3


def test_empty_input():
    from rag.embeddings import EmbeddingModel

    embedder = EmbeddingModel()
    embeddings = embedder.create_embeddings([])
    assert len(embeddings) == 0


def test_cache_hit():
    from rag.embeddings import EmbeddingModel

    embedder = EmbeddingModel()
    embeddings1 = embedder.create_embeddings(["cached text"])
    embeddings2 = embedder.create_embeddings(["cached text"])
    assert embeddings1[0] == embeddings2[0]


def test_cache_size():
    from rag.embeddings import EmbeddingModel, embedding_cache

    initial_size = embedding_cache.size()
    embedder = EmbeddingModel()
    embedder.create_embeddings(["new text for cache"])
    assert embedding_cache.size() >= initial_size


def test_embedder_fixture(sample_text):
    from rag.embeddings import EmbeddingModel

    embedder = EmbeddingModel()
    embeddings = embedder.create_embeddings([sample_text])
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 384


@pytest.mark.skipif(
    not os.path.exists("dataset/pdfs/deep_learning_notes.pdf"),
    reason="PDF file not available"
)
def test_embedding_pipeline():
    from rag.document_loader import DocumentLoader
    from rag.text_splitter import TextSplitter
    from rag.embeddings import EmbeddingModel

    pages = DocumentLoader.load_pdf("dataset/pdfs/deep_learning_notes.pdf")
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    chunk_texts = [chunk["text"] for chunk in chunks]
    embedder = EmbeddingModel()
    embeddings = embedder.create_embeddings(chunk_texts)
    assert len(embeddings) == len(chunks)
    assert len(embeddings[0]) == 384
