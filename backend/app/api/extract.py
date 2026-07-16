"""
Pipeline execution API endpoints.
"""

from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.db_models import (
    Project,
    Document,
    Requirement,
    AcceptanceCriterion,
    TestCase,
    TraceabilityMatrix,
    RequirementPriorityEnum,
    CoverageStatusEnum,
    ReviewStatusEnum,
)
from app.models.pydantic_schemas import (
    PipelineRunRequest,
    PipelineRunResponse,
    RequirementResponse,
)
from app.graph.workflow import pipeline
from app.graph.state import WorkflowState
from app.services.parser import DocumentParser

router = APIRouter()


@router.post("/projects/{project_id}/run-pipeline")
async def run_pipeline(
    project_id: UUID,
    request: PipelineRunRequest = PipelineRunRequest(),
    session: AsyncSession = Depends(get_db),
) -> PipelineRunResponse:
    """
    Run the complete requirement extraction and test generation pipeline.

    Args:
        project_id: Project UUID
        request: Pipeline run request (optional document IDs)
        session: Database session

    Returns:
        Pipeline execution result
    """
    try:
        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get documents to process
        if request.document_ids:
            # Filter to specific documents
            doc_query = select(Document).where(
                (Document.project_id == project_id) &
                (Document.id.in_(request.document_ids))
            )
        else:
            # Process all documents in project
            doc_query = select(Document).where(Document.project_id == project_id)

        result = await session.execute(doc_query)
        documents = result.scalars().all()

        if not documents:
            raise HTTPException(status_code=400, detail="No documents found to process")

        # Load document texts using DocumentParser
        raw_document_texts = {}
        parser = DocumentParser()
        for doc in documents:
            try:
                # Parse document based on file type
                texts = parser.parse(doc.file_path, doc.doc_type.value)
                # Join list of text chunks into single string
                full_text = "\n\n".join(texts) if isinstance(texts, list) else texts
                raw_document_texts[str(doc.id)] = full_text
            except Exception as e:
                print(f"Warning: Could not read document {doc.id}: {str(e)}")
                continue

        if not raw_document_texts:
            raise HTTPException(status_code=400, detail="Could not read any documents")

        # Initialize workflow state
        initial_state: WorkflowState = {
            "project_id": str(project_id),
            "document_ids": [str(doc.id) for doc in documents],
            "raw_document_texts": raw_document_texts,
            "requirements": [],
            "retrieved_chunks": {},
            "acceptance_criteria": {},
            "test_cases": [],
            "coverage_gaps": [],
            "traceability_matrix": [],
            "errors": [],
            "status": "started",
        }

        # Run pipeline
        final_state = pipeline.invoke(initial_state)

        # Save results to database
        requirements_count = 0
        test_cases_count = 0
        coverage_gaps_count = 0

        try:
            # Clear existing data for this project
            delete_query = select(Requirement).where(Requirement.project_id == project_id)
            result = await session.execute(delete_query)
            existing_reqs = result.scalars().all()
            for req in existing_reqs:
                await session.delete(req)

            # Save requirements
            for req_dict in final_state.get("requirements", []):
                try:
                    doc_id = req_dict.get("document_id", "")
                    doc_uuid = UUID(doc_id) if doc_id else None

                    req = Requirement(
                        project_id=project_id,
                        document_id=doc_uuid,
                        req_id=req_dict.get("req_id", ""),
                        title=req_dict.get("title", ""),
                        description=req_dict.get("description", ""),
                        priority=RequirementPriorityEnum(req_dict.get("priority", "medium")),
                        ambiguity_flag=req_dict.get("ambiguity_flag", False),
                        ambiguity_notes=req_dict.get("ambiguity_notes"),
                        source_chunk_ids=req_dict.get("source_chunk_ids", []),
                    )
                    session.add(req)
                    await session.flush()
                    requirements_count += 1

                    # Save acceptance criteria
                    for crit_dict in final_state.get("acceptance_criteria", {}).get(req_dict.get("req_id", ""), []):
                        crit = AcceptanceCriterion(
                            requirement_id=req.id,
                            criterion_text=crit_dict.get("criterion_text", ""),
                            source_citation=crit_dict.get("source_citation"),
                            reviewer_status=ReviewStatusEnum.PENDING,
                        )
                        session.add(crit)

                    # Save test cases
                    for tc_dict in final_state.get("test_cases", []):
                        if tc_dict.get("requirement_id") == req_dict.get("req_id"):
                            tc = TestCase(
                                requirement_id=req.id,
                                title=tc_dict.get("title", ""),
                                preconditions=tc_dict.get("preconditions", ""),
                                steps=tc_dict.get("steps", []),
                                expected_result=tc_dict.get("expected_result", ""),
                                priority=RequirementPriorityEnum(tc_dict.get("priority", "medium")),
                                reviewer_status=ReviewStatusEnum.PENDING,
                            )
                            session.add(tc)
                            test_cases_count += 1

                    # Save traceability matrix row
                    for tm_dict in final_state.get("traceability_matrix", []):
                        if tm_dict.get("req_id") == req_dict.get("req_id"):
                            coverage_status = CoverageStatusEnum(tm_dict.get("coverage_status", "gap"))

                            tm = TraceabilityMatrix(
                                project_id=project_id,
                                requirement_id=req.id,
                                test_case_id=None,  # Could link if known
                                coverage_status=coverage_status,
                                gap_reason=tm_dict.get("gap_reason") if coverage_status == CoverageStatusEnum.GAP else None,
                            )
                            session.add(tm)

                except Exception as e:
                    print(f"Warning: Failed to save requirement {req_dict.get('req_id')}: {str(e)}")
                    continue

            # Save coverage gaps
            for gap_dict in final_state.get("coverage_gaps", []):
                coverage_gaps_count += 1

            await session.commit()

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Error saving pipeline results: {str(e)}")

        return PipelineRunResponse(
            project_id=str(project_id),
            status=final_state.get("status", "unknown"),
            requirements_count=requirements_count,
            test_cases_count=test_cases_count,
            coverage_gaps_count=coverage_gaps_count,
            errors=final_state.get("errors", []),
            timestamp=datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running pipeline: {str(e)}")


@router.get("/projects/{project_id}/requirements")
async def list_requirements(
    project_id: UUID,
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
) -> list[RequirementResponse]:
    """
    Get paginated list of requirements for a project.

    Args:
        project_id: Project UUID
        skip: Number of items to skip
        limit: Maximum items to return
        session: Database session

    Returns:
        List of requirements
    """
    try:
        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get requirements
        query = (
            select(Requirement)
            .where(Requirement.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .order_by(Requirement.req_id)
        )
        result = await session.execute(query)
        requirements = result.scalars().all()

        return [
            RequirementResponse(
                id=req.id,
                req_id=req.req_id,
                title=req.title,
                description=req.description,
                priority=req.priority.value,
                ambiguity_flag=req.ambiguity_flag,
                ambiguity_notes=req.ambiguity_notes,
            )
            for req in requirements
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error listing requirements: {str(e)}")


@router.get("/projects/{project_id}/requirements/{req_id}")
async def get_requirement(
    project_id: UUID,
    req_id: str,
    session: AsyncSession = Depends(get_db),
) -> RequirementResponse:
    """
    Get a specific requirement by ID.

    Args:
        project_id: Project UUID
        req_id: Requirement ID string (e.g., REQ-001)
        session: Database session

    Returns:
        Requirement details
    """
    try:
        # Get requirement
        query = select(Requirement).where(
            (Requirement.project_id == project_id) &
            (Requirement.req_id == req_id)
        )
        result = await session.execute(query)
        requirement = result.scalar_one_or_none()

        if not requirement:
            raise HTTPException(status_code=404, detail="Requirement not found")

        return RequirementResponse(
            id=requirement.id,
            req_id=requirement.req_id,
            title=requirement.title,
            description=requirement.description,
            priority=requirement.priority.value,
            ambiguity_flag=requirement.ambiguity_flag,
            ambiguity_notes=requirement.ambiguity_notes,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving requirement: {str(e)}")
