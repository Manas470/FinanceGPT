"""Anomaly model — flagged financial irregularities"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class AnomalyType(str, enum.Enum):
    UNUSUAL_VARIANCE = "unusual_variance"
    MISSING_DATA = "missing_data"
    RATIO_OUTLIER = "ratio_outlier"
    TREND_REVERSAL = "trend_reversal"
    DUPLICATE_ENTRY = "duplicate_entry"
    ROUND_NUMBER = "round_number"          # Benford's law violation
    YEAR_END_SPIKE = "year_end_spike"
    INTERCOMPANY = "intercompany"
    UNRECONCILED = "unreconciled"
    POLICY_BREACH = "policy_breach"


class AnomalySeverity(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    audit_report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("audit_reports.id"), nullable=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    anomaly_type: Mapped[AnomalyType] = mapped_column(SAEnum(AnomalyType))
    severity: Mapped[AnomalySeverity] = mapped_column(SAEnum(AnomalySeverity))
    status: Mapped[AnomalyStatus] = mapped_column(SAEnum(AnomalyStatus), default=AnomalyStatus.OPEN)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Where in the data
    line_item: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    variance_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-1

    is_auto_detected: Mapped[bool] = mapped_column(Boolean, default=True)
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="anomalies")
    audit_report: Mapped["AuditReport"] = relationship("AuditReport", back_populates="anomalies")

    def __repr__(self):
        return f"<Anomaly {self.anomaly_type} [{self.severity}]>"
