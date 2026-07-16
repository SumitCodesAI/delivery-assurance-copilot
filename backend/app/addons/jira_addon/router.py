"""API router for Jira addon."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.config import get_settings
from .config import JiraConfig, JiraSyncRequest, JiraConfigResponse
from .schemas import (
    JiraConnectionRequest,
    JiraConnectionResponse,
    JiraSyncResponse,
    JiraConnectionStatus
)
from .sync_service import JiraSyncService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/jira",
    tags=["jira"],
    responses={404: {"description": "Not found"}},
)


@router.post("/configure", response_model=JiraConnectionResponse)
async def configure_jira(
    project_id: str,
    config: JiraConnectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Configure Jira connection for a project.
    
    - **project_id**: Project UUID
    - **config**: Jira connection details (URL and project key)
    - Note: Username and API token are read from environment variables for security
    """
    try:
        settings = get_settings()
        
        # Get credentials from environment
        jira_username = settings.jira_username
        jira_api_token = settings.jira_api_token
        
        if not jira_username or not jira_api_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jira credentials not configured in environment. Please set JIRA_USERNAME and JIRA_API_TOKEN in .env"
            )
        
        sync_service = JiraSyncService(db)
        
        connection = await sync_service.save_connection(
            project_id=project_id,
            jira_url=config.jira_url,
            jira_project_key=config.jira_project_key,
            jira_username=jira_username,
            jira_api_token=jira_api_token,
            sync_direction=config.sync_direction
        )
        
        return JiraConnectionResponse(
            status="configured",
            message="Jira connection saved (credentials from environment)",
            jira_project_key=connection.jira_project_key
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure Jira: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration failed: {str(e)}"
        )


@router.post("/validate", response_model=JiraConnectionResponse)
async def validate_jira(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate and activate Jira connection.
    
    - **project_id**: Project UUID
    """
    try:
        sync_service = JiraSyncService(db)
        is_valid, message = await sync_service.validate_and_activate_connection(project_id)
        
        if is_valid:
            connection = await sync_service.get_connection(project_id)
            return JiraConnectionResponse(
                status="active",
                message=message,
                jira_project_key=connection.jira_project_key,
                is_active=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/status/{project_id}", response_model=JiraConnectionStatus)
async def get_connection_status(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get current Jira connection status."""
    try:
        sync_service = JiraSyncService(db)
        connection = await sync_service.get_connection(project_id)
        
        if not connection:
            return JiraConnectionStatus(
                is_configured=False,
                is_active=False
            )
        
        return JiraConnectionStatus(
            is_configured=True,
            is_active=connection.is_active,
            jira_url=connection.jira_url,
            jira_project_key=connection.jira_project_key,
            last_sync_at=connection.last_sync_at,
            sync_direction=connection.sync_direction
        )
    
    except Exception as e:
        logger.error(f"Failed to get connection status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sync/{project_id}", response_model=JiraSyncResponse)
async def sync_with_jira(
    project_id: str,
    sync_request: JiraSyncRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sync requirements and test cases with Jira.
    
    - **project_id**: Project UUID
    - **sync_request**: Sync configuration
    """
    try:
        sync_service = JiraSyncService(db)
        
        # Perform sync
        result = await sync_service.sync_to_jira(
            project_id=project_id,
            include_requirements=sync_request.include_requirements,
            include_test_cases=sync_request.include_test_cases,
            create_epic=sync_request.create_epic,
            epic_title=sync_request.epic_title,
            auto_link=sync_request.auto_link
        )
        
        if result['status'] == 'failed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
        
        return JiraSyncResponse(
            status=result['status'],
            message=result['message'],
            epic_key=result.get('epic_key'),
            items_synced=result.get('items_synced'),
            items_failed=result.get('items_failed')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.delete("/disconnect/{project_id}", response_model=dict)
async def disconnect_jira(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Disconnect Jira from project."""
    try:
        from sqlalchemy import delete, select
        from .models import JiraConnection
        import uuid
        
        # Delete connection
        await db.execute(
            delete(JiraConnection).where(
                JiraConnection.project_id == uuid.UUID(project_id)
            )
        )
        await db.commit()
        
        return {
            'status': 'disconnected',
            'message': 'Jira connection removed'
        }
    
    except Exception as e:
        logger.error(f"Failed to disconnect Jira: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/webhooks/event")
async def receive_jira_webhook(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Receive webhook events from Jira.
    
    This endpoint is called by Jira when:
    - An issue status changes
    - An issue is assigned/reassigned
    - Issue priority changes
    - Comments are added
    
    Webhook should be configured in Jira to POST to:
    {server_url}/api/v1/jira/webhooks/event
    
    Events to listen for:
    - jira:issue_updated
    - jira:issue_created
    """
    try:
        from .webhook_service import WebhookService
        
        webhook_service = WebhookService(db)
        result = await webhook_service.process_webhook(payload)
        
        logger.info(f"Webhook processed: {result}")
        
        return {
            "status": "received",
            "message": result.get("message", "Webhook processed successfully"),
            "updates": result.get("updates", 0)
        }
    
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        # Return 200 OK even on error so Jira doesn't keep retrying
        return {
            "status": "error",
            "message": str(e),
            "updates": 0
        }


@router.get("/webhook-history/{project_id}")
async def get_webhook_history(
    project_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent webhook events for a project."""
    try:
        from sqlalchemy import select, desc
        from .models import JiraSyncHistory
        import uuid
        
        # Get recent webhook events
        query = select(JiraSyncHistory).where(
            (JiraSyncHistory.project_id == uuid.UUID(project_id)) &
            (JiraSyncHistory.direction == "from_jira")
        ).order_by(desc(JiraSyncHistory.synced_at)).limit(limit)
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        return {
            "events": [
                {
                    "id": str(event.id),
                    "timestamp": event.synced_at.isoformat() if event.synced_at else None,
                    "status": event.status,
                    "items_processed": event.items_processed,
                    "items_failed": event.items_failed,
                    "error": event.error_message
                }
                for event in events
            ],
            "total": len(events)
        }
    
    except Exception as e:
        logger.error(f"Failed to get webhook history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
