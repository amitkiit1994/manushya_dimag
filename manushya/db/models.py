"""
Database models for Manushya.ai
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from manushya.config import settings

from .database import Base


class Tenant(Base):
    """Tenant model for multi-tenancy."""

    __tablename__ = "tenants"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Relationships
    identities: Mapped[list["Identity"]] = relationship(
        "Identity", back_populates="tenant"
    )
    memories: Mapped[list["Memory"]] = relationship("Memory", back_populates="tenant")
    policies: Mapped[list["Policy"]] = relationship("Policy", back_populates="tenant")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="tenant"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="tenant")
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", back_populates="tenant"
    )
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="tenant")
    identity_events: Mapped[list["IdentityEvent"]] = relationship(
        "IdentityEvent", back_populates="tenant"
    )
    rate_limits: Mapped[list["RateLimit"]] = relationship(
        "RateLimit", back_populates="tenant"
    )
    webhooks: Mapped[list["Webhook"]] = relationship("Webhook", back_populates="tenant")
    webhook_deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="tenant"
    )
    usage_events: Mapped[list["UsageEvent"]] = relationship(
        "UsageEvent", back_populates="tenant"
    )
    usage_daily: Mapped[list["UsageDaily"]] = relationship(
        "UsageDaily", back_populates="tenant"
    )
    sso_providers: Mapped[list["SSOProvider"]] = relationship(
        "SSOProvider", back_populates="tenant"
    )
    sso_sessions: Mapped[list["SSOSession"]] = relationship(
        "SSOSession", back_populates="tenant"
    )

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}')>"


class Identity(Base):
    """Identity model for agents and users."""

    __tablename__ = "identities"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    claims: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship(
        "Tenant", back_populates="identities"
    )
    # SSO fields
    sso_provider: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    sso_external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    sso_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    sso_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # Relationships
    memories: Mapped[list["Memory"]] = relationship("Memory", back_populates="identity")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="actor_identity"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="identity")
    sent_invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", back_populates="invited_by_identity"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="identity"
    )
    events: Mapped[list["IdentityEvent"]] = relationship(
        "IdentityEvent",
        back_populates="identity",
        foreign_keys="[IdentityEvent.identity_id]",
    )
    acted_events: Mapped[list["IdentityEvent"]] = relationship(
        "IdentityEvent", back_populates="actor", foreign_keys="[IdentityEvent.actor_id]"
    )
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
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    identity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    vector: Mapped[list[float]] = mapped_column(
        Vector(settings.vector_dimension), nullable=True
    )  # pgvector
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    ttl_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="memories")
    # Relationships
    identity: Mapped["Identity"] = relationship("Identity", back_populates="memories")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="memory"
    )
    # Constraints
    __table_args__ = (
        Index("idx_memories_identity_type", "identity_id", "type"),
        Index("idx_memories_created_at", "created_at"),
        Index("idx_memories_deleted_at", "deleted_at"),
        CheckConstraint("score >= 0 AND score <= 1", name="ck_memories_score_range"),
    )

    @property
    def expires_at(self) -> datetime | None:
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
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rule: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="policies")
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
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    memory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )  # IPv6 compatible
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship(
        "Tenant", back_populates="audit_logs"
    )
    # Relationships
    memory: Mapped[Optional["Memory"]] = relationship(
        "Memory", back_populates="audit_logs"
    )
    actor_identity: Mapped[Optional["Identity"]] = relationship(
        "Identity", back_populates="audit_logs"
    )
    # Constraints
    __table_args__ = (
        Index("idx_audit_logs_event_type_timestamp", "event_type", "timestamp"),
        Index("idx_audit_logs_actor_timestamp", "actor_id", "timestamp"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', timestamp={self.timestamp})>"


class ApiKey(Base):
    """API Key model for programmatic access."""

    __tablename__ = "api_keys"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    identity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scopes: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="api_keys")
    # Relationships
    identity: Mapped["Identity"] = relationship("Identity", back_populates="api_keys")
    # Constraints
    __table_args__ = (
        Index("idx_api_keys_identity_active", "identity_id", "is_active"),
        Index("idx_api_keys_expires_at", "expires_at"),
        Index("idx_api_keys_last_used", "last_used_at"),
    )

    @property
    def is_expired(self) -> bool:
        """Check if API key is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    def __repr__(self):
        return f"<ApiKey(id={self.id}, name='{self.name}', identity_id={self.identity_id})>"


class Invitation(Base):
    """Invitation model for email-based user invitations."""

    __tablename__ = "invitations"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    claims: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    token: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    invited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_accepted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="invitations")
    # Relationships
    invited_by_identity: Mapped["Identity | None"] = relationship(
        "Identity", back_populates="sent_invitations"
    )
    # Constraints
    __table_args__ = (
        Index("idx_invitations_email_tenant", "email", "tenant_id"),
        Index("idx_invitations_token", "token"),
        Index("idx_invitations_expires_at", "expires_at"),
        Index("idx_invitations_accepted", "is_accepted"),
    )

    @property
    def is_expired(self) -> bool:
        """Check if invitation is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if invitation is valid (not accepted and not expired)."""
        return not self.is_accepted and not self.is_expired

    def __repr__(self):
        return f"<Invitation(id={self.id}, email='{self.email}', role='{self.role}')>"


