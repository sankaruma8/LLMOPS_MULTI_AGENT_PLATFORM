import hashlib
import time
from functools import lru_cache
from typing import Optional
from sentence_transformers import SentenceTransformer


class EmbeddingCache:

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl_seconds

    def _make_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def get(self, text: str) -> Optional[list]:

        key = self._make_key(text)

        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["embedding"]
            else:
                del self.cache[key]

        return None

    def set(self, text: str, embedding: list):

        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache, key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

        key = self._make_key(text)
        self.cache[key] = {
            "embedding": embedding,
            "timestamp": time.time()
        }

    def get_batch(self, texts: list) -> tuple[list, list]:

        cached_embeddings = []
        texts_to_embed = []
        indices = []

        for i, text in enumerate(texts):
            cached = self.get(text)
            if cached:
                cached_embeddings.append((i, cached))
            else:
                texts_to_embed.append(text)
                indices.append(i)

        return cached_embeddings, texts_to_embed, indices

    def clear(self):
        self.cache.clear()

    def size(self):
        return len(self.cache)


embedding_cache = EmbeddingCache(max_size=1000, ttl_seconds=3600)


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

    def create_embeddings(self, chunks: list, use_cache: bool = True) -> list:

        if use_cache and len(chunks) == 1:
            cached = embedding_cache.get(chunks[0])
            if cached:
                return [cached]

        embeddings = self.model.encode(
            chunks,
            show_progress_bar=len(chunks) > 10,
            batch_size=32
        )

        embedding_list = embeddings.tolist()

        if use_cache and len(chunks) == 1:
            embedding_cache.set(chunks[0], embedding_list[0])

        return embedding_list

    def create_embeddings_batch(self, texts: list, use_cache: bool = True) -> list:

        if not use_cache:
            embeddings = self.model.encode(
                texts,
                show_progress_bar=len(texts) > 10,
                batch_size=32
            )
            return embeddings.tolist()

        cached, to_embed, indices = embedding_cache.get_batch(texts)

        results = [None] * len(texts)

        for idx, embedding in cached:
            results[idx] = embedding

        if to_embed:
            new_embeddings = self.model.encode(
                to_embed,
                show_progress_bar=len(to_embed) > 10,
                batch_size=32
            )

            for i, idx in enumerate(indices):
                embedding = new_embeddings[i].tolist()
                results[idx] = embedding
                embedding_cache.set(to_embed[i], embedding)

        return results
