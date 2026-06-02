"""
Embeddings layer using sentence-transformers to convert text to dense
vector representations for semantic search and retrieval.
"""

from functools import lru_cache

import numpy as np
import structlog
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load and cache the embedding model.
    lru_cache ensures we only load the model once per process, which is important for performance.
    First call downloads the model (approx 90MB), subsequent calls are fast.
    """
    logger.info("loading_embedding_model", model=settings.embedding_model)
    model = SentenceTransformer(settings.embedding_model)
    logger.info("embedding_model_loaded")
    return model


def embed_text(text: str) -> list[float]:
    """Embed a single text string."""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed multiple text in a single batch.
    Batching is significantly faster than embedding one at a time, especially for large lists.
    """
    model = get_embedding_model()
    embeddings = model.encode(
        texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False
    )
    logger.info("batch_embedding_completed", count=len(texts))
    return embeddings.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np))
