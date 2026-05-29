"""Audit and document schemas"""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any
from app.models.document import DocumentType, DocumentStatus
from app.models.audit_report import ReportStatus, RiskLevel
from app.models.anomaly import AnomalyType, AnomalySeverity, AnomalyStatus


class DocumentOut(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    doc_type: DocumentType
    status: DocumentStatus
    period_start: str | None
    period_end: str | None
    created_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True


class AuditReportCreate(BaseModel):
    title: str
    period: str | None = None
    source_document_ids: list[UUID] = []
    additional_context: str = ""


class AuditReportOut(BaseModel):
    id: UUID
    title: str
    period: str | None
    status: ReportStatus
    risk_level: RiskLevel | None
    overall_health_score: float | None
    liquidity_score: float | None
    profitability_score: float | None
    solvency_score: float | None
    efficiency_score: float | None
    executive_summary: str | None
    key_findings: Any | None
    risk_matrix: Any | None
    recommendations: Any | None
    kpis: Any | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class AnomalyOut(BaseModel):
    id: UUID
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    status: AnomalyStatus
    title: str
    description: str
    ai_explanation: str | None
    recommendation: str | None
    line_item: str | None
    amount: float | None
    expected_amount: float | None
    variance_pct: float | None
    confidence_score: float | None
    created_at: datetime

    class Config:
        from_attributes = True


class AnomalyUpdate(BaseModel):
    status: AnomalyStatus
    resolution_notes: str | None = None


class ChatMessage(BaseModel):
    message: str
    document_ids: list[UUID] = []
    conversation_history: list[dict] = []


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []


class DashboardMetrics(BaseModel):
    total_documents: int
    total_reports: int
    open_anomalies: int
    critical_anomalies: int
    avg_health_score: float | None
    recent_reports: list[AuditReportOut]
    recent_anomalies: list[AnomalyOut]
