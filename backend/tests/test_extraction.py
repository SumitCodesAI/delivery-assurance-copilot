"""
Tests for requirement extraction chain.
"""

import pytest
from app.chains.extraction_chain import ExtractionChain
from app.models.pydantic_schemas import ExtractedRequirement


@pytest.mark.asyncio
async def test_extraction_chain_structure():
    """Test that extraction chain produces valid output structure."""
    chain = ExtractionChain()
    
    sample_text = """
    REQ-001: User Login
    Users must be able to login with email and password.
    
    REQ-002: Password Reset
    Users should be able to reset their password via email link.
    
    REQ-003: Account Verification
    User accounts must be verified before use (might require email confirmation).
    """
    
    result = chain.run(
        document_text=sample_text,
        doc_type="brd",
        doc_name="test.txt",
        doc_id="test-doc-1",
    )
    
    assert result.document_id == "test-doc-1"
    assert len(result.requirements) > 0
    
    for req in result.requirements:
        assert isinstance(req, ExtractedRequirement)
        assert req.req_id
        assert req.title
        assert req.description
        assert req.priority in ["high", "medium", "low"]
        assert isinstance(req.ambiguity_flag, bool)


def test_pydantic_validation():
    """Test Pydantic validation of requirements."""
    from pydantic import ValidationError
    
    # Valid requirement
    valid_req = ExtractedRequirement(
        req_id="REQ-001",
        title="Test Requirement",
        description="This is a test",
        priority="high",
        ambiguity_flag=False,
        ambiguity_notes=None,
        source_chunk_ids=["chunk1"],
    )
    assert valid_req.req_id == "REQ-001"
    
    # Invalid priority should raise
    with pytest.raises(ValidationError):
        ExtractedRequirement(
            req_id="REQ-002",
            title="Invalid",
            description="Bad priority",
            priority="critical",  # Invalid
            ambiguity_flag=False,
        )
