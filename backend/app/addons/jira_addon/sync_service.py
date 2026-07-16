"""Jira sync service for bidirectional synchronization."""

import logging
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join

from app.models.db_models import (
    Project, 
    Requirement, 
    TestCase, 
    AcceptanceCriterion
)
from .client import JiraClient
from .models import (
    JiraConnection,
    JiraRequirementMapping,
    JiraTestMapping,
    JiraSyncHistory
)
from .encryption import decrypt_token

logger = logging.getLogger(__name__)


class JiraSyncService:
    """Service for syncing with Jira."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize sync service."""
        self.db_session = db_session
        self.jira_client: Optional[JiraClient] = None
    
    async def get_connection(self, project_id: str) -> Optional[JiraConnection]:
        """Get Jira connection for project."""
        result = await self.db_session.execute(
            select(JiraConnection).where(JiraConnection.project_id == uuid.UUID(project_id))
        )
        return result.scalar_one_or_none()
    
    async def save_connection(
        self,
        project_id: str,
        jira_url: str,
        jira_project_key: str,
        jira_username: str,
        jira_api_token: str,
        sync_direction: str = 'bidirectional'
    ) -> JiraConnection:
        """Save Jira connection configuration."""
        from .encryption import encrypt_token
        
        # Encrypt token before storing
        encrypted_token = encrypt_token(jira_api_token)
        
        # Check if connection exists
        connection = await self.get_connection(project_id)
        
        if connection:
            connection.jira_url = jira_url
            connection.jira_project_key = jira_project_key
            connection.jira_username = jira_username
            connection.jira_api_token_encrypted = encrypted_token
            connection.sync_direction = sync_direction
        else:
            connection = JiraConnection(
                project_id=uuid.UUID(project_id),
                jira_url=jira_url,
                jira_project_key=jira_project_key,
                jira_username=jira_username,
                jira_api_token_encrypted=encrypted_token,
                sync_direction=sync_direction,
                is_active=False
            )
            self.db_session.add(connection)
        
        await self.db_session.commit()
        return connection
    
    async def validate_and_activate_connection(self, project_id: str) -> Tuple[bool, str]:
        """Test Jira connection and activate if valid."""
        connection = await self.get_connection(project_id)
        
        if not connection:
            return False, "No Jira connection configured"
        
        try:
            # Decrypt token
            decrypted_token = decrypt_token(connection.jira_api_token_encrypted)
            
            # Initialize client
            self.jira_client = JiraClient(
                url=connection.jira_url,
                username=connection.jira_username,
                api_token=decrypted_token
            )
            
            # Test connection
            if self.jira_client.validate_connection():
                connection.is_active = True
                connection.last_sync_at = datetime.utcnow()
                await self.db_session.commit()
                return True, "Jira connection validated and activated"
            else:
                return False, "Failed to validate Jira connection"
        
        except Exception as e:
            logger.error(f"Connection validation error: {e}")
            return False, f"Connection error: {str(e)}"
    
    async def sync_to_jira(
        self,
        project_id: str,
        include_requirements: bool = True,
        include_test_cases: bool = True,
        create_epic: bool = True,
        epic_title: Optional[str] = None,
        auto_link: bool = True
    ) -> Dict:
        """
        Sync requirements and test cases to Jira.
        
        Returns:
            Dict with sync results
        """
        connection = await self.get_connection(project_id)
        if not connection or not connection.is_active:
            return {'status': 'failed', 'message': 'No active Jira connection'}
        
        # Initialize client if needed
        if not self.jira_client:
            decrypted_token = decrypt_token(connection.jira_api_token_encrypted)
            self.jira_client = JiraClient(
                url=connection.jira_url,
                username=connection.jira_username,
                api_token=decrypted_token
            )
        
        try:
            items_processed = 0
            items_failed = 0
            epic_key = None
            
            # Create epic if requested
            if create_epic:
                epic_title = epic_title or f"Test Plan - {datetime.now().strftime('%Y-%m-%d')}"
                try:
                    epic_key = self.jira_client.create_epic(
                        connection.jira_project_key,
                        epic_title,
                        "Auto-generated test planning epic"
                    )
                    logger.info(f"Created epic {epic_key}")
                except Exception as e:
                    logger.error(f"Failed to create epic: {e}")
            
            # Sync requirements
            if include_requirements:
                processed, failed = await self._sync_requirements_to_jira(
                    project_id,
                    connection.jira_project_key,
                    epic_key
                )
                items_processed += processed
                items_failed += failed
            
            # Sync test cases
            if include_test_cases:
                processed, failed = await self._sync_test_cases_to_jira(
                    project_id,
                    connection.jira_project_key,
                    epic_key
                )
                items_processed += processed
                items_failed += failed
            
            # Log sync history
            await self._log_sync_history(
                project_id,
                'push',
                'to_jira',
                'success' if items_failed == 0 else 'partial',
                items_processed,
                items_failed
            )
            
            return {
                'status': 'success',
                'epic_key': epic_key,
                'items_synced': items_processed,
                'items_failed': items_failed,
                'message': f"Synced {items_processed} items to Jira"
            }
        
        except Exception as e:
            logger.error(f"Sync to Jira failed: {e}")
            await self._log_sync_history(
                project_id,
                'push',
                'to_jira',
                'failed',
                0,
                0,
                str(e)
            )
            return {
                'status': 'failed',
                'message': f"Sync failed: {str(e)}"
            }
    
    async def _sync_requirements_to_jira(
        self,
        project_id: str,
        jira_project_key: str,
        epic_key: Optional[str] = None
    ) -> Tuple[int, int]:
        """Sync requirements to Jira."""
        processed = 0
        failed = 0
        
        # Get all requirements
        result = await self.db_session.execute(
            select(Requirement).where(Requirement.project_id == uuid.UUID(project_id))
        )
        requirements = result.scalars().all()
        
        for req in requirements:
            try:
                # Check if already mapped
                existing = await self.db_session.execute(
                    select(JiraRequirementMapping).where(
                        JiraRequirementMapping.requirement_id == req.id
                    )
                )
                existing_map = existing.scalar_one_or_none()
                
                if existing_map:
                    logger.info(f"Requirement {req.id} already mapped to {existing_map.jira_issue_key}")
                    processed += 1
                    continue
                
                # Create Jira issue
                issue_key = self.jira_client.create_requirement_issue(
                    jira_project_key,
                    {
                        'req_id': req.req_id,
                        'title': req.title,
                        'description': req.description,
                        'priority': req.priority or 'medium'
                    },
                    parent_epic_key=epic_key
                )
                
                # Save mapping
                mapping = JiraRequirementMapping(
                    requirement_id=req.id,
                    jira_issue_key=issue_key,
                    sync_status='synced',
                    last_synced_at=datetime.utcnow()
                )
                self.db_session.add(mapping)
                
                processed += 1
            
            except Exception as e:
                logger.error(f"Failed to sync requirement {req.id}: {e}")
                failed += 1
        
        await self.db_session.commit()
        return processed, failed
    
    async def _sync_test_cases_to_jira(
        self,
        project_id: str,
        jira_project_key: str,
        epic_key: Optional[str] = None
    ) -> Tuple[int, int]:
        """Sync test cases to Jira."""
        processed = 0
        failed = 0
        
        # Get all test cases for this project (through requirement)
        result = await self.db_session.execute(
            select(TestCase).join(Requirement).where(Requirement.project_id == uuid.UUID(project_id))
        )
        test_cases = result.scalars().all()
        
        for test in test_cases:
            try:
                # Check if already mapped
                existing = await self.db_session.execute(
                    select(JiraTestMapping).where(
                        JiraTestMapping.test_case_id == test.id
                    )
                )
                existing_map = existing.scalar_one_or_none()
                
                if existing_map:
                    logger.info(f"Test case {test.id} already mapped to {existing_map.jira_issue_key}")
                    processed += 1
                    continue
                
                # Get parent requirement for linking
                requirement = await self.db_session.get(Requirement, test.requirement_id)
                requirement_issue_key = None
                
                if requirement:
                    req_mapping = await self.db_session.execute(
                        select(JiraRequirementMapping).where(
                            JiraRequirementMapping.requirement_id == test.requirement_id
                        )
                    )
                    req_map = req_mapping.scalar_one_or_none()
                    if req_map:
                        requirement_issue_key = req_map.jira_issue_key
                
                # Create Jira issue
                issue_key = self.jira_client.create_test_issue(
                    jira_project_key,
                    {
                        'id': str(test.id),
                        'title': test.title,
                        'preconditions': test.preconditions or '',
                        'steps': test.steps or [],
                        'expected_result': test.expected_result or '',
                        'priority': test.priority or 'medium'
                    },
                    parent_issue_key=epic_key,
                    requirement_key=requirement_issue_key
                )
                
                # Save mapping
                mapping = JiraTestMapping(
                    test_case_id=test.id,
                    jira_issue_key=issue_key,
                    sync_status='synced',
                    last_synced_at=datetime.utcnow()
                )
                self.db_session.add(mapping)
                
                processed += 1
            
            except Exception as e:
                logger.error(f"Failed to sync test case {test.id}: {e}")
                failed += 1
        
        await self.db_session.commit()
        return processed, failed
    
    async def _log_sync_history(
        self,
        project_id: str,
        sync_type: str,
        direction: str,
        status: str,
        items_processed: int,
        items_failed: int,
        error_message: Optional[str] = None
    ):
        """Log sync operation to history."""
        history = JiraSyncHistory(
            project_id=uuid.UUID(project_id),
            sync_type=sync_type,
            direction=direction,
            status=status,
            items_processed=items_processed,
            items_failed=items_failed,
            error_message=error_message
        )
        self.db_session.add(history)
        await self.db_session.commit()
