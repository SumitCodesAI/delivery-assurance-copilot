"""
LangGraph workflow node functions for requirement processing.
"""

from datetime import datetime
from typing import Dict, List

from app.chains.extraction_chain import ExtractionChain
from app.chains.rag_chain import RAGChain
from app.graph.state import WorkflowState
from app.models.pydantic_schemas import (
    ExtractedRequirement,
    AcceptanceCriterionOutput,
    TestCaseOutput,
    TraceabilityRow,
    CoverageGap,
)
from app.services.chroma_service import ChromaService


# ============================================================================
# Node 1: Extract Requirements
# ============================================================================

def extract_requirements_node(state: WorkflowState) -> Dict:
    """
    Extract requirements from raw document texts.

    Args:
        state: Current workflow state

    Returns:
        Partial state with requirements and updated status
    """
    try:
        extraction_chain = ExtractionChain()
        all_requirements = []
        errors = state.get("errors", [])

        # Iterate over raw document texts
        for doc_id, text in state.get("raw_document_texts", {}).items():
            try:
                if not text.strip():
                    errors.append(f"Document {doc_id} has empty content")
                    continue

                # Extract requirements from this document
                result = extraction_chain.run(
                    document_text=text,
                    doc_type="general",  # Could be refined per document
                    doc_name=doc_id,
                    doc_id=doc_id,
                )

                # Convert to dicts for state
                for req in result.requirements:
                    req_dict = req.model_dump()
                    req_dict["document_id"] = doc_id
                    all_requirements.append(req_dict)

            except Exception as e:
                error_msg = f"Error extracting requirements from {doc_id}: {str(e)}"
                errors.append(error_msg)
                continue

        if not all_requirements:
            errors.append("No requirements could be extracted from any documents")

        return {
            "requirements": all_requirements,
            "status": "extraction_complete",
            "errors": errors,
        }

    except Exception as e:
        errors = state.get("errors", [])
        errors.append(f"Critical error in extract_requirements_node: {str(e)}")
        return {
            "status": "extraction_failed",
            "errors": errors,
            "requirements": [],
        }


# ============================================================================
# Node 2: Retrieve Standards
# ============================================================================

def retrieve_standards_node(state: WorkflowState) -> Dict:
    """
    Retrieve relevant standards and context from ChromaDB for each requirement.

    Args:
        state: Current workflow state

    Returns:
        Partial state with retrieved chunks
    """
    try:
        chroma_service = ChromaService()
        rag_chain = RAGChain(chroma_service)
        retrieved_chunks = {}
        errors = state.get("errors", [])
        project_id = state.get("project_id", "")

        requirements = state.get("requirements", [])

        for req_dict in requirements:
            try:
                # Convert dict back to ExtractedRequirement for typing
                req = ExtractedRequirement(**req_dict)
                req_id = req.req_id

                # Retrieve relevant chunks
                chunks = rag_chain.retrieve_for_requirement(req, project_id)
                retrieved_chunks[req_id] = chunks

            except Exception as e:
                error_msg = f"Error retrieving context for {req_dict.get('req_id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                retrieved_chunks[req_dict.get("req_id", "unknown")] = []
                continue

        return {
            "retrieved_chunks": retrieved_chunks,
            "status": "retrieval_complete",
            "errors": errors,
        }

    except Exception as e:
        errors = state.get("errors", [])
        errors.append(f"Critical error in retrieve_standards_node: {str(e)}")
        return {
            "status": "retrieval_failed",
            "errors": errors,
            "retrieved_chunks": {},
        }


# ============================================================================
# Node 3: Generate Acceptance Criteria
# ============================================================================

def generate_criteria_node(state: WorkflowState) -> Dict:
    """
    Generate acceptance criteria for each requirement using RAG.

    Args:
        state: Current workflow state

    Returns:
        Partial state with acceptance criteria
    """
    try:
        chroma_service = ChromaService()
        rag_chain = RAGChain(chroma_service)
        acceptance_criteria = {}
        errors = state.get("errors", [])

        requirements = state.get("requirements", [])
        retrieved_chunks = state.get("retrieved_chunks", {})

        for req_dict in requirements:
            try:
                req = ExtractedRequirement(**req_dict)
                req_id = req.req_id

                # Get chunks for this requirement
                chunks = retrieved_chunks.get(req_id, [])

                # Generate criteria
                criteria = rag_chain.generate_criteria(req, chunks)

                # Convert to dicts
                criteria_dicts = [c.model_dump() for c in criteria]
                acceptance_criteria[req_id] = criteria_dicts

            except Exception as e:
                error_msg = f"Error generating criteria for {req_dict.get('req_id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                acceptance_criteria[req_dict.get("req_id", "unknown")] = []
                continue

        return {
            "acceptance_criteria": acceptance_criteria,
            "status": "criteria_complete",
            "errors": errors,
        }

    except Exception as e:
        errors = state.get("errors", [])
        errors.append(f"Critical error in generate_criteria_node: {str(e)}")
        return {
            "status": "criteria_failed",
            "errors": errors,
            "acceptance_criteria": {},
        }


# ============================================================================
# Node 4: Generate Test Cases
# ============================================================================

