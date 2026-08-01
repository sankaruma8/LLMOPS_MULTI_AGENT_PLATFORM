from typing import Optional
from sentence_transformers import SentenceTransformer


class EmbeddingModel:

    _model: Optional[SentenceTransformer] = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            print("Loading embedding model (first time only)...")
            cls._model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )
            print("Embedding model loaded.")
        return cls._model

    def __init__(self):
        self.model = self.get_model()

    def create_embeddings(self, chunks: list) -> list:
        embeddings = self.model.encode(
            chunks,
            show_progress_bar=len(chunks) > 10,
            batch_size=32
        )
        return embeddings.tolist()
