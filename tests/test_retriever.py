import sys
import os

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, project_root)

from rag.embeddings import EmbeddingModel
from rag.retriever import Retriever

embedder = EmbeddingModel()

query = "What is Deep Learning?"

query_embedding = embedder.create_embeddings([query])[0]

retriever = Retriever()

documents = retriever.retrieve(query_embedding)

print()

for i, doc in enumerate(documents, start=1):
    print(f"Chunk {i}")
    print("-" * 60)
    print(doc)
    print()