"""Job management with idempotency, retry, and DLQ support."""

import hashlib
import json
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Callable, Optional
from filelock import FileLock
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy.orm import Session

from app.models import Job
from app.utils.logger import logger, set_job_context
from app.routes.health import increment_job_metric
import os

def idempotency_key(payload: Dict[str, Any]) -> str:
    """Generate stable hash for job idempotency."""
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()[:16]

@contextmanager
def with_job(db: Session, kind: str, payload: Dict[str, Any]):
    """Context manager for job lifecycle with idempotency."""
    idem_key = idempotency_key(payload)
    
    # Check if job already completed
    existing = db.query(Job).filter(
        Job.kind == kind,
        Job.idempotency_key == idem_key,
        Job.status == "completed"
    ).first()
    
    if existing:
        logger.info(f"Job {kind} already completed with key {idem_key}")
        yield existing.id
        return
    
    # Create new job
    job = Job(
        kind=kind,
        status="queued",
        payload=json.dumps(payload),
        idempotency_key=idem_key,
        created_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    
    set_job_context(job.id)
    increment_job_metric(kind, "started")
    
    try:
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Starting job {job.id} ({kind})")
        yield job.id
        
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        increment_job_metric(kind, "completed")
        logger.info(f"Completed job {job.id} ({kind})")
        
    except Exception as e:
        job.status = "failed"
        job.last_error = str(e)
        job.attempts = (job.attempts or 0) + 1
        job.completed_at = datetime.utcnow()
        db.commit()
        
        increment_job_metric(kind, "failed")
        logger.error(f"Failed job {job.id} ({kind}): {e}")
        
        # Send to DLQ if max attempts reached
        if job.attempts >= int(os.getenv("MAX_JOB_ATTEMPTS", "3")):
            dead_letter(db, job)
        
        raise

def dead_letter(db: Session, job: Job):
    """Move job to dead letter queue."""
    job.status = "dlq"
    job.dlq_reason = f"Max attempts ({job.attempts}) reached"
    db.commit()
    
    logger.warning(f"Job {job.id} moved to DLQ: {job.dlq_reason}")
    increment_job_metric(job.kind, "dlq")

def with_file_lock(lock_key: str):
    """Decorator for file-based locking."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            lock_file = f"/tmp/contentflow_{lock_key}.lock"
            with FileLock(lock_file, timeout=300):  # 5 min timeout
                return func(*args, **kwargs)
        return wrapper
    return decorator

def get_retry_decorator(job_kind: str):
    """Get retry decorator with exponential backoff."""
    max_attempts = int(os.getenv(f"MAX_RETRY_{job_kind.upper()}", "3"))
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True
    )

def check_rate_limit(platform: str) -> bool:
    """Check if platform rate limit allows operation."""
    rate_limit_key = f"RL_{platform.upper()}_PMIN"
    max_per_minute = int(os.getenv(rate_limit_key, "5"))
    
    # Simple in-memory rate limiting (in production, use Redis)
    # For now, just log and return True
    logger.info(f"Rate limit check for {platform}: {max_per_minute}/min")
    return True

def should_backoff_platform(platform: str) -> bool:
    """Check if platform needs backoff due to quota limits."""
    # Check for recent 429/403 errors (simplified)
    # In production, this would check error logs or Redis cache
    return False