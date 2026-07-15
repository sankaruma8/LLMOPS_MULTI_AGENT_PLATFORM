import sys
import os

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, project_root)

from rag.document_loader import DocumentLoader
from rag.text_splitter import TextSplitter
from rag.embeddings import EmbeddingModel


text = DocumentLoader.load_pdf(
    "dataset/pdfs/deep_learning_notes.pdf"
)

chunks = TextSplitter.split_text(text)

embedder = EmbeddingModel()

embeddings = embedder.create_embeddings(chunks)

print("Total Chunks :", len(chunks))
print("Embedding Dimension :", len(embeddings[0]))

print()

print(embeddings[0][:10])