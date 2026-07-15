import sys
import os

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, project_root)

from rag.document_loader import DocumentLoader
from rag.text_splitter import TextSplitter


text = DocumentLoader.load_pdf(
    "dataset/pdfs/deep_learning_notes.pdf"
)

chunks = TextSplitter.split_text(text)

print("Total Chunks:", len(chunks))
print()
print(chunks[0])