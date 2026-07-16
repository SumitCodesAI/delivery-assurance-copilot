"""Jira addon configuration models."""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class JiraConfig(BaseModel):
    """Jira connection configuration."""
    
    jira_url: str = Field(
        ..., 
        description="Jira instance URL (e.g., https://mycompany.atlassian.net)"
    )
    jira_project_key: str = Field(
        ..., 
        description="Project key (e.g., 'QUAL')"
    )
    jira_username: str = Field(
        ..., 
        description="Jira email/username"
    )
    jira_api_token: str = Field(
        ..., 
        description="Jira API token (will be encrypted)"
    )
    sync_direction: Literal['push', 'pull', 'bidirectional'] = Field(
        default='bidirectional',
        description="Sync direction: push only, pull only, or both"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "jira_url": "https://mycompany.atlassian.net",
                "jira_project_key": "QUAL",
                "jira_username": "qa@company.com",
                "jira_api_token": "atatt1234567890",
                "sync_direction": "bidirectional"
            }
        }


class JiraSyncRequest(BaseModel):
    """Request to sync with Jira."""
    
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
        description="Include acceptance criteria in sync"
    )
    create_epic: bool = Field(
        default=True,
        description="Create parent epic for organization"
    )
    epic_title: Optional[str] = Field(
        default=None,
        description="Custom epic title (auto-generated if not provided)"
    )
    auto_link: bool = Field(
        default=True,
        description="Auto-link related issues"
    )
    sync_direction: Literal['push', 'pull', 'bidirectional'] = Field(
        default='bidirectional',
        description="Sync direction for this operation"
    )


class JiraConfigResponse(BaseModel):
    """Response after Jira configuration."""
    
    status: str
    jira_project: str
    message: str
