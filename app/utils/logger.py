"""JSON logging with request tracking for production."""

import json
import uuid
import logging
from typing import Optional, Dict, Any
from contextvars import ContextVar
from app.utils.datetime import iso_utc

# Context variables for request tracking
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
job_id_ctx: ContextVar[Optional[int]] = ContextVar('job_id', default=None)
post_id_ctx: ContextVar[Optional[int]] = ContextVar('post_id', default=None)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            'timestamp': iso_utc(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context if available
        if request_id_ctx.get():
            log_data['request_id'] = request_id_ctx.get()
        if job_id_ctx.get():
            log_data['job_id'] = job_id_ctx.get()
        if post_id_ctx.get():
            log_data['post_id'] = post_id_ctx.get()
            
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
            
        return json.dumps(log_data)

def setup_logger(name: str = "contentflow") -> logging.Logger:
    """Setup JSON logger for the application."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    return logger

def set_request_context(request_id: Optional[str] = None):
    """Set request context for logging."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_ctx.set(request_id)
    return request_id

def set_job_context(job_id: int):
    """Set job context for logging."""
    job_id_ctx.set(job_id)

def set_post_context(post_id: int):
    """Set post context for logging."""
    post_id_ctx.set(post_id)

def clear_context():
    """Clear all context variables."""
    request_id_ctx.set(None)
    job_id_ctx.set(None)
    post_id_ctx.set(None)

def log_with_context(logger: logging.Logger, level: str, message: str, **extra):
    """Log message with current context and extra fields."""
    getattr(logger, level.lower())(message, extra={'extra': extra})

# Global logger instance
logger = setup_logger()