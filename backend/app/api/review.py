"""
Review management API endpoints.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.db_models import (
    Project,
    Requirement,
    TestCase,
    AcceptanceCriterion,
    ReviewSession,
    ReviewStatusEnum,
)
from app.models.pydantic_schemas import ReviewUpdateRequest, ReviewSessionResponse

router = APIRouter()


@router.get("/projects/{project_id}/review")
async def get_review_data(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get all test cases and criteria grouped by requirement for review.

    Args:
        project_id: Project UUID
        session: Database session

    Returns:
        Grouped review data
    """
    try:
        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get all requirements
        req_query = select(Requirement).where(Requirement.project_id == project_id)
        result = await session.execute(req_query)
        requirements = result.scalars().all()

        review_data = []
        for req in requirements:
            # Get criteria for this requirement
            crit_query = select(AcceptanceCriterion).where(
                AcceptanceCriterion.requirement_id == req.id
            )
            crit_result = await session.execute(crit_query)
            criteria = crit_result.scalars().all()

            # Get test cases for this requirement
            tc_query = select(TestCase).where(TestCase.requirement_id == req.id)
            tc_result = await session.execute(tc_query)
            test_cases = tc_result.scalars().all()

            review_data.append({
                "requirement": {
                    "id": str(req.id),
                    "req_id": req.req_id,
                    "title": req.title,
                    "description": req.description,
                    "priority": req.priority.value,
                    "ambiguity_flag": req.ambiguity_flag,
                    "ambiguity_notes": req.ambiguity_notes,
                },
                "acceptance_criteria": [
                    {
                        "id": str(c.id),
                        "text": c.criterion_text,
                        "source": c.source_citation,
                        "status": c.reviewer_status.value,
                        "note": c.reviewer_note,
                        "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
                    }
                    for c in criteria
                ],
                "test_cases": [
                    {
                        "id": str(tc.id),
                        "title": tc.title,
                        "preconditions": tc.preconditions,
                        "steps": tc.steps,
                        "expected_result": tc.expected_result,
                        "priority": tc.priority.value,
                        "status": tc.reviewer_status.value,
                        "note": tc.reviewer_note,
                        "reviewed_at": tc.reviewed_at.isoformat() if tc.reviewed_at else None,
                    }
                    for tc in test_cases
                ],
            })

        return {"requirements_count": len(review_data), "data": review_data}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving review data: {str(e)}")


