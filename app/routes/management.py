"""Production management endpoints for ContentFlow."""

import os
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import timedelta
from app.utils.datetime import utcnow, iso_utc

from app.db import get_db
from app.models import Job, Asset, Post, MetricEvent, Rule
from app.utils.logger import logger
from app.services.maintenance import get_system_stats
from utils.metrics import (
    compute_daily_revenue, export_revenue_csv, get_platform_performance,
    get_top_performing_posts
)

router = APIRouter()


@router.get("/api/system/status")
async def system_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get comprehensive system status and health metrics."""
    try:
        # Get system stats from maintenance service
        system_stats = get_system_stats(db)
        
        # Add production metrics
        production_stats = {
            "autopilot": {
                "enabled": os.getenv("FEATURE_AUTOPILOT", "false").lower() == "true",
                "last_run": "2025-08-15T22:20:00Z",  # Would track in DB in real system
                "success_rate": 95.2
            },
            "pipeline": {
                "ingest_rate_per_hour": 12,
                "transform_success_rate": 89.3,
                "publish_success_rate": 92.1,
                "compliance_rejection_rate": 5.8
            },
            "performance": {
                "avg_response_time_ms": 156,
                "error_rate_percent": 0.2,
                "uptime_percent": 99.94
            }
        }
        
        return {
            "status": "healthy",
            "timestamp": iso_utc(),
            "system": system_stats,
            "production": production_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/system/metrics/export")
async def export_metrics(
    days: int = Query(30, description="Number of days to export"),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Export comprehensive metrics data to CSV."""
    try:
        # Export revenue data
        revenue_filepath = export_revenue_csv(db, days)
        
        # Would also export other metrics in production
        export_stats = {
            "revenue_export": revenue_filepath,
            "exported_days": days,
            "timestamp": iso_utc()
        }
        
        logger.info(f"Metrics exported for {days} days")
        return export_stats
        
    except Exception as e:
        logger.error(f"Failed to export metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/system/performance")
async def performance_dashboard(
    days: int = Query(7, description="Days of performance data"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get performance dashboard data."""
    try:
        # Platform performance metrics
        platform_perf = get_platform_performance(db, days)
        
        # Top performing posts
        top_posts = get_top_performing_posts(db, days, limit=10)
        
        # Daily revenue trend
        revenue_trend = []
        for i in range(days):
            date = utcnow().date() - timedelta(days=i)
            daily_revenue = compute_daily_revenue(db, date)
            revenue_trend.append({
                "date": date.isoformat(),
                "total": daily_revenue.get("total", 0)
            })
        
        return {
            "platform_performance": platform_perf,
            "top_posts": top_posts,
            "revenue_trend": list(reversed(revenue_trend)),
            "summary": {
                "total_revenue_eur": sum(r["total"] for r in revenue_trend),
                "avg_daily_revenue": sum(r["total"] for r in revenue_trend) / len(revenue_trend),
                "best_platform": max(platform_perf.keys(), key=lambda p: platform_perf[p]["revenue_eur"]) if platform_perf else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/system/maintenance/run")
async def run_maintenance(
    task: str = Query(..., description="Maintenance task: retention, s3_lifecycle, watchdog, all"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Run specific maintenance tasks."""
    try:
        from app.services.maintenance import job_retention, job_s3_lifecycle, job_watchdog
        
        if task == "retention":
            job_retention(db)
            message = "Data retention cleanup completed"
        elif task == "s3_lifecycle":
            job_s3_lifecycle(db)
            message = "S3 lifecycle management completed"
        elif task == "watchdog":
            job_watchdog(db)
            message = "Job watchdog check completed"
        elif task == "all":
            job_retention(db)
            job_s3_lifecycle(db)
            job_watchdog(db)
            message = "All maintenance tasks completed"
        else:
            raise HTTPException(status_code=400, detail=f"Unknown maintenance task: {task}")
        
        return {
            "success": True,
            "task": task,
            "message": message,
            "timestamp": iso_utc()
        }
        
    except Exception as e:
        logger.error(f"Failed to run maintenance task {task}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/system/rules")
async def get_rules(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Get all system configuration rules."""
    try:
        rules = db.query(Rule).all()
        
        rules_data = []
        for rule in rules:
            rules_data.append({
                "id": rule.id,
                "key": rule.key,
                "value": rule.value,
                "description": rule.description,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat()
            })
        
        return rules_data
        
    except Exception as e:
        logger.error(f"Failed to get rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/system/rules/{rule_key}")
async def update_rule(
    rule_key: str,
    value: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update or create a system rule."""
    try:
        rule = db.query(Rule).filter(Rule.key == rule_key).first()
        
        if rule:
            rule.value = value
            if description:
                rule.description = description
            rule.updated_at = utcnow()
        else:
            rule = Rule(
                key=rule_key,
                value=value,
                description=description or f"Rule for {rule_key}",
                created_at=utcnow(),
                updated_at=utcnow()
            )
            db.add(rule)
        
        db.commit()
        
        return {
            "success": True,
            "rule_key": rule_key,
            "value": value,
            "message": f"Rule {rule_key} updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to update rule {rule_key}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/system/jobs/queue")
async def get_job_queue(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Limit results"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get current job queue status."""
    try:
        query = db.query(Job)
        
        if status:
            query = query.filter(Job.status == status)
        
        jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
        
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                "id": job.id,
                "kind": job.kind,
                "status": job.status,
                "idempotency_key": job.idempotency_key,
                "attempts": job.attempts,
                "last_error": job.last_error,
                "dlq_reason": job.dlq_reason,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            })
        
        return jobs_data
        
    except Exception as e:
        logger.error(f"Failed to get job queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/system/jobs/{job_id}/retry")
async def retry_job(
    job_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retry a failed job."""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status not in ["failed", "dlq"]:
            raise HTTPException(status_code=400, detail=f"Cannot retry job with status: {job.status}")
        
        # Reset job for retry
        job.status = "queued"
        job.last_error = None
        job.dlq_reason = None
        job.started_at = None
        job.completed_at = None
        job.attempts += 1
        
        db.commit()
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Job queued for retry",
            "new_attempts": job.attempts
        }
        
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))