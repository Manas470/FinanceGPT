"""Audit Report model — CFO-grade AI-generated reports"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class ReportStatus(str, enum.Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditReport(Base):
    __tablename__ = "audit_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    period: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "Q1 2024", "FY 2023"
    status: Mapped[ReportStatus] = mapped_column(SAEnum(ReportStatus), default=ReportStatus.GENERATING)
    risk_level: Mapped[RiskLevel | None] = mapped_column(SAEnum(RiskLevel), nullable=True)

    # AI-generated content (stored as structured JSON + markdown)
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_findings: Mapped[dict | None] = mapped_column(JSON, nullable=True)    # list of findings
    risk_matrix: Mapped[dict | None] = mapped_column(JSON, nullable=True)     # risk scores by category
    recommendations: Mapped[dict | None] = mapped_column(JSON, nullable=True) # list of action items
    kpis: Mapped[dict | None] = mapped_column(JSON, nullable=True)            # extracted KPIs
    full_report_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scores (0-100)
    overall_health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    profitability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    solvency_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    efficiency_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Source document IDs
    source_document_ids: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="audit_reports")
    created_by: Mapped["User"] = relationship("User", back_populates="audit_reports")
    anomalies: Mapped[list["Anomaly"]] = relationship("Anomaly", back_populates="audit_report")

    def __repr__(self):
        return f"<AuditReport {self.title} [{self.risk_level}]>"
