"""Shortlink redirects with revenue tracking and EPC calculation."""

import os
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import hashlib
from app.utils.datetime import utcnow

from app.db import get_db
from app.models import Link, MetricEvent, Post
from app.utils.logger import logger
from app.routes.health import increment_click_metric

router = APIRouter()

@router.get("/l/{hash}")
async def redirect_shortlink(
    hash: str, 
    request: Request, 
    response: Response,
    db: Session = Depends(get_db)
):
    """Handle shortlink redirects with click tracking and revenue attribution."""
    
    # Find the link by hash
    link = db.query(Link).filter(Link.hash == hash).first()
    if not link:
        logger.warning(f"Shortlink not found: {hash}")
        return {"error": "Link not found"}, 404
    
    # Get or create session ID for tracking
    session_id = request.cookies.get("cf_session")
    if not session_id:
        session_id = hashlib.md5(f"{request.client.host}_{utcnow()}".encode()).hexdigest()[:16]
        response.set_cookie("cf_session", session_id, max_age=86400)  # 24 hours
    
    # Get post information for context
    post = None
    post_id = request.query_params.get("post_id")
    if post_id:
        post = db.query(Post).filter(Post.id == int(post_id)).first()
    
    platform = request.query_params.get("platform", link.platform_hint or "unknown")
    
    # Calculate revenue (EPC-based estimation)
    amount_eur = _calculate_revenue(link)
    
    # Create click event
    metric_event = MetricEvent(
        post_id=int(post_id) if post_id else None,
        platform=platform,
        kind="click",
        value=1,
        session_id=session_id,
        amount_eur=amount_eur,
        timestamp=utcnow(),
        metadata={
            "link_id": link.id,
            "user_agent": request.headers.get("user-agent", ""),
            "referer": request.headers.get("referer", ""),
            "ip": request.client.host
        }
    )
    
    db.add(metric_event)
    db.commit()
    
    # Update Prometheus metrics
    increment_click_metric(platform)
    
    # Build final URL with UTM parameters
    final_url = _build_final_url(link, post_id, platform)
    
    logger.info(f"Shortlink redirect: {hash} -> {final_url} (revenue: €{amount_eur:.3f})")
    
    return RedirectResponse(url=final_url, status_code=302)

def _calculate_revenue(link: Link) -> float:
    """Calculate estimated revenue for this click."""
    # Use link-specific EPC override if available
    if link.epc_override_eur is not None:
        return link.epc_override_eur
    
    # Use default EPC from environment
    default_epc = float(os.getenv("DEFAULT_EPC_EUR", "0.20"))
    return default_epc

def _build_final_url(link: Link, post_id: str = None, platform: str = None) -> str:
    """Build final URL with UTM parameters and tracking."""
    base_url = link.affiliate_url
    
    # Add UTM parameters
    utm_params = []
    if link.utm_params:
        utm_params.append(link.utm_params)
    
    # Add dynamic UTM based on context
    if platform:
        utm_params.append(f"utm_source={platform}")
    if post_id:
        utm_params.append(f"utm_content=post_{post_id}")
    
    # Default tracking
    utm_params.append(f"utm_medium=contentflow")
    utm_params.append(f"utm_campaign=automated")
    
    # Combine URL and parameters
    separator = "&" if "?" in base_url else "?"
    if utm_params:
        final_url = base_url + separator + "&".join(utm_params)
    else:
        final_url = base_url
    
    return final_url