"""
Document embedding service using sentence-transformers.
"""

from typing import List

from sentence_transformers import SentenceTransformer

from app.config import get_settings

settings = get_settings()


class DocumentEmbedder:
    """Generates embeddings for text using sentence-transformers."""

    _model = None  # Class-level cache

    def __init__(self):
        """Initialize the embedder by loading the model."""
        if DocumentEmbedder._model is None:
            # Load model once and cache it
            DocumentEmbedder._model = SentenceTransformer(settings.embed_model)

        self.model = DocumentEmbedder._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text documents.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors (list of floats)
        """
        if not texts:
            return []

        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text.

        Args:
            text: Query text string

        Returns:
            Embedding vector (list of floats)
        """
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
