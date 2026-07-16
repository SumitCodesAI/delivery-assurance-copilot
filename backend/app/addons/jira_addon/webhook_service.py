"""Service to handle Jira webhook events and sync back to Copilot."""

import logging
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import Requirement
from .models import JiraRequirementMapping, JiraSyncHistory

logger = logging.getLogger(__name__)


class WebhookService:
    """Handle incoming Jira webhooks and update Copilot data."""
    
    def __init__(self, session: AsyncSession):
        """Initialize webhook service with database session."""
        self.session = session
    
    async def process_webhook(self, payload: dict) -> dict:
        """
        Process Jira webhook payload.
        
        Args:
            payload: Webhook payload from Jira
        
        Returns:
            dict with processing results
        """
        try:
            # Extract event type
            event_type = payload.get("webhookEvent", "unknown")
            logger.info(f"Processing Jira webhook event: {event_type}")
            
            # Handle different event types
            if event_type == "jira:issue_updated":
                return await self._handle_issue_updated(payload)
            elif event_type == "jira:issue_created":
                return await self._handle_issue_created(payload)
            else:
                logger.warning(f"Unknown webhook event: {event_type}")
                return {
                    "message": f"Unknown event type: {event_type}",
                    "updates": 0
                }
        
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise
    
    async def _handle_issue_updated(self, payload: dict) -> dict:
        """
        Handle issue updated event.
        
        Extract:
        - Status changes
        - Assignee changes
        - Priority changes
        """
        try:
            issue_data = payload.get("issue", {})
            issue_key = issue_data.get("key")
            fields = issue_data.get("fields", {})
            
            # Extract current state
            status = fields.get("status", {}).get("name", "Unknown")
            priority = fields.get("priority", {}).get("name", "Unknown")
            assignee = fields.get("assignee", {})
            assignee_name = assignee.get("displayName") if assignee else None
            
            logger.info(f"Issue {issue_key} updated: status={status}, priority={priority}")
            
            # Find corresponding requirement mapping
            mapping = await self._get_mapping_by_jira_key(issue_key)
            if not mapping:
                logger.warning(f"No mapping found for Jira issue {issue_key}")
                return {
                    "message": f"No mapping found for {issue_key}",
                    "updates": 0
                }
            
            # Update requirement in Copilot
            requirement = await self.session.get(Requirement, mapping.requirement_id)
            if not requirement:
                logger.warning(f"Requirement {mapping.requirement_id} not found")
                return {
                    "message": f"Requirement not found",
                    "updates": 0
                }
            
            # Update fields based on what changed
            old_status = requirement.status
            requirement.status = self._normalize_status(status)
            requirement.priority = priority
            if assignee_name:
                requirement.assigned_to = assignee_name
            requirement.last_synced_with_jira = datetime.utcnow()
            
            await self.session.commit()
            
            # Log the sync
            await self._log_webhook_event(
                mapping.project_id,
                issue_key,
                f"Status: {old_status} → {status}",
                "pull"
            )
            
            logger.info(f"Updated requirement {mapping.requirement_id} from webhook")
            return {
                "message": f"Updated requirement from {issue_key}",
                "updates": 1
            }
        
        except Exception as e:
            logger.error(f"Error handling issue updated: {e}")
            raise
    
    async def _handle_issue_created(self, payload: dict) -> dict:
        """Handle issue created event."""
        # Not typically needed as we create issues, but useful if Jira is primary
        logger.info("Issue created webhook received (not implemented)")
        return {
            "message": "Issue created event received",
            "updates": 0
        }
    
    async def _get_mapping_by_jira_key(self, jira_issue_key: str) -> JiraRequirementMapping:
        """Get requirement mapping by Jira issue key."""
        query = select(JiraRequirementMapping).where(
            JiraRequirementMapping.jira_issue_key == jira_issue_key
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _log_webhook_event(
        self,
        project_id: UUID,
        issue_key: str,
        description: str,
        sync_direction: str = "pull"
    ):
        """Log webhook event for audit trail."""
        try:
            event = JiraSyncHistory(
                project_id=project_id,
                sync_type="bidirectional",
                direction="from_jira",
                status="success",
                items_processed=1,
                items_failed=0,
                error_message=None
            )
            self.session.add(event)
            await self.session.commit()
            logger.info(f"Logged webhook event: {issue_key} → {description}")
        except Exception as e:
            logger.error(f"Error logging webhook event: {e}")
    
    @staticmethod
    def _normalize_status(jira_status: str) -> str:
        """
        Normalize Jira status to Copilot status.
        
        Mapping:
        - Open, To Do → pending
        - In Progress → in_progress
        - In Review, Review → review
        - Done, Closed → completed
        """
        status_lower = jira_status.lower()
        
        if status_lower in ["open", "to do", "backlog"]:
            return "pending"
        elif status_lower in ["in progress", "started"]:
            return "in_progress"
        elif status_lower in ["in review", "review", "under review"]:
            return "review"
        elif status_lower in ["done", "closed", "resolved"]:
            return "completed"
        else:
            return status_lower
