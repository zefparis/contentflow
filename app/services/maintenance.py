"""Maintenance jobs for retention, cleanup, and system health."""

import os
from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import Asset, Job, MetricEvent
from app.utils.logger import logger
from app.utils.datetime import utcnow, iso_utc
from app.utils.jobs import with_job, get_retry_decorator

def job_retention(db: Session):
    """Clean up old data according to retention policies."""
    logger.info("Starting data retention cleanup")
    
    # Clean up failed assets older than 7 days
    cutoff_failed = utcnow() - timedelta(days=7)
    failed_assets = db.query(Asset).filter(
        Asset.status == "failed",
        Asset.created_at < cutoff_failed
    ).all()
    
    for asset in failed_assets:
        logger.info(f"Deleting failed asset {asset.id}")
        db.delete(asset)
    
    # Clean up old jobs older than 30 days
    cutoff_jobs = utcnow() - timedelta(days=30)
    old_jobs = db.query(Job).filter(
        Job.created_at < cutoff_jobs
    ).all()
    
    for job in old_jobs:
        logger.info(f"Deleting old job {job.id}")
        db.delete(job)
    
    # Clean up old metric events older than 90 days (keep recent for analytics)
    cutoff_metrics = utcnow() - timedelta(days=90)
    old_metrics_count = db.query(MetricEvent).filter(
        MetricEvent.timestamp < cutoff_metrics
    ).count()
    
    if old_metrics_count > 0:
        logger.info(f"Deleting {old_metrics_count} old metric events")
        db.query(MetricEvent).filter(
            MetricEvent.timestamp < cutoff_metrics
        ).delete(synchronize_session=False)
    
    # Clean up completed jobs older than 14 days
    cutoff_jobs = utcnow() - timedelta(days=14)
    old_jobs_count = db.query(Job).filter(
        Job.status == "completed",
        Job.completed_at < cutoff_jobs
    ).count()
    
    if old_jobs_count > 0:
        logger.info(f"Deleting {old_jobs_count} old completed jobs")
        db.query(Job).filter(
            Job.status == "completed",
            Job.completed_at < cutoff_jobs
        ).delete(synchronize_session=False)
    
    db.commit()
    
    logger.info(f"Retention cleanup completed: {len(failed_assets)} assets, {old_metrics_count} metrics, {old_jobs_count} jobs")

@get_retry_decorator("maintenance")
def job_s3_lifecycle(db: Session):
    """Simulate S3 lifecycle management for cost optimization."""
    with with_job(db, "s3_lifecycle", {"action": "lifecycle"}) as job_id:
        logger.info("Starting S3 lifecycle management")
        
        # Find assets older than 30 days that are posted
        cutoff_date = utcnow() - timedelta(days=30)
        old_assets = db.query(Asset).filter(
            Asset.created_at < cutoff_date,
            Asset.status == "ready",
            Asset.s3_key.isnot(None)
        ).all()
        
        for asset in old_assets:
            # In production, this would use boto3 to move to infrequent access storage
            # For now, we simulate by adding metadata
            logger.info(f"Simulating S3 lifecycle for asset {asset.id}: {asset.s3_key}")
            
            # Add lifecycle tag (simulated)
            if asset.meta_json:
                import json
                meta = json.loads(asset.meta_json)
            else:
                meta = {}
            
            meta["s3_storage_class"] = "infrequent_access"
            meta["lifecycle_moved_at"] = iso_utc()
            asset.meta_json = json.dumps(meta)
        
        db.commit()
        
        logger.info(f"S3 lifecycle completed for {len(old_assets)} assets")

@get_retry_decorator("maintenance")
def job_watchdog(db: Session):
    """Watchdog to detect and handle stuck jobs."""
    with with_job(db, "watchdog", {"action": "check_stuck"}) as job_id:
        logger.info("Starting job watchdog check")
        
        # Find jobs that have been running for more than 30 minutes
        stuck_threshold = utcnow() - timedelta(minutes=30)
        stuck_jobs = db.query(Job).filter(
            Job.status == "running",
            Job.started_at < stuck_threshold
        ).all()
        
        for job in stuck_jobs:
            logger.warning(f"Found stuck job {job.id} ({job.kind}) running since {job.started_at}")
            
            # Move to DLQ with reason
            job.status = "dlq"
            job.dlq_reason = f"Stuck for {utcnow() - job.started_at}"
            job.completed_at = utcnow()
            
            # Could also restart certain types of jobs automatically
            if job.kind in ["ingest", "metrics"] and job.attempts < 2:
                logger.info(f"Auto-requeuing stuck {job.kind} job {job.id}")
                # Create new job with same payload
                import json
                from app.utils.jobs import idempotency_key
                
                payload = json.loads(job.payload) if job.payload else {}
                new_job = Job(
                    kind=job.kind,
                    status="queued",
                    payload=job.payload,
                    idempotency_key=idempotency_key(payload) + "_retry",
                    attempts=job.attempts + 1,
                    created_at=utcnow()
                )
                db.add(new_job)
        
        db.commit()
        
        logger.info(f"Watchdog completed: {len(stuck_jobs)} stuck jobs handled")

def get_system_stats(db: Session) -> dict:
    """Get system health statistics for monitoring."""
    try:
        stats = {
            "database": {
                "total_assets": db.query(Asset).count(),
                "ready_assets": db.query(Asset).filter(Asset.status == "ready").count(),
                "failed_assets": db.query(Asset).filter(Asset.status == "failed").count(),
                "pending_jobs": db.query(Job).filter(Job.status.in_(["queued", "running"])).count(),
                "dlq_jobs": db.query(Job).filter(Job.status == "dlq").count(),
            },
            "metrics": {
                "events_last_24h": db.query(MetricEvent).filter(
                    MetricEvent.timestamp > utcnow() - timedelta(hours=24)
                ).count(),
                "total_revenue_eur": db.execute(
                    text("SELECT COALESCE(SUM(amount_eur), 0) FROM metric_events WHERE amount_eur > 0")
                ).scalar(),
            },
            "maintenance": {
                "last_retention": _get_last_job_time(db, "retention"),
                "last_watchdog": _get_last_job_time(db, "watchdog"),
                "last_s3_lifecycle": _get_last_job_time(db, "s3_lifecycle"),
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        return {"error": str(e)}

def _get_last_job_time(db: Session, job_kind: str) -> str:
    """Get the timestamp of the last completed job of a given kind."""
    last_job = db.query(Job).filter(
        Job.kind == job_kind,
        Job.status == "completed"
    ).order_by(Job.completed_at.desc()).first()
    
    if last_job and last_job.completed_at:
        return last_job.completed_at.isoformat()
    return "never"