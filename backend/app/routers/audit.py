"""Audit Reports router — generate and retrieve CFO audit reports"""
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.audit_report import AuditReport, ReportStatus, RiskLevel
from app.models.anomaly import Anomaly, AnomalyStatus
from app.schemas.audit import (
    AuditReportCreate, AuditReportOut,
    AnomalyOut, AnomalyUpdate,
    ChatMessage, ChatResponse,
    DashboardMetrics,
)
from app.core.security import get_current_user
from app.services.ai_audit_engine import (
    generate_cfo_audit_report,
    financial_qa,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit"])


@router.post("/reports", response_model=AuditReportOut, status_code=202)
async def create_audit_report(
    data: AuditReportCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI-powered CFO audit report generation"""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User must belong to a company")

    report = AuditReport(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        created_by_id=current_user.id,
        title=data.title,
        period=data.period,
        status=ReportStatus.GENERATING,
        source_document_ids=[str(d) for d in data.source_document_ids],
    )
    db.add(report)
    await db.flush()

    background_tasks.add_task(
        _generate_report_bg,
        str(report.id),
        str(current_user.company_id),
        [str(d) for d in data.source_document_ids],
        data.additional_context,
    )

    return report


async def _generate_report_bg(
    report_id: str,
    company_id: str,
    document_ids: list[str],
    additional_context: str,
):
    """Background task: run AI audit analysis and save results"""
    from app.database import AsyncSessionLocal
    from app.models.company import Company

    async with AsyncSessionLocal() as db:
        try:
            # Load report and company
            report_result = await db.execute(select(AuditReport).where(AuditReport.id == report_id))
            report = report_result.scalar_one()

            company_result = await db.execute(select(Company).where(Company.id == company_id))
            company = company_result.scalar_one()

            # Gather financial data from documents
            financial_data = {}
            if document_ids:
                for doc_id in document_ids:
                    doc_result = await db.execute(
                        select(Document).where(
                            Document.id == doc_id,
                            Document.status == DocumentStatus.PROCESSED,
                        )
                    )
                    doc = doc_result.scalar_one_or_none()
                    if doc and doc.extracted_data:
                        financial_data[doc.doc_type.value] = doc.extracted_data
            else:
                # Use all processed documents for this company
                docs_result = await db.execute(
                    select(Document).where(
                        Document.company_id == company_id,
                        Document.status == DocumentStatus.PROCESSED,
                    ).limit(10)
                )
                for doc in docs_result.scalars().all():
                    if doc.extracted_data:
                        financial_data[doc.doc_type.value] = doc.extracted_data

            if not financial_data:
                financial_data = {"note": "No processed documents available — provide context manually"}

            # Run AI audit
            audit_results = await generate_cfo_audit_report(
                company_name=company.name,
                period=report.period or "Current Period",
                financial_data=financial_data,
                additional_context=additional_context,
            )

            # Map results to report
            scores = audit_results.get("scores", {})
            risk_level_str = audit_results.get("risk_level", "medium")

            report.status = ReportStatus.COMPLETED
            report.overall_health_score = audit_results.get("overall_health_score")
            report.liquidity_score = scores.get("liquidity")
            report.profitability_score = scores.get("profitability")
            report.solvency_score = scores.get("solvency")
            report.efficiency_score = scores.get("efficiency")
            # Check against string values (e.g. "high"), not enum members
            valid_risk_values = {e.value for e in RiskLevel}
            report.risk_level = RiskLevel(risk_level_str) if risk_level_str in valid_risk_values else RiskLevel.MEDIUM
            report.executive_summary = audit_results.get("executive_summary")
            report.key_findings = audit_results.get("key_findings", [])
            report.risk_matrix = audit_results.get("risk_matrix", {})
            report.recommendations = audit_results.get("recommendations", [])
            report.kpis = audit_results.get("kpis", {})
            report.completed_at = datetime.utcnow()

            # Save anomalies from audit
            for a in audit_results.get("anomalies", []):
                anomaly = Anomaly(
                    id=uuid.uuid4(),
                    audit_report_id=report.id,
                    company_id=company_id,
                    anomaly_type=a.get("type", "unusual_variance"),
                    severity=a.get("severity", "medium"),
                    status=AnomalyStatus.OPEN,
                    title=a.get("title", "Anomaly detected"),
                    description=a.get("description", ""),
                    ai_explanation=a.get("ai_explanation"),
                    recommendation=a.get("recommendation"),
                    line_item=a.get("line_item"),
                    amount=a.get("amount"),
                    expected_amount=a.get("expected_amount"),
                    variance_pct=a.get("variance_pct"),
                    confidence_score=a.get("confidence_score"),
                    is_auto_detected=True,
                )
                db.add(anomaly)

            await db.commit()
            logger.info(f"Audit report {report_id} completed successfully")

        except Exception as e:
            logger.error(f"Audit report {report_id} failed: {e}", exc_info=True)
            async with AsyncSessionLocal() as db2:
                r = await db2.execute(select(AuditReport).where(AuditReport.id == report_id))
                report = r.scalar_one_or_none()
                if report:
                    report.status = ReportStatus.FAILED
                    report.error_message = str(e)
                    await db2.commit()


@router.get("/reports", response_model=list[AuditReportOut])
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
):
    result = await db.execute(
        select(AuditReport)
        .where(AuditReport.company_id == current_user.company_id)
        .order_by(AuditReport.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/reports/{report_id}", response_model=AuditReportOut)
async def get_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditReport).where(
            AuditReport.id == report_id,
            AuditReport.company_id == current_user.company_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/anomalies", response_model=list[AnomalyOut])
async def list_anomalies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    severity: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
):
    query = select(Anomaly).where(Anomaly.company_id == current_user.company_id)
    if severity:
        query = query.where(Anomaly.severity == severity)
    if status:
        query = query.where(Anomaly.status == status)
    query = query.order_by(Anomaly.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/anomalies/{anomaly_id}", response_model=AnomalyOut)
async def update_anomaly(
    anomaly_id: uuid.UUID,
    data: AnomalyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Anomaly).where(
            Anomaly.id == anomaly_id,
            Anomaly.company_id == current_user.company_id,
        )
    )
    anomaly = result.scalar_one_or_none()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    anomaly.status = data.status
    anomaly.resolution_notes = data.resolution_notes
    anomaly.resolved_by_id = current_user.id
    anomaly.resolved_at = datetime.utcnow()
    return anomaly


@router.post("/chat", response_model=ChatResponse)
async def chat_with_data(
    data: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Natural language Q&A against your financial data"""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User must belong to a company")

    # Gather context from specified or recent documents
    financial_context = {}
    doc_query = select(Document).where(
        Document.company_id == current_user.company_id,
        Document.status == DocumentStatus.PROCESSED,
    )
    if data.document_ids:
        doc_query = doc_query.where(Document.id.in_([str(d) for d in data.document_ids]))
    else:
        doc_query = doc_query.order_by(Document.created_at.desc()).limit(5)

    docs_result = await db.execute(doc_query)
    for doc in docs_result.scalars().all():
        if doc.extracted_data:
            financial_context[doc.doc_type.value] = doc.extracted_data

    from app.models.company import Company
    company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = company_result.scalar_one_or_none()

    response = await financial_qa(
        question=data.message,
        financial_context=financial_context,
        company_name=company.name if company else "Your Company",
        conversation_history=data.conversation_history,
    )

    return ChatResponse(response=response)


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company_id = current_user.company_id

    # Counts
    total_docs = await db.scalar(
        select(func.count(Document.id)).where(Document.company_id == company_id)
    ) or 0
    total_reports = await db.scalar(
        select(func.count(AuditReport.id)).where(AuditReport.company_id == company_id)
    ) or 0
    open_anomalies = await db.scalar(
        select(func.count(Anomaly.id)).where(
            Anomaly.company_id == company_id,
            Anomaly.status == AnomalyStatus.OPEN,
        )
    ) or 0
    critical_anomalies = await db.scalar(
        select(func.count(Anomaly.id)).where(
            Anomaly.company_id == company_id,
            Anomaly.severity == "critical",
            Anomaly.status == AnomalyStatus.OPEN,
        )
    ) or 0

    avg_score = await db.scalar(
        select(func.avg(AuditReport.overall_health_score)).where(
            AuditReport.company_id == company_id,
            AuditReport.status == ReportStatus.COMPLETED,
        )
    )

    # Recent reports & anomalies
    recent_reports_result = await db.execute(
        select(AuditReport)
        .where(AuditReport.company_id == company_id)
        .order_by(AuditReport.created_at.desc())
        .limit(5)
    )
    recent_anomalies_result = await db.execute(
        select(Anomaly)
        .where(Anomaly.company_id == company_id, Anomaly.status == AnomalyStatus.OPEN)
        .order_by(Anomaly.created_at.desc())
        .limit(5)
    )

    return DashboardMetrics(
        total_documents=total_docs,
        total_reports=total_reports,
        open_anomalies=open_anomalies,
        critical_anomalies=critical_anomalies,
        avg_health_score=round(float(avg_score), 1) if avg_score else None,
        recent_reports=recent_reports_result.scalars().all(),
        recent_anomalies=recent_anomalies_result.scalars().all(),
    )
