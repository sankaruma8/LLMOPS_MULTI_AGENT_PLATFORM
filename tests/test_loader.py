import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from rag.document_loader import DocumentLoader

text = DocumentLoader.load_pdf(
    "dataset/pdfs/deep_learning_notes.pdf"
)

print(text[:1000])