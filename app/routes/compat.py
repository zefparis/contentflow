from fastapi import APIRouter, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse

# Import existing handlers to proxy where possible
from app.routes.partner_auth import send_magic_link as partner_send_magic_link
from app.aiops.autopilot import get_agent_status
from app.services.pricing import epc_7d, compute_cpc

router = APIRouter()

@router.post("/api/auth/magic-link")
def compat_magic_link(email: str = Form(...)):
    """
    Compatibility endpoint expected by older frontend: POST /api/auth/magic-link
    Proxies to current /partner/magic implementation.
    """
    resp = partner_send_magic_link(email)  # returns HTMLResponse
    if isinstance(resp, HTMLResponse):
        return resp
    # Fallback: standard message
    return HTMLResponse("<h3>Magic link processed</h3>")

@router.post("/api/payments/calculate")
def compat_payments_calculate(platform: str | None = Query(None)):
    """
    Legacy endpoint used by UI to compute partner CPC/payment terms.
    Uses pricing service to compute EPC and CPC.
    """
    epc = float(epc_7d(platform=platform))
    cpc = float(compute_cpc(epc))
    # Keep legacy fields and add dummy contract for frontend expecting {amount, currency}
    return JSONResponse({
        "success": True,
        "platform": platform,
        "epc_7d": round(epc, 3),
        "cpc": cpc,
        "amount": round(cpc, 2),
        "currency": "EUR",
    })

@router.get("/api/ai/orchestrator/status")
def compat_ai_orchestrator_status():
    """
    Legacy path used by UI; maps to /api/ai/status
    """
    return JSONResponse(get_agent_status())

@router.get("/api/auth/magic-link")
def compat_magic_link_get(email: str = Query(...)):
    """
    Some older frontends call GET /api/auth/magic-link?email=...
    Delegate to POST handler implementation.
    """
    resp = partner_send_magic_link(email)
    if isinstance(resp, HTMLResponse):
        return resp
    return HTMLResponse("<h3>Magic link processed</h3>")
