import sys
import os
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


def test_load_pdf():
    from rag.document_loader import DocumentLoader

    path = "dataset/pdfs/deep_learning_notes.pdf"
    if os.path.exists(path):
        pages = DocumentLoader.load_pdf(path)
        assert len(pages) > 0
    else:
        pytest.skip("PDF file not available")


def test_load_nonexistent_pdf():
    from rag.document_loader import DocumentLoader

    with pytest.raises(Exception):
        DocumentLoader.load_pdf("nonexistent.pdf")


def test_pdf_pages_have_content():
    from rag.document_loader import DocumentLoader

    path = "dataset/pdfs/deep_learning_notes.pdf"
    if os.path.exists(path):
        pages = DocumentLoader.load_pdf(path)
        for page in pages:
            assert len(page) > 0
    else:
        pytest.skip("PDF file not available")


def test_loader_fixture():
    from rag.document_loader import DocumentLoader

    path = "dataset/pdfs/deep_learning_notes.pdf"
    if os.path.exists(path):
        pages = DocumentLoader.load_pdf(path)
        assert isinstance(pages, list)
    else:
        pytest.skip("PDF file not available")


@pytest.mark.skipif(
    not os.path.exists("dataset/pdfs/deep_learning_notes.pdf"),
    reason="PDF file not available"
)
def test_loader_integration():
    from rag.document_loader import DocumentLoader
    from rag.text_splitter import TextSplitter

    pages = DocumentLoader.load_pdf("dataset/pdfs/deep_learning_notes.pdf")
    splitter = TextSplitter()
    chunks = splitter.split_pages(pages)
    assert len(chunks) > 0
    assert isinstance(chunks, list)
