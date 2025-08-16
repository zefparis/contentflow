"""Health and metrics endpoints for production monitoring."""

import time
import psutil
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.db import get_db
from app.models import Job, Post, MetricEvent

router = APIRouter()

# Prometheus metrics
cf_jobs_total = Counter('cf_jobs_total', 'Total ContentFlow jobs processed', ['kind', 'status'])
cf_posts_published_total = Counter('cf_posts_published_total', 'Total posts published', ['platform'])
cf_clicks_total = Counter('cf_clicks_total', 'Total link clicks', ['platform'])
cf_request_duration = Histogram('cf_request_duration_seconds', 'Request duration')

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0"
    }

@router.get("/health/db")
async def health_db(db: Session = Depends(get_db)):
    """Database health check."""
    try:
        # Simple query to test DB connectivity
        job_count = db.query(Job).count()
        return {
            "status": "healthy",
            "database": "connected",
            "total_jobs": job_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    # Update metrics from database
    try:
        # This is a lightweight way to expose metrics without heavy DB queries
        # In production, these would be updated by the actual job processes
        pass
    except Exception:
        # Fail silently to not break metrics collection
        pass
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/health/system")
async def system_health():
    """System resource health check."""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "status": "healthy",
            "resources": {
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "cpu_percent": cpu_percent
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Helper functions for incrementing metrics
def increment_job_metric(kind: str, status: str):
    """Increment job counter metric."""
    cf_jobs_total.labels(kind=kind, status=status).inc()

def increment_publish_metric(platform: str):
    """Increment publish counter metric."""
    cf_posts_published_total.labels(platform=platform).inc()

def increment_click_metric(platform: str):
    """Increment click counter metric."""
    cf_clicks_total.labels(platform=platform).inc()