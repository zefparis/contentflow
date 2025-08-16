from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db import get_db
from app.models import Job
from app.services.scheduler import (
    run_job_by_kind, 
    get_scheduler_status,
    get_job_priorities,
    job_ingest,
    job_transform,
    job_publish,
    job_metrics
)
from app.utils.logger import logger

router = APIRouter()


@router.get("/jobs", response_model=List[Dict[str, Any]])
async def list_jobs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List recent jobs with their status"""
    jobs = db.query(Job).offset(skip).limit(limit).order_by(Job.created_at.desc()).all()
    
    return [
        {
            "id": job.id,
            "kind": job.kind,
            "status": job.status,
            "created_at": job.created_at,
            "attempts": job.attempts,
            "last_error": job.last_error,
        }
        for job in jobs
    ]


@router.post("/jobs/{job_kind}/run")
async def trigger_job(job_kind: str, background_tasks: BackgroundTasks):
    """Manually trigger a job"""
    
    def run_job():
        try:
            result = run_job_by_kind(job_kind)
            logger.info(f"Job {job_kind} completed: {result}")
        except Exception as e:
            logger.error(f"Job {job_kind} failed: {e}")
    
    background_tasks.add_task(run_job)
    
    return {"message": f"Job {job_kind} triggered", "status": "running"}


@router.get("/jobs/status")
async def jobs_status():
    """Get scheduler status"""
    return get_scheduler_status()


@router.get("/jobs/available")
async def get_available_jobs():
    """Get list of available job types"""
    try:
        jobs = get_job_priorities()
        return {"success": True, "data": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/ingest")
async def run_ingest_job():
    """Manually trigger ingest job"""
    try:
        result = job_ingest()
        return {"message": "Ingest job completed", "success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/transform")
async def run_transform_job():
    """Manually trigger transform job"""
    try:
        result = job_transform()
        return {"message": "Transform job completed", "success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/publish")
async def run_publish_job():
    """Manually trigger publish job"""
    try:
        result = job_publish()
        return {"message": "Publish job completed", "success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/metrics")
async def run_metrics_job():
    """Manually trigger metrics collection job"""
    try:
        result = job_metrics()
        return {"message": "Metrics job completed", "success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
