import sys
import os

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, project_root)

from rag.document_loader import DocumentLoader
from rag.text_splitter import TextSplitter
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore


text = DocumentLoader.load_pdf(
    "dataset/pdfs/deep_learning_notes.pdf"
)

chunks = TextSplitter.split_text(text)

embedder = EmbeddingModel()

embeddings = embedder.create_embeddings(chunks)

vector_db = VectorStore()

vector_db.add_documents(
    chunks,
    embeddings
)

print("Stored Chunks :", vector_db.count())