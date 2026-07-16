"""
Tests for document parsing and ingestion.
"""

import pytest
import tempfile
from pathlib import Path
from app.services.parser import DocumentParser
from app.services.chunker import DocumentChunker
from app.services.chroma_service import ChromaService


@pytest.mark.asyncio
async def test_parse_txt():
    """Test parsing TXT files."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test requirement.\nIt should be parsed correctly.")
        f.flush()
        
        parser = DocumentParser()
        result = parser.parse(f.name, "txt")
        
        assert len(result) > 0
        assert "test requirement" in "".join(result).lower()
        
        Path(f.name).unlink()


def test_chunker():
    """Test document chunking."""
    from langchain.schema import Document
    
    texts = [
        "This is a long requirement that should be split into chunks. " * 50
    ]
    
    chunker = DocumentChunker()
    chunks = chunker.chunk(
        texts,
        {
            "doc_id": "test-doc",
            "doc_type": "brd",
            "filename": "test.txt",
            "project_id": "test-project",
        }
    )
    
    assert len(chunks) > 1
    assert all(isinstance(c, Document) for c in chunks)
    assert all("doc_id" in c.metadata for c in chunks)


def test_chroma_query():
    """Test ChromaDB operations."""
    from langchain.schema import Document
    
    chroma = ChromaService()
    
    # Create test chunks
    doc1 = Document(
        page_content="User authentication system",
        metadata={
            "doc_id": "doc1",
            "doc_type": "brd",
            "filename": "auth.txt",
            "project_id": "proj1",
            "chunk_id": "chunk1",
        }
    )
    
    doc2 = Document(
        page_content="Password reset functionality",
        metadata={
            "doc_id": "doc1",
            "doc_type": "brd",
            "filename": "auth.txt",
            "project_id": "proj1",
            "chunk_id": "chunk2",
        }
    )
    
    # Add chunks
    count = chroma.add_chunks([doc1, doc2], "doc1")
    assert count == 2
    
    # Query
    results = chroma.query(
        "authentication system",
        "proj1",
        top_k=2
    )
    
    assert len(results) > 0
    assert results[0]["score"] > 0
