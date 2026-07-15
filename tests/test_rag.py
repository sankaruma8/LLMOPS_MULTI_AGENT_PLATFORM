import sys
import os

project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, project_root)

from rag.rag_pipeline import RAGPipeline

rag = RAGPipeline()

answer = rag.ask(
    "What is Deep Learning?"
)

print(answer)