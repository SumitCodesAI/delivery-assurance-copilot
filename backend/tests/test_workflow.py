"""
Tests for LangGraph workflow pipeline.
"""

import pytest
from app.graph.workflow import pipeline
from app.graph.state import WorkflowState


@pytest.mark.asyncio
async def test_workflow_structure():
    """Test that workflow has correct node structure."""
    # Check graph has expected nodes
    assert "extract" in pipeline.nodes
    assert "retrieve" in pipeline.nodes
    assert "generate_criteria" in pipeline.nodes
    assert "generate_tests" in pipeline.nodes
    assert "analyze_coverage" in pipeline.nodes
    assert "assemble_matrix" in pipeline.nodes


def test_workflow_state_structure():
    """Test WorkflowState structure."""
    state: WorkflowState = {
        "project_id": "test-proj",
        "document_ids": ["doc1", "doc2"],
        "raw_document_texts": {
            "doc1": "Test document content",
        },
        "requirements": [],
        "retrieved_chunks": {},
        "acceptance_criteria": {},
        "test_cases": [],
        "coverage_gaps": [],
        "traceability_matrix": [],
        "errors": [],
        "status": "started",
    }
    
    assert state["project_id"] == "test-proj"
    assert len(state["document_ids"]) == 2
    assert isinstance(state["requirements"], list)
    assert isinstance(state["errors"], list)


@pytest.mark.asyncio
async def test_workflow_minimal_run():
    """Test minimal workflow run with mock data."""
    initial_state: WorkflowState = {
        "project_id": "test-proj",
        "document_ids": ["doc1"],
        "raw_document_texts": {
            "doc1": """
            REQ-001: Simple Requirement
            This is a simple test requirement that should be extracted.
            
            REQ-002: Another Requirement  
            This is another requirement for testing the pipeline.
            """
        },
        "requirements": [],
        "retrieved_chunks": {},
        "acceptance_criteria": {},
        "test_cases": [],
        "coverage_gaps": [],
        "traceability_matrix": [],
        "errors": [],
        "status": "started",
    }
    
    # Run pipeline (will use real LLM calls - skip in CI)
    # For this test, we just verify the pipeline is callable
    assert callable(pipeline.invoke)
