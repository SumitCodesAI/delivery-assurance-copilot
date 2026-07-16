"""
Pydantic models for request/response validation and LangGraph state.
"""

from typing import Literal, Optional, TypedDict, Annotated
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Source Citation
# ============================================================================

class SourceCitation(BaseModel):
    """Citation to a source document chunk."""
    doc_name: str = Field(..., description="Name of the source document")
    chunk_id: str = Field(..., description="ID of the chunk in ChromaDB")
    excerpt: str = Field(..., max_length=300, description="Short excerpt from the chunk")


# ============================================================================
# Extracted Requirements
# ============================================================================

class ExtractedRequirement(BaseModel):
    """A single requirement extracted from a document."""
    req_id: str = Field(..., description="Requirement ID like REQ-001")
    title: str = Field(..., max_length=500, description="Short descriptive title")
    description: str = Field(..., description="Full requirement description")
    priority: Literal["high", "medium", "low"] = Field(
        "medium", description="Business priority"
    )
    ambiguity_flag: bool = Field(
        False, description="True if requirement uses vague language"
    )
    ambiguity_notes: Optional[str] = Field(
        None, description="Explanation of why it's ambiguous"
    )
    source_chunk_ids: list[str] = Field(
        default_factory=list, description="Chunk IDs that contain this requirement"
    )


class ExtractionResult(BaseModel):
    """Result of requirement extraction from a document."""
    document_id: str = Field(..., description="UUID of the document")
    requirements: list[ExtractedRequirement] = Field(
        ..., description="List of extracted requirements"
    )


# ============================================================================
# Acceptance Criteria
# ============================================================================

class AcceptanceCriterionOutput(BaseModel):
    """A single acceptance criterion for a requirement."""
    criterion_text: str = Field(..., description="The acceptance criterion text")
    source_citation: SourceCitation = Field(
        ..., description="Citation to the source that informed this criterion"
    )


# ============================================================================
# Test Cases
# ============================================================================

class TestStep(BaseModel):
    """A single step in a test case."""
    step_number: int = Field(..., description="Sequential step number starting from 1")
    action: str = Field(..., description="Action to perform in this step")
    expected_outcome: str = Field(..., description="Expected outcome of the action")


class TestCaseOutput(BaseModel):
    """A single test case for a requirement."""
    title: str = Field(..., max_length=500, description="Descriptive test case title")
    preconditions: str = Field(..., description="System state before test execution")
    steps: list[TestStep] = Field(..., description="Ordered list of test steps")
    expected_result: str = Field(..., description="Overall pass condition")
    priority: Literal["high", "medium", "low"] = Field(
        "medium", description="Test priority"
    )
    requirement_id: str = Field(..., description="REQ-ID this test case covers")


# ============================================================================
# Coverage Analysis
# ============================================================================

class CoverageGap(BaseModel):
    """A requirement with no test coverage."""
    requirement_id: str = Field(..., description="REQ-ID with coverage gap")
    req_title: str = Field(..., description="Requirement title")
    reason: str = Field(..., description="Why there's a gap")


# ============================================================================
# Traceability Matrix
# ============================================================================

class TraceabilityRow(BaseModel):
    """One row in the traceability matrix."""
    req_id: str = Field(..., description="Requirement ID")
    req_title: str = Field(..., description="Requirement title")
    req_priority: Literal["high", "medium", "low"] = Field(
        ..., description="Requirement priority"
    )
    test_case_titles: list[str] = Field(
        default_factory=list, description="Titles of linked test cases"
    )
    coverage_status: Literal["covered", "gap", "partial"] = Field(
        ..., description="Coverage status"
    )
    source_documents: list[str] = Field(
        default_factory=list, description="Source documents for this requirement"
    )


# ============================================================================
# LangGraph State
# ============================================================================

class WorkflowState(TypedDict, total=False):
    """
    State dictionary for the LangGraph workflow.
    Tracks all data flowing through the pipeline.
    """
    project_id: str
    document_ids: list[str]
    raw_document_texts: dict[str, str]  # doc_id -> full text
    requirements: list[dict]  # validated ExtractedRequirement dicts
    retrieved_chunks: dict[str, list[dict]]  # req_id -> list of chunk dicts
    acceptance_criteria: dict[str, list[dict]]  # req_id -> list of criteria dicts
    test_cases: list[dict]  # all TestCaseOutput dicts
    coverage_gaps: list[dict]  # CoverageGap dicts
    traceability_matrix: list[dict]  # TraceabilityRow dicts
    errors: list[str]  # error messages encountered
    status: str  # current pipeline status


# ============================================================================
# API Request/Response Models
# ============================================================================

class ProjectCreate(BaseModel):
    """Request to create a new project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(
        None, max_length=2000, description="Project description"
    )


class ProjectResponse(BaseModel):
    """Response containing project details."""
    id: UUID
    name: str
    description: Optional[str]
    status: str
    created_at: str
    updated_at: str
    document_count: int = 0


class DocumentResponse(BaseModel):
    """Response containing document details."""
    id: UUID
    filename: str
    doc_type: str
    status: str
    chunk_count: int
    uploaded_at: str


class RequirementResponse(BaseModel):
    """Response containing requirement details."""
    id: UUID
    req_id: str
    title: str
    description: str
    priority: str
    ambiguity_flag: bool
    ambiguity_notes: Optional[str]


class PipelineRunRequest(BaseModel):
    """Request to run the extraction pipeline."""
    document_ids: Optional[list[str]] = Field(
        None, description="Specific documents to process. If empty, processes all."
    )


class PipelineRunResponse(BaseModel):
    """Response from running the pipeline."""
    project_id: str
    status: str
    requirements_count: int
    test_cases_count: int
    coverage_gaps_count: int
    errors: list[str]
    timestamp: str


class ReviewUpdateRequest(BaseModel):
    """Request to update review status of a test case or criterion."""
    reviewer_status: Literal["approved", "rejected", "edited"] = Field(
        ..., description="New review status"
    )
    reviewer_note: Optional[str] = Field(
        None, max_length=1000, description="Reviewer notes"
    )
    edited_text: Optional[str] = Field(
        None, description="Edited text if status is 'edited'"
    )


class ReviewSessionResponse(BaseModel):
    """Response containing review session details."""
    id: UUID
    project_id: UUID
    reviewer_name: str
    started_at: str
    completed_at: Optional[str]
    approved_count: int
    rejected_count: int
    edited_count: int


# ============================================================================
# Export Models
# ============================================================================

class ExportSummary(BaseModel):
    """Summary of exported data."""
    total_requirements: int
    covered_requirements: int
    gap_requirements: int
    partial_requirements: int
    total_test_cases: int
    approved_items: int
    pending_items: int
    rejected_items: int
    approval_rate: float  # percentage


class ExportData(BaseModel):
    """Complete export data for a project."""
    project_id: str
    project_name: str
    summary: ExportSummary
    requirements: list[dict]
    test_cases: list[dict]
    acceptance_criteria: list[dict]
    traceability_matrix: list[dict]
    coverage_gaps: list[dict]
    exported_at: str
