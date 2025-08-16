import datetime as dt
from sqlalchemy import func
from app.db import SessionLocal
from app.config import settings
from app.models import MetricEvent

def _since(days: int): 
    return dt.datetime.utcnow() - dt.timedelta(days=7 if days <= 0 else days)

def epc_7d(platform: str | None = None, niche: str | None = None) -> float:
    """EPC observé (€/clic) sur 7j; fallback DEFAULT_EPC_EUR si pas de data."""
    db = SessionLocal()
    since = _since(7)
    q = db.query(
        func.coalesce(func.sum(MetricEvent.value * 0.20), 0.0),  # Fallback: value * default EPC
        func.coalesce(func.count(), 0)
    ).filter(MetricEvent.kind == "click", MetricEvent.ts >= since)
    if platform:
        q = q.filter(MetricEvent.platform == platform)
    result = q.first()
    db.close()
    if not result or not result[1]:
        return float(settings.DEFAULT_EPC_EUR)
    total, n = result[0], result[1]
    return float(total) / float(n)

def compute_cpc(epc: float) -> float:
    """CPC partenaire = clamp( epc * REVSHARE - buffer, [floor, ceiling] )."""
    base = epc * float(settings.REVSHARE_BASE_PCT)
    cpc = base - float(settings.CPC_SAFETY_MARGIN_EUR)
    cpc = max(float(settings.CPC_MIN_EUR), min(float(settings.CPC_MAX_EUR), cpc))
    # si data trop faible, fallback
    if cpc < settings.CPC_MIN_EUR + 0.001 and epc <= 0.15:
        cpc = float(settings.CPC_DEFAULT_EUR)
    return round(cpc, 2)

def current_offer() -> dict:
    mode = (settings.OFFER_MODE or "cpc_dynamic").lower()
    epc = epc_7d()
    if mode == "cpc_fixed":
        cpc = round(float(settings.CPC_DEFAULT_EUR), 2)
        return {"headline_cpc": cpc, "epc_7d": round(epc, 2), "terms": {"mode": mode, "cpc": cpc}}
    if mode == "revshare":
        pct = float(settings.REVSHARE_BASE_PCT)
        return {"headline_cpc": round(epc * pct, 2), "epc_7d": round(epc, 2), "terms": {"mode": mode, "revshare_pct": pct}}
    if mode == "hybrid":
        pct = float(settings.REVSHARE_BASE_PCT)
        fixed = float(settings.CPC_MIN_EUR)
        headline = round(max(fixed, epc * pct - settings.CPC_SAFETY_MARGIN_EUR), 2)
        return {"headline_cpc": headline, "epc_7d": round(epc, 2), "terms": {"mode": mode, "fixed": fixed, "revshare_pct": pct}}
    # cpc_dynamic
    cpc = compute_cpc(epc)
    return {"headline_cpc": float(cpc), "epc_7d": round(epc, 2), "terms": {"mode": "cpc_dynamic", "cpc": cpc}}