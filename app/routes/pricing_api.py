from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services.pricing import current_offer, epc_7d, compute_cpc
from app.config import settings

router = APIRouter(tags=["pricing"])

@router.get("/api/pricing/current")
def get_current_pricing():
    """API pour récupérer l'offre tarifaire actuelle."""
    try:
        offer = current_offer()
        return JSONResponse({
            "success": True,
            "data": offer
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/api/pricing/epc")
def get_epc_stats(platform: str = None, days: int = 7):
    """API pour récupérer l'EPC par plateforme."""
    try:
        epc = epc_7d(platform=platform)
        return JSONResponse({
            "success": True,
            "data": {
                "epc": round(epc, 3),
                "platform": platform,
                "days": days
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/api/pricing/config")
def get_pricing_config():
    """API pour récupérer la configuration pricing."""
    return JSONResponse({
        "success": True,
        "data": {
            "mode": settings.OFFER_MODE,
            "default_epc": settings.DEFAULT_EPC_EUR,
            "cpc_default": settings.CPC_DEFAULT_EUR,
            "cpc_min": settings.CPC_MIN_EUR,
            "cpc_max": settings.CPC_MAX_EUR,
            "revshare_pct": settings.REVSHARE_BASE_PCT,
            "safety_margin": settings.CPC_SAFETY_MARGIN_EUR
        }
    })