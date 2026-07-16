"""
LangGraph workflow state definition.
"""

from typing import TypedDict


class WorkflowState(TypedDict, total=False):
    """
    State dictionary for the LangGraph requirement processing workflow.
    Tracks all data flowing through the pipeline.
    
    total=False means all keys are optional, making it more flexible.
    """
    
    # Basic pipeline inputs
    project_id: str
    document_ids: list[str]
    
    # Raw document data
    raw_document_texts: dict[str, str]  # doc_id -> full concatenated text
    
    # Extracted requirements (dicts of ExtractedRequirement)
    requirements: list[dict]
    
    # Retrieved context from ChromaDB (req_id -> chunks)
    retrieved_chunks: dict[str, list[dict]]
    
    # Generated acceptance criteria (req_id -> criteria)
    acceptance_criteria: dict[str, list[dict]]
    
    # Generated test cases
    test_cases: list[dict]
    
    # Coverage analysis results
    coverage_gaps: list[dict]
    
    # Traceability matrix
    traceability_matrix: list[dict]
    
    # Error tracking
    errors: list[str]
    
    # Pipeline status
    status: str
