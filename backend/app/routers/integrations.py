"""
Integrations router — QuickBooks & Xero OAuth + data sync
"""
import uuid
import logging
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.integration import Integration, IntegrationProvider, IntegrationStatus
from app.core.security import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations", tags=["Integrations"])


# ─── QuickBooks ────────────────────────────────────────────────
QB_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QB_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QB_BASE_URL = "https://quickbooks.api.intuit.com"
QB_SCOPES = "com.intuit.quickbooks.accounting"


@router.get("/quickbooks/authorize")
async def quickbooks_authorize(current_user: User = Depends(get_current_user)):
    """Step 1: Redirect user to QuickBooks OAuth"""
    import secrets
    state = secrets.token_urlsafe(32)
    auth_url = (
        f"{QB_AUTH_URL}?"
        f"client_id={settings.QB_CLIENT_ID}&"
        f"redirect_uri={settings.QB_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={QB_SCOPES}&"
        f"state={state}"
    )
    return {"auth_url": auth_url, "state": state}


@router.get("/quickbooks/callback")
async def quickbooks_callback(
    code: str,
    state: str,
    realmId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Step 2: Exchange code for tokens"""
    import base64

    credentials = base64.b64encode(
        f"{settings.QB_CLIENT_ID}:{settings.QB_CLIENT_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            QB_TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.QB_REDIRECT_URI,
            },
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="QuickBooks OAuth failed")

    tokens = resp.json()

    # Upsert integration record
    existing = await db.execute(
        select(Integration).where(
            Integration.company_id == current_user.company_id,
            Integration.provider == IntegrationProvider.QUICKBOOKS,
        )
    )
    integration = existing.scalar_one_or_none()

    if not integration:
        integration = Integration(
            id=uuid.uuid4(),
            company_id=current_user.company_id,
            provider=IntegrationProvider.QUICKBOOKS,
        )
        db.add(integration)

    integration.access_token = tokens["access_token"]
    integration.refresh_token = tokens["refresh_token"]
    integration.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
    integration.external_company_id = realmId
    integration.status = IntegrationStatus.ACTIVE
    integration.is_active = True

    return {"message": "QuickBooks connected", "realm_id": realmId}


@router.get("/quickbooks/sync")
async def sync_quickbooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sync financial data from QuickBooks"""
    result = await db.execute(
        select(Integration).where(
            Integration.company_id == current_user.company_id,
            Integration.provider == IntegrationProvider.QUICKBOOKS,
            Integration.is_active == True,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="QuickBooks not connected")

    realm_id = integration.external_company_id
    token = integration.access_token

    async with httpx.AsyncClient() as client:
        # Fetch P&L
        pl_resp = await client.get(
            f"{QB_BASE_URL}/v3/company/{realm_id}/reports/ProfitAndLoss",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            params={"minorversion": "73"},
        )
        # Fetch Balance Sheet
        bs_resp = await client.get(
            f"{QB_BASE_URL}/v3/company/{realm_id}/reports/BalanceSheet",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            params={"minorversion": "73"},
        )

    data = {}
    if pl_resp.status_code == 200:
        data["profit_loss"] = pl_resp.json()
    if bs_resp.status_code == 200:
        data["balance_sheet"] = bs_resp.json()

    integration.last_synced_at = datetime.utcnow()
    integration.sync_metadata = {"last_sync_status": "success", "records": list(data.keys())}

    return {"message": "Sync complete", "data_fetched": list(data.keys()), "data": data}


# ─── Xero ──────────────────────────────────────────────────────
XERO_AUTH_URL = "https://login.xero.com/identity/connect/authorize"
XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_BASE_URL = "https://api.xero.com/api.xro/2.0"
XERO_SCOPES = "openid profile email accounting.reports.read accounting.transactions"


@router.get("/xero/authorize")
async def xero_authorize(current_user: User = Depends(get_current_user)):
    import secrets
    state = secrets.token_urlsafe(32)
    auth_url = (
        f"{XERO_AUTH_URL}?"
        f"response_type=code&"
        f"client_id={settings.XERO_CLIENT_ID}&"
        f"redirect_uri={settings.XERO_REDIRECT_URI}&"
        f"scope={XERO_SCOPES}&"
        f"state={state}"
    )
    return {"auth_url": auth_url, "state": state}


@router.get("/xero/callback")
async def xero_callback(
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            XERO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.XERO_REDIRECT_URI,
                "client_id": settings.XERO_CLIENT_ID,
                "client_secret": settings.XERO_CLIENT_SECRET,
            },
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Xero OAuth failed")

    tokens = resp.json()

    existing = await db.execute(
        select(Integration).where(
            Integration.company_id == current_user.company_id,
            Integration.provider == IntegrationProvider.XERO,
        )
    )
    integration = existing.scalar_one_or_none()
    if not integration:
        integration = Integration(id=uuid.uuid4(), company_id=current_user.company_id, provider=IntegrationProvider.XERO)
        db.add(integration)

    integration.access_token = tokens["access_token"]
    integration.refresh_token = tokens.get("refresh_token")
    integration.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 1800))
    integration.status = IntegrationStatus.ACTIVE
    integration.is_active = True

    return {"message": "Xero connected"}


@router.get("/")
async def list_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(Integration.company_id == current_user.company_id)
    )
    integrations = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "provider": i.provider,
            "status": i.status,
            "is_active": i.is_active,
            "external_company_name": i.external_company_name,
            "last_synced_at": i.last_synced_at,
        }
        for i in integrations
    ]


@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Integration).where(
            Integration.id == integration_id,
            Integration.company_id == current_user.company_id,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    integration.is_active = False
    integration.status = IntegrationStatus.REVOKED
    return {"message": f"{integration.provider} disconnected"}
