"""
Upload API endpoints for document ingestion.
"""

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.config import get_settings
from app.models.db_models import Project, Document, DocumentStatusEnum, DocumentTypeEnum
from app.models.pydantic_schemas import ProjectCreate, ProjectResponse, DocumentResponse
from app.services.parser import DocumentParser
from app.services.chunker import DocumentChunker
from app.services.chroma_service import ChromaService

router = APIRouter()
settings = get_settings()


# ============================================================================
# Project Management
# ============================================================================

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_create: ProjectCreate,
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Create a new project.

    Args:
        project_create: Project creation request
        session: Database session

    Returns:
        Created project details
    """
    try:
        project = Project(
            name=project_create.name,
            description=project_create.description,
        )
        session.add(project)
        await session.flush()

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status.value,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            document_count=0,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating project: {str(e)}")


@router.get("/projects")
async def list_projects(
    session: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    """
    List all projects with document counts.

    Args:
        session: Database session

    Returns:
        List of projects
    """
    try:
        from sqlalchemy import select, func

        query = select(Project)
        result = await session.execute(query)
        projects = result.scalars().all()

        responses = []
        for project in projects:
            # Count documents for this project
            doc_query = select(func.count(Document.id)).where(
                Document.project_id == project.id
            )
            doc_result = await session.execute(doc_query)
            doc_count = doc_result.scalar() or 0

            responses.append(ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status.value,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat(),
                document_count=doc_count,
            ))

        return responses

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error listing projects: {str(e)}")


@router.get("/projects/{project_id}")
async def get_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Get project details.

    Args:
        project_id: Project UUID
        session: Database session

    Returns:
        Project details
    """
    try:
        from sqlalchemy import select, func

        # Get project
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Count documents
        doc_query = select(func.count(Document.id)).where(
            Document.project_id == project.id
        )
        doc_result = await session.execute(doc_query)
        doc_count = doc_result.scalar() or 0

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status.value,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
            document_count=doc_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving project: {str(e)}")


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    """
    Delete a project and all its associated data.
    
    This includes:
    - All documents in the project
    - All requirements extracted from documents
    - All test cases
    - All acceptance criteria
    - All embeddings in ChromaDB
    - All Jira mappings
    
    Args:
        project_id: Project UUID
        session: Database session
    
    Returns:
        Deletion confirmation
    """
    try:
        from sqlalchemy import select, delete
        
        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_name = project.name
        
        # Step 1: Delete all associated embeddings from ChromaDB
        try:
            chroma = ChromaService()
            # Get all documents for this project
            doc_query = select(Document).where(Document.project_id == project_id)
            doc_result = await session.execute(doc_query)
            documents = doc_result.scalars().all()
            
            # Delete embeddings for each document
            for doc in documents:
                try:
                    chroma.delete_collection(str(doc.id))
                except Exception as e:
                    print(f"Warning: Failed to delete ChromaDB collection for doc {doc.id}: {e}")
        except Exception as e:
            print(f"Warning: Failed to delete ChromaDB embeddings: {e}")
        
        # Step 2: Delete Jira addon data first (no foreign key constraints to other tables)
        try:
            from app.addons.jira_addon.models import (
                JiraConnection, 
                JiraRequirementMapping, 
                JiraTestMapping, 
                JiraSyncHistory
            )
            
            # Delete in order of dependencies
            jira_hist_query = delete(JiraSyncHistory).where(JiraSyncHistory.project_id == project_id)
            await session.execute(jira_hist_query)
            await session.commit()
            
            jira_req_query = delete(JiraRequirementMapping).where(JiraRequirementMapping.project_id == project_id)
            await session.execute(jira_req_query)
            await session.commit()
            
            jira_test_query = delete(JiraTestMapping).where(JiraTestMapping.project_id == project_id)
            await session.execute(jira_test_query)
            await session.commit()
            
            jira_conn_query = delete(JiraConnection).where(JiraConnection.project_id == project_id)
            await session.execute(jira_conn_query)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Warning: Failed to delete Jira addon data: {e}")
        
        # Step 3: Delete acceptance criteria
        try:
            from app.models.db_models import AcceptanceCriteria
            ac_query = delete(AcceptanceCriteria).where(AcceptanceCriteria.project_id == project_id)
            await session.execute(ac_query)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Warning: Error deleting acceptance criteria: {e}")
        
        # Step 4: Delete test cases
        try:
            from app.models.db_models import TestCase
            test_query = delete(TestCase).where(TestCase.project_id == project_id)
            await session.execute(test_query)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Warning: Error deleting test cases: {e}")
        
        # Step 5: Delete requirements
        try:
            from app.models.db_models import Requirement
            req_query = delete(Requirement).where(Requirement.project_id == project_id)
            await session.execute(req_query)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Warning: Error deleting requirements: {e}")
        
        # Step 6: Delete documents
        try:
            doc_delete_query = delete(Document).where(Document.project_id == project_id)
            await session.execute(doc_delete_query)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Warning: Error deleting documents: {e}")
        
        # Step 7: Delete the project itself
        try:
            await session.delete(project)
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting project record: {str(e)}")
        
        return {
            "status": "success",
            "message": f"Project '{project_name}' and all associated data deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        try:
            await session.rollback()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")


# ============================================================================
# Document Upload
# ============================================================================

async def process_document_chunks(
    doc_id: str,
    file_path: str,
    doc_type: str,
    project_id: str,
    session: AsyncSession,
):
    """Background task to chunk and index document."""
    try:
        # Parse document
        parser = DocumentParser()
        texts = parser.parse(file_path, doc_type)

        # Chunk document
        chunker = DocumentChunker()
        chunks = chunker.chunk(
            texts,
            {
                "doc_id": doc_id,
                "doc_type": doc_type,
                "filename": Path(file_path).name,
                "project_id": project_id,
            },
        )

        # Add to ChromaDB
        chroma = ChromaService()
        chunk_count = chroma.add_chunks(chunks, doc_id)

        # Update document status
        doc = await session.get(Document, UUID(doc_id))
        if doc:
            doc.chunk_count = chunk_count
            doc.status = DocumentStatusEnum.INDEXED
            await session.commit()

    except Exception as e:
        # Update document with error status
        try:
            doc = await session.get(Document, UUID(doc_id))
            if doc:
                doc.status = DocumentStatusEnum.FAILED
                await session.commit()
        except:
            pass


@router.post("/projects/{project_id}/upload", response_model=DocumentResponse)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    session: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """
    Upload and process a document.

    Args:
        project_id: Project UUID
        file: Uploaded file
        background_tasks: FastAPI background tasks
        session: Database session

    Returns:
        Document details
    """
    try:
        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate file size (max 20MB)
        contents = await file.read()
        file_size = len(contents)
        if file_size > 20 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 20MB)")

        # Determine document type from filename
        filename = file.filename or "unknown"
        ext = Path(filename).suffix.lower()

        doc_type_map = {
            ".pdf": "brd",
            ".docx": "user_story",
            ".doc": "user_story",
            ".txt": "nfr",
        }
        doc_type = doc_type_map.get(ext, "other")

        # Create uploads directory
        uploads_dir = Path("/app/uploads") / str(project_id)
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        doc_id = str(uuid4())
        file_path = uploads_dir / f"{doc_id}_{filename}"
        with open(file_path, "wb") as f:
            f.write(contents)

        # Create document record
        document = Document(
            project_id=project_id,
            filename=filename,
            doc_type=DocumentTypeEnum(doc_type),
            file_path=str(file_path),
            status=DocumentStatusEnum.UPLOADED,
        )
        session.add(document)
        await session.flush()

        # Queue background chunking task
        background_tasks.add_task(
            process_document_chunks,
            str(document.id),
            str(file_path),
            doc_type,
            str(project_id),
            session,
        )

        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            doc_type=document.doc_type.value,
            status=document.status.value,
            chunk_count=0,
            uploaded_at=document.uploaded_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error uploading document: {str(e)}")


@router.get("/projects/{project_id}/documents")
async def list_documents(
    project_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[DocumentResponse]:
    """
    List documents for a project.

    Args:
        project_id: Project UUID
        session: Database session

    Returns:
        List of documents
    """
    try:
        from sqlalchemy import select

        # Verify project exists
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get documents
        query = select(Document).where(Document.project_id == project_id)
        result = await session.execute(query)
        documents = result.scalars().all()

        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                doc_type=doc.doc_type.value,
                status=doc.status.value,
                chunk_count=doc.chunk_count,
                uploaded_at=doc.uploaded_at.isoformat(),
            )
            for doc in documents
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error listing documents: {str(e)}")
