"""
ChromaDB service for vector storage and retrieval.
"""

from typing import List, Optional

import chromadb
from langchain.schema import Document

from app.config import get_settings
from app.services.embedder import DocumentEmbedder

settings = get_settings()


class ChromaService:
    """Manages ChromaDB collection and RAG retrieval."""

    def __init__(self):
        """Initialize ChromaDB client and embedder."""
        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="delivery_docs",
            metadata={"hnsw:space": "cosine"},
        )

        # Initialize embedder
        self.embedder = DocumentEmbedder()

    def add_chunks(self, chunks: List[Document], doc_id: str) -> int:
        """
        Add document chunks to ChromaDB collection.

        Args:
            chunks: List of LangChain Document objects
            doc_id: Document UUID

        Returns:
            Count of chunks added
        """
        if not chunks:
            return 0

        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        ids = [chunk.metadata.get("chunk_id", f"{doc_id}_{i}") for i, chunk in enumerate(chunks)]

        # Generate embeddings
        embeddings = self.embedder.embed_documents(texts)

        # Add to collection
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        return len(chunks)

    def query(
        self,
        query_text: str,
        project_id: str,
        top_k: int = None,
        doc_type_filter: Optional[str] = None,
    ) -> List[dict]:
        """
        Query ChromaDB collection with filters.

        Args:
            query_text: Query text to embed and search
            project_id: Project UUID for filtering
            top_k: Number of results to return
            doc_type_filter: Optional document type to filter by

        Returns:
            List of dicts with chunk_id, text, metadata, distance, and score
        """
        if top_k is None:
            top_k = settings.top_k_retrieval

        # Generate query embedding
        query_embedding = self.embedder.embed_query(query_text)

        # Build where filter
        where_filter = {"project_id": {"$eq": project_id}}
        if doc_type_filter:
            where_filter["doc_type"] = {"$eq": doc_type_filter}

        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["embeddings", "documents", "metadatas", "distances"],
        )

        # Parse results
        if not results or not results["ids"] or len(results["ids"]) == 0:
            return []

        output = []
        for i, chunk_id in enumerate(results["ids"][0]):
            # Cosine distance to similarity score (0-1)
            distance = results["distances"][0][i]
            score = 1 - (distance / 2)  # Convert cosine distance to similarity

            output.append({
                "chunk_id": chunk_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": distance,
                "score": score,
            })

        return output

    def delete_document(self, doc_id: str) -> None:
        """
        Delete all chunks for a document from ChromaDB.

        Args:
            doc_id: Document UUID
        """
        # Get all chunk IDs for this document
        where_filter = {"doc_id": {"$eq": doc_id}}

        try:
            results = self.collection.get(where=where_filter, include=[])
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])
        except Exception as e:
            # If document doesn't exist, that's fine
            pass

    def get_collection_stats(self) -> dict:
        """Get statistics about the collection."""
        count = self.collection.count()
        return {
            "collection_name": "delivery_docs",
            "total_chunks": count,
        }
