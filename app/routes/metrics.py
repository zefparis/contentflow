from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db import get_db
from utils.metrics import (
    get_revenue_summary, 
    get_platform_performance, 
    aggregate_metrics_by_day,
    export_metrics_csv,
    track_click_event
)

router = APIRouter()

@router.get("/metrics/revenue")
async def get_revenue_metrics(days: int = 30, db: Session = Depends(get_db)):
    """Get revenue summary for specified period."""
    try:
        summary = get_revenue_summary(days)
        return {"success": True, "data": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/platforms")
async def get_platform_metrics(db: Session = Depends(get_db)):
    """Get performance breakdown by platform."""
    try:
        performance = get_platform_performance()
        return {"success": True, "data": performance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/daily")
async def get_daily_metrics(days: int = 7, db: Session = Depends(get_db)):
    """Get daily aggregated metrics."""
    try:
        daily_data = aggregate_metrics_by_day(days)
        return {"success": True, "data": daily_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/export")
async def export_metrics(days: int = 30, db: Session = Depends(get_db)):
    """Export metrics as CSV."""
    try:
        csv_content = export_metrics_csv(days)
        return {"success": True, "csv": csv_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics/click/{shortlink_hash}")
async def track_click(shortlink_hash: str, meta: Dict[str, Any] = None):
    """Track a click event from shortlink."""
    try:
        success = track_click_event(shortlink_hash, meta or {})
        if success:
            return {"success": True, "message": "Click tracked"}
        else:
            raise HTTPException(status_code=404, detail="Shortlink not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))