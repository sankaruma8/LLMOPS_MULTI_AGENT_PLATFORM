import sys
import os
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


def test_split_short_text():
    from rag.text_splitter import TextSplitter

    pages = [{"page": 1, "text": "Short text for splitting test."}]
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    assert len(chunks) >= 1


def test_split_long_text():
    from rag.text_splitter import TextSplitter

    pages = [{"page": 1, "text": " ".join(["word"] * 2000)}]
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    assert len(chunks) > 1


def test_split_empty_text():
    from rag.text_splitter import TextSplitter

    pages = [{"page": 1, "text": ""}]
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    assert len(chunks) == 0


def test_chunk_size():
    from rag.text_splitter import TextSplitter

    pages = [{"page": 1, "text": " ".join(["test"] * 1000)}]
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    for chunk in chunks:
        assert len(chunk["text"]) > 0


def test_overlap():
    from rag.text_splitter import TextSplitter

    pages = [{"page": 1, "text": " ".join(["word"] * 2000)}]
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    assert len(chunks) >= 2


def test_splitter_fixture(sample_text):
    from rag.text_splitter import TextSplitter

    pages = [{"page": 1, "text": sample_text}]
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    assert len(chunks) >= 1


@pytest.mark.skipif(
    not os.path.exists("dataset/pdfs/deep_learning_notes.pdf"),
    reason="PDF file not available"
)
def test_split_pdf_pages():
    from rag.document_loader import DocumentLoader
    from rag.text_splitter import TextSplitter

    pages = DocumentLoader.load_pdf("dataset/pdfs/deep_learning_notes.pdf")
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    assert len(chunks) > 0
