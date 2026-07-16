"""
SQLAlchemy async ORM models for the delivery assurance copilot.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, DateTime, UUID, ForeignKey, Enum, Boolean,
    Integer, JSON, ARRAY, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ProjectStatusEnum(str, PyEnum):
    """Enum for project status."""
    ACTIVE = "active"
    ARCHIVED = "archived"


class DocumentTypeEnum(str, PyEnum):
    """Enum for document types."""
    BRD = "brd"
    USER_STORY = "user_story"
    API_SPEC = "api_spec"
    NFR = "nfr"
    QA_POLICY = "qa_policy"
    OTHER = "other"


class DocumentStatusEnum(str, PyEnum):
    """Enum for document processing status."""
    UPLOADED = "uploaded"
    CHUNKED = "chunked"
    INDEXED = "indexed"
    FAILED = "failed"


class RequirementPriorityEnum(str, PyEnum):
    """Enum for requirement priority."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CoverageStatusEnum(str, PyEnum):
    """Enum for test coverage status."""
    COVERED = "covered"
    GAP = "gap"
    PARTIAL = "partial"


class ReviewStatusEnum(str, PyEnum):
    """Enum for review status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class Project(Base):
    """Project entity."""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(ProjectStatusEnum), default=ProjectStatusEnum.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    traceability_matrices = relationship("TraceabilityMatrix", back_populates="project", cascade="all, delete-orphan")
    review_sessions = relationship("ReviewSession", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"


class Document(Base):
    """Document entity for uploaded files."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    doc_type = Column(Enum(DocumentTypeEnum), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    chunk_count = Column(Integer, default=0)
    status = Column(Enum(DocumentStatusEnum), default=DocumentStatusEnum.UPLOADED, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="documents")
    requirements = relationship("Requirement", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class Requirement(Base):
    """Requirement entity extracted from documents."""
    __tablename__ = "requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    req_id = Column(String(50), nullable=False, index=True)  # e.g., REQ-001
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(Enum(RequirementPriorityEnum), default=RequirementPriorityEnum.MEDIUM, nullable=False)
    ambiguity_flag = Column(Boolean, default=False, nullable=False)
    ambiguity_notes = Column(Text, nullable=True)
    source_chunk_ids = Column(ARRAY(String), default=list, nullable=False)
    assigned_to = Column(String(255), nullable=True)  # Assigned person/team
    last_synced_with_jira = Column(DateTime(timezone=True), nullable=True)  # When last pulled from Jira
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="requirements")
    document = relationship("Document", back_populates="requirements")
    acceptance_criteria = relationship("AcceptanceCriterion", back_populates="requirement", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="requirement", cascade="all, delete-orphan")
    traceability_matrices = relationship("TraceabilityMatrix", back_populates="requirement", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Requirement(id={self.id}, req_id={self.req_id}, title={self.title})>"


class AcceptanceCriterion(Base):
    """Acceptance criteria for requirements."""
    __tablename__ = "acceptance_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False, index=True)
    criterion_text = Column(Text, nullable=False)
    source_citation = Column(JSON, nullable=True)  # {doc_name, chunk_id, excerpt}
    reviewer_status = Column(Enum(ReviewStatusEnum), default=ReviewStatusEnum.PENDING, nullable=False)
    reviewer_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    requirement = relationship("Requirement", back_populates="acceptance_criteria")

    def __repr__(self) -> str:
        return f"<AcceptanceCriterion(id={self.id}, requirement_id={self.requirement_id})>"


class User(Base):
    """User entity for authentication."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=False, unique=True, index=True)
    encrypted_password = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class TestCase(Base):
    """Test cases generated for requirements."""
    __tablename__ = "test_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    preconditions = Column(Text, nullable=False)
    steps = Column(JSON, nullable=False)  # Array of {step_number, action, expected_outcome}
    expected_result = Column(Text, nullable=False)
    priority = Column(Enum(RequirementPriorityEnum), default=RequirementPriorityEnum.MEDIUM, nullable=False)
    reviewer_status = Column(Enum(ReviewStatusEnum), default=ReviewStatusEnum.PENDING, nullable=False)
    reviewer_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    requirement = relationship("Requirement", back_populates="test_cases")
    traceability_matrices = relationship("TraceabilityMatrix", back_populates="test_case", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TestCase(id={self.id}, requirement_id={self.requirement_id}, title={self.title})>"


class TraceabilityMatrix(Base):
    """Traceability matrix linking requirements to test cases."""
    __tablename__ = "traceability_matrices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False, index=True)
    test_case_id = Column(UUID(as_uuid=True), ForeignKey("test_cases.id"), nullable=True, index=True)
    coverage_status = Column(Enum(CoverageStatusEnum), nullable=False, index=True)
    gap_reason = Column(Text, nullable=True)
    export_timestamp = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="traceability_matrices")
    requirement = relationship("Requirement", back_populates="traceability_matrices")
    test_case = relationship("TestCase", back_populates="traceability_matrices")

    def __repr__(self) -> str:
        return f"<TraceabilityMatrix(id={self.id}, requirement_id={self.requirement_id}, coverage_status={self.coverage_status})>"


class ReviewSession(Base):
    """Review session tracking human approvals."""
    __tablename__ = "review_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    reviewer_name = Column(String(255), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    approved_count = Column(Integer, default=0, nullable=False)
    rejected_count = Column(Integer, default=0, nullable=False)
    edited_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="review_sessions")

    def __repr__(self) -> str:
        return f"<ReviewSession(id={self.id}, reviewer_name={self.reviewer_name}, project_id={self.project_id})>"
