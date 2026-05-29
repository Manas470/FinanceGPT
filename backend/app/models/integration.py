"""Integration model — QuickBooks, Xero OAuth connections"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class IntegrationProvider(str, enum.Enum):
    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    MANUAL = "manual"


class IntegrationStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    provider: Mapped[IntegrationProvider] = mapped_column(SAEnum(IntegrationProvider))
    status: Mapped[IntegrationStatus] = mapped_column(SAEnum(IntegrationStatus), default=IntegrationStatus.ACTIVE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # OAuth tokens (encrypted in production)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Provider-specific IDs
    external_company_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Sync settings
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sync_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # last sync cursors

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="integrations")

    def __repr__(self):
        return f"<Integration {self.provider} [{self.status}]>"
