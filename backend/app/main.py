"""
FinanceGPT — CFO-grade AI Audit Platform
FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import time

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth, documents, audit, integrations

# ─── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    await init_db()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    yield
    await close_db()
    logger.info("Application shutdown complete")


# ─── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="FinanceGPT API",
    description="""
## FinanceGPT — AI-Powered CFO Audit Platform

Production-grade financial analysis powered by Anthropic Claude.

### Features
- 📊 **CFO Audit Reports** — AI-generated comprehensive financial audits
- 🔍 **Anomaly Detection** — Automated flagging of financial irregularities
- 💬 **Financial Q&A** — Natural language queries against your financial data
- 📁 **Multi-format Ingestion** — CSV, Excel, PDF support
- 🔗 **Integrations** — QuickBooks & Xero OAuth sync
- 🛡️ **RBAC** — Role-based access control (CFO, Auditor, Analyst, Viewer)
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── Middleware ────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
    logger.debug(f"{request.method} {request.url.path} → {response.status_code} ({duration_ms:.1f}ms)")
    return response


# ─── Exception Handlers ───────────────────────────────────────
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error" if not settings.DEBUG else str(exc)},
    )


# ─── Routers ──────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(integrations.router, prefix="/api")


# ─── Health & Info ────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api", tags=["System"])
async def api_info():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/redoc",
        "endpoints": {
            "auth": "/api/auth",
            "documents": "/api/documents",
            "audit": "/api/audit",
            "integrations": "/api/integrations",
            "dashboard": "/api/audit/dashboard",
        },
    }
