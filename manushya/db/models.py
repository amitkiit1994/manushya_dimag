"""
Database models for Manushya.ai
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, DateTime, Text, Boolean, Integer, Float, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .database import Base


class Identity(Base):
    """Identity model for agents and users."""
    
    __tablename__ = "identities"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    claims: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    memories: Mapped[List["Memory"]] = relationship("Memory", back_populates="identity")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="actor_identity")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_identities_external_id"),
        Index("idx_identities_role_active", "role", "is_active"),
    )
    
    def __repr__(self):
        return f"<Identity(id={self.id}, external_id='{self.external_id}', role='{self.role}')>"


class Memory(Base):
    """Memory model for storing agent memories with vector embeddings."""
    
    __tablename__ = "memories"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    identity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    vector: Mapped[List[float]] = mapped_column(ARRAY(Float), nullable=True)  # pgvector
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    ttl_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    identity: Mapped["Identity"] = relationship("Identity", back_populates="memories")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="memory")
    
    # Constraints
    __table_args__ = (
        Index("idx_memories_identity_type", "identity_id", "type"),
        Index("idx_memories_created_at", "created_at"),
        Index("idx_memories_deleted_at", "deleted_at"),
        CheckConstraint("score >= 0 AND score <= 1", name="ck_memories_score_range"),
    )
    
    @property
    def expires_at(self) -> Optional[datetime]:
        """Calculate expiration date based on TTL."""
        if self.ttl_days:
            return self.created_at + timedelta(days=self.ttl_days)
        return None
    
    @property
    def is_expired(self) -> bool:
        """Check if memory is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def __repr__(self):
        return f"<Memory(id={self.id}, identity_id={self.identity_id}, type='{self.type}')>"


class Policy(Base):
    """Policy model for role-based access control."""
    
    __tablename__ = "policies"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rule: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Constraints
    __table_args__ = (
        Index("idx_policies_role_active", "role", "is_active"),
        Index("idx_policies_priority", "priority"),
    )
    
    def __repr__(self):
        return f"<Policy(id={self.id}, role='{self.role}', priority={self.priority})>"


class AuditLog(Base):
    """Audit log model for compliance and tracking."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    memory_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("memories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("identities.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    before_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    meta_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    memory: Mapped[Optional["Memory"]] = relationship("Memory", back_populates="audit_logs")
    actor_identity: Mapped[Optional["Identity"]] = relationship("Identity", back_populates="audit_logs")
    
    # Constraints
    __table_args__ = (
        Index("idx_audit_logs_event_type_timestamp", "event_type", "timestamp"),
        Index("idx_audit_logs_actor_timestamp", "actor_id", "timestamp"),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', timestamp={self.timestamp})>" 