"""Request/response schemas for Jira addon."""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class JiraConnectionRequest(BaseModel):
    """Request to configure Jira connection.
    
    Note: jira_username and jira_api_token are read from environment variables
    (JIRA_USERNAME and JIRA_API_TOKEN in .env) for security.
    """
    
    jira_url: str = Field(
        ..., 
        description="Jira instance URL (e.g., https://mycompany.atlassian.net)"
    )
    jira_project_key: str = Field(
        ..., 
        description="Jira project key (e.g., QUAL, TEST)"
    )
    sync_direction: Literal['push', 'pull', 'bidirectional'] = Field(
        default='bidirectional',
        description="Sync direction: push, pull, or bidirectional"
    )


class JiraConnectionResponse(BaseModel):
    """Response after Jira connection setup."""
    
    status: str
    message: str
    jira_project_key: str
    is_active: Optional[bool] = None


class JiraSyncRequest(BaseModel):
    """Request to perform sync."""
    
    include_requirements: bool = Field(
        default=True,
        description="Include requirements in sync"
    )
    include_test_cases: bool = Field(
        default=True,
        description="Include test cases in sync"
    )
    include_criteria: bool = Field(
        default=True,
        description="Include acceptance criteria"
    )
    create_epic: bool = Field(
        default=True,
        description="Create parent epic"
    )
    epic_title: Optional[str] = Field(
        default=None,
        description="Custom epic title"
    )
    auto_link: bool = Field(
        default=True,
        description="Auto-link related issues"
    )


class JiraSyncResponse(BaseModel):
    """Response from sync operation."""
    
    status: str
    message: str
    epic_key: Optional[str] = None
    items_synced: Optional[int] = None
    items_failed: Optional[int] = None


class JiraConnectionStatus(BaseModel):
    """Current Jira connection status."""
    
    is_configured: bool
    is_active: bool
    jira_url: Optional[str] = None
    jira_project_key: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    sync_direction: Optional[str] = None


class JiraSyncHistory(BaseModel):
    """Sync history entry."""
    
    id: str
    project_id: str
    sync_type: str
    direction: Optional[str]
    status: str
    items_processed: int
    items_failed: int
    error_message: Optional[str]
    synced_at: datetime


class JiraIssueLink(BaseModel):
    """Link between local artifact and Jira issue."""
    
    artifact_id: str
    artifact_type: Literal['requirement', 'test_case', 'criteria']
    jira_issue_key: str
    jira_issue_id: Optional[str] = None
    sync_status: str
    last_synced_at: Optional[datetime] = None
