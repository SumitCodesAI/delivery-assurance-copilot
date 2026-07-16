"""
Export API endpoints for downloading project data.
"""

import csv
import json
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.db_models import (
    Project,
    Requirement,
    TestCase,
    AcceptanceCriterion,
    TraceabilityMatrix,
    ReviewStatusEnum,
)
from app.models.pydantic_schemas import ExportData, ExportSummary

router = APIRouter()


@router.get("/projects/{project_id}/export/csv")
async def export_csv(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    Export traceability matrix as CSV.

    Args:
        project_id: Project UUID
        session: Database session

    Returns:
        CSV file download
    """
    try:
        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get traceability matrix with eager loading of relationships
        tm_query = select(TraceabilityMatrix).where(
            TraceabilityMatrix.project_id == project_id
        ).options(
            selectinload(TraceabilityMatrix.requirement).selectinload(Requirement.document),
            selectinload(TraceabilityMatrix.test_case)
        )
        result = await session.execute(tm_query)
        matrix_rows = result.scalars().all()

        # Build CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "Requirement ID",
            "Requirement Title",
            "Priority",
            "Test Case Title",
            "Test Case Steps",
            "Coverage Status",
            "Source Documents",
            "Reviewer Status",
        ])

        # Write rows
        for row in matrix_rows:
            req = row.requirement
            tc = row.test_case

            writer.writerow([
                req.req_id,
                req.title,
                req.priority.value,
                tc.title if tc else "",
                len(tc.steps) if tc and tc.steps else 0,
                row.coverage_status.value,
                doc.filename if (doc := req.document) else "",
                tc.reviewer_status.value if tc else "",
            ])

        # Return as download
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=traceability_matrix.csv"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error exporting CSV: {str(e)}")


@router.get("/projects/{project_id}/export/json")
async def export_json(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    Export complete project data as JSON.

    Args:
        project_id: Project UUID
        session: Database session

    Returns:
        JSON file download
    """
    try:
        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get all data with eager loading
        req_query = select(Requirement).where(
            Requirement.project_id == project_id
        ).options(
            selectinload(Requirement.criteria),
            selectinload(Requirement.test_cases),
            selectinload(Requirement.document),
            selectinload(Requirement.traceability_matrix)
        )
        result = await session.execute(req_query)
        requirements = result.scalars().all()

        # Build requirements data
        requirements_data = []
        test_cases_data = []
        criteria_data = []
        matrix_data = []
        covered_count = 0
        gap_count = 0
        partial_count = 0
        approved_count = 0
        pending_count = 0
        rejected_count = 0

        for req in requirements:
            req_dict = {
                "id": str(req.id),
                "req_id": req.req_id,
                "title": req.title,
                "description": req.description,
                "priority": req.priority.value,
                "ambiguity_flag": req.ambiguity_flag,
                "ambiguity_notes": req.ambiguity_notes,
            }
            requirements_data.append(req_dict)

            # Get criteria from already-loaded relationship
            criteria = req.criteria

            for c in criteria:
                criteria_data.append({
                    "id": str(c.id),
                    "requirement_id": str(req.id),
                    "text": c.criterion_text,
                    "source": c.source_citation,
                    "status": c.reviewer_status.value,
                })
                if c.reviewer_status == ReviewStatusEnum.APPROVED:
                    approved_count += 1
                elif c.reviewer_status == ReviewStatusEnum.PENDING:
                    pending_count += 1
                elif c.reviewer_status == ReviewStatusEnum.REJECTED:
                    rejected_count += 1

            # Get test cases from already-loaded relationship
            test_cases = req.test_cases

            for tc in test_cases:
                test_cases_data.append({
                    "id": str(tc.id),
                    "requirement_id": str(req.id),
                    "title": tc.title,
                    "preconditions": tc.preconditions,
                    "steps": tc.steps,
                    "expected_result": tc.expected_result,
                    "priority": tc.priority.value,
                    "status": tc.reviewer_status.value,
                })
                if tc.reviewer_status == ReviewStatusEnum.APPROVED:
                    approved_count += 1
                elif tc.reviewer_status == ReviewStatusEnum.PENDING:
                    pending_count += 1
                elif tc.reviewer_status == ReviewStatusEnum.REJECTED:
                    rejected_count += 1

            # Get matrix rows from already-loaded relationship
            matrix_rows = req.traceability_matrix

            for tm in matrix_rows:
                matrix_data.append({
                    "requirement_id": str(req.id),
                    "test_case_id": str(tm.test_case_id) if tm.test_case_id else None,
                    "coverage_status": tm.coverage_status.value,
                    "gap_reason": tm.gap_reason,
                })

                if tm.coverage_status.value == "covered":
                    covered_count += 1
                elif tm.coverage_status.value == "gap":
                    gap_count += 1
                elif tm.coverage_status.value == "partial":
                    partial_count += 1

        # Build summary
        total_items = len(requirements_data) + len(test_cases_data) + len(criteria_data)
        approval_rate = (approved_count / total_items * 100) if total_items > 0 else 0

        summary = ExportSummary(
            total_requirements=len(requirements_data),
            covered_requirements=covered_count,
            gap_requirements=gap_count,
            partial_requirements=partial_count,
            total_test_cases=len(test_cases_data),
            approved_items=approved_count,
            pending_items=pending_count,
            rejected_items=rejected_count,
            approval_rate=approval_rate,
        )

        # Build export data
        export_data = ExportData(
            project_id=str(project_id),
            project_name=project.name,
            summary=summary,
            requirements=requirements_data,
            test_cases=test_cases_data,
            acceptance_criteria=criteria_data,
            traceability_matrix=matrix_data,
            coverage_gaps=[],  # TODO: populate from analysis
            exported_at=datetime.now().isoformat(),
        )

        # Return as JSON download
        json_str = json.dumps(export_data.model_dump(), indent=2)
        output = io.BytesIO(json_str.encode())

        return StreamingResponse(
            iter([json_str]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=export.json"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error exporting JSON: {str(e)}")


@router.get("/projects/{project_id}/export/summary")
async def export_summary(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get export summary statistics.

    Args:
        project_id: Project UUID
        session: Database session

    Returns:
        Summary statistics
    """
    try:
        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get counts
        req_query = select(Requirement).where(Requirement.project_id == project_id)
        result = await session.execute(req_query)
        requirements = result.scalars().all()

        total_reqs = len(requirements)
        total_criteria = 0
        total_tests = 0
        approved = 0
        pending = 0
        rejected = 0

        covered = 0
        gap = 0
        partial = 0

        for req in requirements:
            # Count criteria
            crit_query = select(AcceptanceCriterion).where(
                AcceptanceCriterion.requirement_id == req.id
            )
            crit_result = await session.execute(crit_query)
            criteria = crit_result.scalars().all()
            total_criteria += len(criteria)

            for c in criteria:
                if c.reviewer_status == ReviewStatusEnum.APPROVED:
                    approved += 1
                elif c.reviewer_status == ReviewStatusEnum.PENDING:
                    pending += 1
                elif c.reviewer_status == ReviewStatusEnum.REJECTED:
                    rejected += 1

            # Count test cases
            tc_query = select(TestCase).where(TestCase.requirement_id == req.id)
            tc_result = await session.execute(tc_query)
            test_cases = tc_result.scalars().all()
            total_tests += len(test_cases)

            for tc in test_cases:
                if tc.reviewer_status == ReviewStatusEnum.APPROVED:
                    approved += 1
                elif tc.reviewer_status == ReviewStatusEnum.PENDING:
                    pending += 1
                elif tc.reviewer_status == ReviewStatusEnum.REJECTED:
                    rejected += 1

            # Count matrix rows
            tm_query = select(TraceabilityMatrix).where(
                TraceabilityMatrix.requirement_id == req.id
            )
            tm_result = await session.execute(tm_query)
            matrix_rows = tm_result.scalars().all()

            for tm in matrix_rows:
                if tm.coverage_status.value == "covered":
                    covered += 1
                elif tm.coverage_status.value == "gap":
                    gap += 1
                elif tm.coverage_status.value == "partial":
                    partial += 1

        total_items = total_criteria + total_tests
        approval_rate = (approved / total_items * 100) if total_items > 0 else 0

        return {
            "project_id": str(project_id),
            "project_name": project.name,
            "total_requirements": total_reqs,
            "total_criteria": total_criteria,
            "total_test_cases": total_tests,
            "covered_requirements": covered,
            "gap_requirements": gap,
            "partial_requirements": partial,
            "approved_items": approved,
            "pending_items": pending,
            "rejected_items": rejected,
            "approval_rate": round(approval_rate, 2),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error getting export summary: {str(e)}")
