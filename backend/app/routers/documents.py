"""Documents router — upload, parse, manage financial files"""
import uuid
import logging
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.anomaly import Anomaly, AnomalyStatus
from app.schemas.audit import DocumentOut
from app.core.security import get_current_user
from app.services.document_parser import document_parser
from app.services.ai_audit_engine import detect_anomalies, extract_kpis
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: DocumentType = Form(DocumentType.OTHER),
    period_start: str | None = Form(None),
    period_end: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Guard: company must exist BEFORE any file I/O to avoid orphaned files
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User must belong to a company to upload documents")

    # Validate file type
    if file.content_type not in [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/pdf",
    ]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    # Validate file size
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    # Save to disk
    doc_id = uuid.uuid4()
    suffix = Path(file.filename).suffix
    saved_filename = f"{doc_id}{suffix}"
    file_path = UPLOAD_DIR / saved_filename

    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        id=doc_id,
        company_id=current_user.company_id,
        uploaded_by_id=current_user.id,
        filename=saved_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type,
        doc_type=doc_type,
        status=DocumentStatus.PENDING,
        period_start=period_start,
        period_end=period_end,
    )
    db.add(doc)
    await db.flush()

    # Queue background processing
    background_tasks.add_task(process_document, str(doc_id), str(file_path), file.content_type)

    logger.info(f"Document {doc_id} uploaded by {current_user.email}")
    return doc


async def process_document(doc_id: str, file_path: str, mime_type: str):
    """Background task: parse document and run anomaly detection"""
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            doc.status = DocumentStatus.PROCESSING
            await db.commit()

            # Parse document
            parsed_data = await document_parser.parse(file_path, mime_type)

            # Auto-detect doc type if OTHER
            if doc.doc_type == DocumentType.OTHER:
                detected = document_parser.detect_document_type(parsed_data, doc.original_filename)
                # Check against string values, not enum members
                valid_values = {e.value for e in DocumentType}
                doc.doc_type = DocumentType(detected) if detected in valid_values else DocumentType.OTHER

            # Extract KPIs
            kpis = await extract_kpis(parsed_data, doc.doc_type.value)
            parsed_data["kpis"] = kpis

            # Run anomaly detection
            from app.models.company import Company
            company_result = await db.execute(select(Company).where(Company.id == doc.company_id))
            company = company_result.scalar_one_or_none()
            company_name = company.name if company else "Unknown Company"

            anomalies = await detect_anomalies(
                financial_data=parsed_data,
                company_name=company_name,
                period=f"{doc.period_start or 'Unknown'} to {doc.period_end or 'Unknown'}",
            )

            # Save anomalies
            for a in anomalies:
                anomaly = Anomaly(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    company_id=doc.company_id,
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

            doc.extracted_data = parsed_data
            doc.status = DocumentStatus.PROCESSED
            doc.processed_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Document {doc_id} processed. Anomalies: {len(anomalies)}")

        except Exception as e:
            logger.error(f"Document {doc_id} processing failed: {e}", exc_info=True)
            async with AsyncSessionLocal() as db2:
                result = await db2.execute(select(Document).where(Document.id == doc_id))
                doc = result.scalar_one_or_none()
                if doc:
                    doc.status = DocumentStatus.FAILED
                    doc.extraction_error = str(e)
                    await db2.commit()


@router.get("/", response_model=list[DocumentOut])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    result = await db.execute(
        select(Document)
        .where(Document.company_id == current_user.company_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.company_id == current_user.company_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.company_id == current_user.company_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file
    try:
        Path(doc.file_path).unlink(missing_ok=True)
    except Exception:
        pass

    await db.delete(doc)
