"""
Document chunking service using LangChain text splitters.
"""

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.config import get_settings

settings = get_settings()


class DocumentChunker:
    """Chunks documents into smaller pieces for embedding."""

    def __init__(self):
        """Initialize the text splitter."""
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, texts: List[str], doc_metadata: dict) -> List[Document]:
        """
        Split texts into chunks and create Document objects with metadata.

        Args:
            texts: List of text sections from a document
            doc_metadata: Metadata dict with keys:
                - doc_id: UUID of the document
                - doc_type: Type of document
                - filename: Name of the file
                - project_id: Project UUID

        Returns:
            List of LangChain Document objects with metadata
        """
        documents = []

        for page_idx, text in enumerate(texts):
            if not text.strip():
                continue

            # Split page into chunks
            chunks = self.splitter.split_text(text)

            for chunk_idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                # Create unique chunk ID
                chunk_id = f"{doc_metadata['doc_id']}_{page_idx}_{chunk_idx}"

                # Create metadata
                metadata = {
                    **doc_metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_idx,
                    "page_index": page_idx,
                }

                # Create Document
                doc = Document(page_content=chunk, metadata=metadata)
                documents.append(doc)

        return documents
