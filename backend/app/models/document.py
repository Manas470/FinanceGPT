"""Document model — uploaded financial files"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class DocumentType(str, enum.Enum):
    PROFIT_LOSS = "profit_loss"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    TRIAL_BALANCE = "trial_balance"
    GENERAL_LEDGER = "general_ledger"
    ANNUAL_REPORT = "annual_report"
    INVOICE = "invoice"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    doc_type: Mapped[DocumentType] = mapped_column(SAEnum(DocumentType), default=DocumentType.OTHER)
    status: Mapped[DocumentStatus] = mapped_column(SAEnum(DocumentStatus), default=DocumentStatus.PENDING)

    # Extracted data (JSON)
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Period covered
    period_start: Mapped[str | None] = mapped_column(String(20), nullable=True)  # YYYY-MM-DD
    period_end: Mapped[str | None] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="documents")
    uploaded_by: Mapped["User"] = relationship("User", back_populates="documents")
    anomalies: Mapped[list["Anomaly"]] = relationship("Anomaly", back_populates="document")

    def __repr__(self):
        return f"<Document {self.original_filename} [{self.doc_type}]>"