def generate_tests_node(state: WorkflowState) -> Dict:
    """
    Generate test cases for each requirement using RAG.

    Args:
        state: Current workflow state

    Returns:
        Partial state with test cases
    """
    try:
        chroma_service = ChromaService()
        rag_chain = RAGChain(chroma_service)
        all_test_cases = []
        errors = state.get("errors", [])

        requirements = state.get("requirements", [])
        retrieved_chunks = state.get("retrieved_chunks", {})
        acceptance_criteria = state.get("acceptance_criteria", {})

        for req_dict in requirements:
            try:
                req = ExtractedRequirement(**req_dict)
                req_id = req.req_id

                # Get chunks and criteria for this requirement
                chunks = retrieved_chunks.get(req_id, [])
                criteria_dicts = acceptance_criteria.get(req_id, [])

                # Convert criteria dicts back to objects
                criteria = [
                    AcceptanceCriterionOutput(**c) for c in criteria_dicts
                ]

                # Generate test cases
                test_cases = rag_chain.generate_test_cases(req, criteria, chunks)

                # Convert to dicts and add to list
                for tc in test_cases:
                    tc_dict = tc.model_dump()
                    tc_dict["requirement_id"] = req_id
                    all_test_cases.append(tc_dict)

            except Exception as e:
                error_msg = f"Error generating tests for {req_dict.get('req_id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                continue

        return {
            "test_cases": all_test_cases,
            "status": "tests_complete",
            "errors": errors,
        }

    except Exception as e:
        errors = state.get("errors", [])
        errors.append(f"Critical error in generate_tests_node: {str(e)}")
        return {
            "status": "tests_failed",
            "errors": errors,
            "test_cases": [],
        }


# ============================================================================
# Node 5: Analyze Coverage
# ============================================================================

def analyze_coverage_node(state: WorkflowState) -> Dict:
    """
    Analyze test coverage and identify gaps.

    Args:
        state: Current workflow state

    Returns:
        Partial state with coverage gaps
    """
    try:
        coverage_gaps = []
        errors = state.get("errors", [])

        requirements = state.get("requirements", [])
        test_cases = state.get("test_cases", [])
        acceptance_criteria = state.get("acceptance_criteria", {})

        # Build a map of req_id -> test cases
        req_to_tests = {}
        for tc in test_cases:
            req_id = tc.get("requirement_id", "")
            if req_id not in req_to_tests:
                req_to_tests[req_id] = []
            req_to_tests[req_id].append(tc)

        # Check each requirement for coverage
        for req_dict in requirements:
            req_id = req_dict.get("req_id", "")
            title = req_dict.get("title", "")
            ambiguity_flag = req_dict.get("ambiguity_flag", False)

            test_count = len(req_to_tests.get(req_id, []))

            # Determine coverage status
            if test_count == 0:
                gap = CoverageGap(
                    requirement_id=req_id,
                    req_title=title,
                    reason="No test cases generated for this requirement",
                )
                coverage_gaps.append(gap.model_dump())
            elif ambiguity_flag:
                # Has tests but requirement is ambiguous
                gap = CoverageGap(
                    requirement_id=req_id,
                    req_title=title,
                    reason=f"Requirement is ambiguous: {req_dict.get('ambiguity_notes', '')}. Generated {test_count} tests but coverage is partial.",
                )
                coverage_gaps.append(gap.model_dump())

        return {
            "coverage_gaps": coverage_gaps,
            "status": "coverage_complete",
            "errors": errors,
        }

    except Exception as e:
        errors = state.get("errors", [])
        errors.append(f"Critical error in analyze_coverage_node: {str(e)}")
        return {
            "status": "coverage_failed",
            "errors": errors,
            "coverage_gaps": [],
        }


# ============================================================================
# Node 6: Assemble Traceability Matrix
# ============================================================================

def assemble_matrix_node(state: WorkflowState) -> Dict:
    """
    Assemble the traceability matrix linking requirements to test cases.

    Args:
        state: Current workflow state

    Returns:
        Partial state with traceability matrix
    """
    try:
        traceability_matrix = []
        errors = state.get("errors", [])

        requirements = state.get("requirements", [])
        test_cases = state.get("test_cases", [])

        # Build a map of req_id -> test cases
        req_to_tests = {}
        for tc in test_cases:
            req_id = tc.get("requirement_id", "")
            if req_id not in req_to_tests:
                req_to_tests[req_id] = []
            req_to_tests[req_id].append(tc)

        # Build matrix rows
        for req_dict in requirements:
            req_id = req_dict.get("req_id", "")
            title = req_dict.get("title", "")
            priority = req_dict.get("priority", "medium")
            doc_id = req_dict.get("document_id", "")
            ambiguity_flag = req_dict.get("ambiguity_flag", False)

            # Get test cases for this requirement
            tests = req_to_tests.get(req_id, [])
            test_titles = [t.get("title", "") for t in tests]

            # Determine coverage status
            if not tests:
                coverage_status = "gap"
            elif ambiguity_flag:
                coverage_status = "partial"
            else:
                coverage_status = "covered"

            # Create matrix row
            row = TraceabilityRow(
                req_id=req_id,
                req_title=title,
                req_priority=priority,
                test_case_titles=test_titles,
                coverage_status=coverage_status,
                source_documents=[doc_id] if doc_id else [],
            )

            traceability_matrix.append(row.model_dump())

        return {
            "traceability_matrix": traceability_matrix,
            "status": "complete",
            "errors": errors,
        }

    except Exception as e:
        errors = state.get("errors", [])
        errors.append(f"Critical error in assemble_matrix_node: {str(e)}")
        return {
            "status": "matrix_failed",
            "errors": errors,
            "traceability_matrix": [],
        }