@router.put("/test-cases/{test_case_id}/review")
async def review_test_case(
    test_case_id: UUID,
    request: ReviewUpdateRequest,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Update review status of a test case.

    Args:
        test_case_id: Test case UUID
        request: Review update request
        session: Database session

    Returns:
        Updated test case
    """
    try:
        # Get test case
        tc = await session.get(TestCase, test_case_id)
        if not tc:
            raise HTTPException(status_code=404, detail="Test case not found")

        # Update status
        tc.reviewer_status = ReviewStatusEnum(request.reviewer_status)
        tc.reviewer_note = request.reviewer_note
        tc.reviewed_at = datetime.now()

        # If edited, update steps
        if request.reviewer_status == "edited" and request.edited_text:
            # For simplicity, store edited text in note (could parse and update steps)
            tc.reviewer_note = request.edited_text

        await session.commit()

        return {
            "id": str(tc.id),
            "status": tc.reviewer_status.value,
            "note": tc.reviewer_note,
            "reviewed_at": tc.reviewed_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating test case review: {str(e)}")


@router.put("/criteria/{criterion_id}/review")
async def review_criterion(
    criterion_id: UUID,
    request: ReviewUpdateRequest,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Update review status of an acceptance criterion.

    Args:
        criterion_id: Criterion UUID
        request: Review update request
        session: Database session

    Returns:
        Updated criterion
    """
    try:
        # Get criterion
        criterion = await session.get(AcceptanceCriterion, criterion_id)
        if not criterion:
            raise HTTPException(status_code=404, detail="Criterion not found")

        # Update status
        criterion.reviewer_status = ReviewStatusEnum(request.reviewer_status)
        criterion.reviewer_note = request.reviewer_note
        criterion.reviewed_at = datetime.now()

        # If edited, update text
        if request.reviewer_status == "edited" and request.edited_text:
            criterion.criterion_text = request.edited_text

        await session.commit()

        return {
            "id": str(criterion.id),
            "status": criterion.reviewer_status.value,
            "note": criterion.reviewer_note,
            "reviewed_at": criterion.reviewed_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating criterion review: {str(e)}")


@router.post("/projects/{project_id}/review-sessions")
async def create_review_session(
    project_id: UUID,
    reviewer_name: str,
    session: AsyncSession = Depends(get_db),
) -> ReviewSessionResponse:
    """
    Start a new review session.

    Args:
        project_id: Project UUID
        reviewer_name: Name of the reviewer
        session: Database session

    Returns:
        Review session details
    """
    try:
        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Create session
        review_session = ReviewSession(
            project_id=project_id,
            reviewer_name=reviewer_name,
        )
        session.add(review_session)
        await session.commit()

        return ReviewSessionResponse(
            id=review_session.id,
            project_id=review_session.project_id,
            reviewer_name=review_session.reviewer_name,
            started_at=review_session.started_at.isoformat(),
            completed_at=None,
            approved_count=0,
            rejected_count=0,
            edited_count=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating review session: {str(e)}")


@router.put("/review-sessions/{session_id}/complete")
async def complete_review_session(
    session_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ReviewSessionResponse:
    """
    Mark a review session as complete and calculate counts.

    Args:
        session_id: Review session UUID
        session: Database session

    Returns:
        Completed review session
    """
    try:
        # Get review session
        review_session = await session.get(ReviewSession, session_id)
        if not review_session:
            raise HTTPException(status_code=404, detail="Review session not found")

        # Calculate counts from all items reviewed in this project
        project_id = review_session.project_id

        # Count by status for all requirements in project
        req_query = select(Requirement).where(Requirement.project_id == project_id)
        result = await session.execute(req_query)
        requirements = result.scalars().all()

        approved = 0
        rejected = 0
        edited = 0

        for req in requirements:
            # Count criteria
            crit_query = select(AcceptanceCriterion).where(
                AcceptanceCriterion.requirement_id == req.id
            )
            crit_result = await session.execute(crit_query)
            criteria = crit_result.scalars().all()

            for c in criteria:
                if c.reviewer_status == ReviewStatusEnum.APPROVED:
                    approved += 1
                elif c.reviewer_status == ReviewStatusEnum.REJECTED:
                    rejected += 1
                elif c.reviewer_status == ReviewStatusEnum.EDITED:
                    edited += 1

            # Count test cases
            tc_query = select(TestCase).where(TestCase.requirement_id == req.id)
            tc_result = await session.execute(tc_query)
            test_cases = tc_result.scalars().all()

            for tc in test_cases:
                if tc.reviewer_status == ReviewStatusEnum.APPROVED:
                    approved += 1
                elif tc.reviewer_status == ReviewStatusEnum.REJECTED:
                    rejected += 1
                elif tc.reviewer_status == ReviewStatusEnum.EDITED:
                    edited += 1

        # Update session
        review_session.completed_at = datetime.now()
        review_session.approved_count = approved
        review_session.rejected_count = rejected
        review_session.edited_count = edited
        await session.commit()

        return ReviewSessionResponse(
            id=review_session.id,
            project_id=review_session.project_id,
            reviewer_name=review_session.reviewer_name,
            started_at=review_session.started_at.isoformat(),
            completed_at=review_session.completed_at.isoformat(),
            approved_count=approved,
            rejected_count=rejected,
            edited_count=edited,
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=f"Error completing review session: {str(e)}")