class Session(Base):
    """Session model for managing user sessions with refresh tokens."""

    __tablename__ = "sessions"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    identity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    device_info: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )  # IPv6 compatible
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="sessions")
    # Relationships
    identity: Mapped["Identity"] = relationship("Identity", back_populates="sessions")
    # Constraints
    __table_args__ = (
        Index("idx_sessions_identity_active", "identity_id", "is_active"),
        Index("idx_sessions_expires_at", "expires_at"),
        Index("idx_sessions_last_used", "last_used_at"),
    )

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now(UTC) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    def __repr__(self):
        return f"<Session(id={self.id}, identity_id={self.identity_id}, is_active={self.is_active})>"


class IdentityEvent(Base):
    """Identity event model for real-time identity lifecycle events."""

    __tablename__ = "identity_events"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    identity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    is_delivered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    delivery_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship(
        "Tenant", back_populates="identity_events"
    )
    # Relationships
    identity: Mapped["Identity | None"] = relationship(
        "Identity", back_populates="events", foreign_keys=[identity_id]
    )
    actor: Mapped["Identity | None"] = relationship(
        "Identity", back_populates="acted_events", foreign_keys=[actor_id]
    )
    # Constraints
    __table_args__ = (
        Index("idx_identity_events_type_created", "event_type", "created_at"),
        Index("idx_identity_events_delivered", "is_delivered"),
        Index("idx_identity_events_identity_type", "identity_id", "event_type"),
    )

    def __repr__(self):
        return f"<IdentityEvent(id={self.id}, event_type='{self.event_type}', identity_id={self.identity_id})>"


class RateLimit(Base):
    """Rate limit model for API usage throttling."""

    __tablename__ = "rate_limits"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_request_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship(
        "Tenant", back_populates="rate_limits"
    )
    # Constraints
    __table_args__ = (
        Index(
            "idx_rate_limits_client_endpoint_window",
            "client_key",
            "endpoint",
            "window_start",
        ),
        Index("idx_rate_limits_window_start", "window_start"),
    )

    def __repr__(self):
        return f"<RateLimit(id={self.id}, client_key='{self.client_key}', endpoint='{self.endpoint}', count={self.request_count})>"


class Webhook(Base):
    """Webhook model for real-time notifications."""

    __tablename__ = "webhooks"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    events: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    secret: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # For signature verification
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="webhooks")
    # Relationships
    created_by_identity: Mapped["Identity | None"] = relationship(
        "Identity", foreign_keys=[created_by]
    )
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="webhook"
    )
    # Constraints
    __table_args__ = (
        Index("idx_webhooks_tenant_active", "tenant_id", "is_active"),
        Index("idx_webhooks_events", "events", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<Webhook(id={self.id}, name='{self.name}', url='{self.url}')>"


class WebhookDelivery(Base):
    """Webhook delivery tracking model."""

    __tablename__ = "webhook_deliveries"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    webhook_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, delivered, failed
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    tenant: Mapped["Tenant | None"] = relationship(
        "Tenant", back_populates="webhook_deliveries"
    )
    # Relationships
    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="deliveries")
    # Constraints
    __table_args__ = (
        Index("idx_webhook_deliveries_status", "status"),
        Index("idx_webhook_deliveries_next_retry", "next_retry_at"),
        Index("idx_webhook_deliveries_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, webhook_id={self.webhook_id}, event_type='{self.event_type}', status='{self.status}')>"


class UsageEvent(Base):
    """Usage event model for billing and analytics."""

    __tablename__ = "usage_events"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    identity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    units: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="usage_events")
    api_key: Mapped["ApiKey | None"] = relationship("ApiKey")
    identity: Mapped["Identity | None"] = relationship("Identity")
    # Constraints
    __table_args__ = (
        Index("idx_usage_events_tenant_created", "tenant_id", "created_at"),
        Index("idx_usage_events_event_created", "event", "created_at"),
    )

    def __repr__(self):
        return f"<UsageEvent(id={self.id}, tenant_id={self.tenant_id}, event='{self.event}', units={self.units})>"


class UsageDaily(Base):
    """Daily aggregated usage for billing."""

    __tablename__ = "usage_daily"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    event: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="usage_daily")
    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "date", "event", name="uq_usage_daily_tenant_date_event"
        ),
        Index("idx_usage_daily_tenant_date", "tenant_id", "date"),
    )

    def __repr__(self):
        return f"<UsageDaily(id={self.id}, tenant_id={self.tenant_id}, date={self.date}, event='{self.event}', units={self.units})>"


class SSOProvider(Base):
    """SSO Provider model for OAuth2/OIDC configuration."""

    __tablename__ = "sso_providers"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String(255), nullable=False)
    client_secret: Mapped[str] = mapped_column(String(500), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="sso_providers")
    # Constraints
    __table_args__ = (
        Index("idx_sso_providers_tenant_active", "tenant_id", "is_active"),
        Index("idx_sso_providers_type", "provider_type"),
    )

    def __repr__(self):
        return f"<SSOProvider(id={self.id}, name='{self.name}', provider_type='{self.provider_type}')>"


class SSOSession(Base):
    """SSO Session model for OAuth2 state management."""

    __tablename__ = "sso_sessions"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    nonce: Mapped[str] = mapped_column(String(255), nullable=True)
    redirect_uri: Mapped[str] = mapped_column(String(500), nullable=False)
    scope: Mapped[str] = mapped_column(String(500), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="sso_sessions")
    # Constraints
    __table_args__ = (
        Index("idx_sso_sessions_provider_state", "provider", "state"),
        Index("idx_sso_sessions_expires_at", "expires_at"),
    )

    @property
    def is_expired(self) -> bool:
        """Check if SSO session is expired."""
        return datetime.now(UTC) > self.expires_at

    def __repr__(self):
        return f"<SSOSession(id={self.id}, provider='{self.provider}', state='{self.state}')>"
