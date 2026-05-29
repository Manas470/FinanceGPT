"""Company model"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fiscal_year_end: Mapped[str] = mapped_column(String(10), default="12-31")  # MM-DD
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    revenue_range: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "$1M-$10M"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="company")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="company")
    audit_reports: Mapped[list["AuditReport"]] = relationship("AuditReport", back_populates="company")
    integrations: Mapped[list["Integration"]] = relationship("Integration", back_populates="company")

    def __repr__(self):
        return f"<Company {self.name}>"
