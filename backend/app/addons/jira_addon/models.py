"""Database models for Jira addon."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, UUID, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class JiraConnection(Base):
    """Track Jira connections per project."""
    
    __tablename__ = "jira_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True)  # References projects.id (app-level FK)
    jira_url = Column(String(255), nullable=False)
    jira_project_key = Column(String(50), nullable=False)
    jira_username = Column(String(255), nullable=False)
    jira_api_token_encrypted = Column(Text, nullable=False)  # Encrypted
    is_active = Column(Boolean, default=False, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_direction = Column(String(20), default='bidirectional', nullable=False)  # 'push', 'pull', 'bidirectional'
    created_at = Column(DateTime(timezone=True), server_default=__import__('sqlalchemy').func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=__import__('sqlalchemy').func.now(), onupdate=__import__('sqlalchemy').func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<JiraConnection(id={self.id}, project_id={self.project_id}, jira_project={self.jira_project_key})>"


class JiraRequirementMapping(Base):
    """Map requirements to Jira issues."""
    
    __tablename__ = "jira_requirement_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References requirements.id (app-level FK)
    jira_issue_key = Column(String(50), nullable=False)  # e.g., "QUAL-101"
    jira_issue_id = Column(String(100), nullable=True)
    sync_status = Column(String(50), default='synced', nullable=False)  # 'synced', 'pending', 'failed'
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=__import__('sqlalchemy').func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=__import__('sqlalchemy').func.now(), onupdate=__import__('sqlalchemy').func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<JiraRequirementMapping(requirement_id={self.requirement_id}, jira_key={self.jira_issue_key})>"


class JiraTestMapping(Base):
    """Map test cases to Jira issues."""
    
    __tablename__ = "jira_test_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_case_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References test_cases.id (app-level FK)
    jira_issue_key = Column(String(50), nullable=False)
    jira_issue_id = Column(String(100), nullable=True)
    sync_status = Column(String(50), default='synced', nullable=False)  # 'synced', 'pending', 'failed'
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=__import__('sqlalchemy').func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=__import__('sqlalchemy').func.now(), onupdate=__import__('sqlalchemy').func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<JiraTestMapping(test_case_id={self.test_case_id}, jira_key={self.jira_issue_key})>"


class JiraSyncHistory(Base):
    """Track sync history for auditing."""
    
    __tablename__ = "jira_sync_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References projects.id (app-level FK)
    sync_type = Column(String(50), nullable=False)  # 'push', 'pull', 'bidirectional'
    direction = Column(String(50), nullable=True)  # 'to_jira', 'from_jira'
    status = Column(String(50), nullable=False)  # 'success', 'partial', 'failed'
    items_processed = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    synced_at = Column(DateTime(timezone=True), server_default=__import__('sqlalchemy').func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<JiraSyncHistory(project_id={self.project_id}, status={self.status}, synced_at={self.synced_at})>"
