from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, Index, func
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.db import Base
import sqlalchemy as sa


class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(50), nullable=False)  # rss, youtube_cc, stock, serp_youtube, serp_news, serp_trends
    url = Column(String(500), nullable=False)  # For SERP: stores the query string
    params_json = Column(Text, default="{}")  # Provider options (locale, filters, etc.)
    enabled = Column(Boolean, default=True)
    keywords = Column(String(500))  # CSV filter keywords
    categories = Column(String(500))  # CSV categories
    min_duration = Column(Integer, default=10)  # seconds
    language = Column(String(10), default="fr")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assets = relationship("Asset", back_populates="source")


class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"))
    status = Column(String(20), default="new")  # new, ready, failed
    meta_json = Column(Text)
    s3_key = Column(String(500))
    duration = Column(Float)
    lang = Column(String(10))
    phash = Column(String(64), nullable=True, index=True)  # perceptual hash for dedup
    keywords = Column(String(500), index=True)  # extracted keywords
    created_at = Column(DateTime, default=datetime.utcnow)
    
    source = relationship("Source", back_populates="assets")
    posts = relationship("Post", back_populates="asset")


class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    platform = Column(String(50))
    title = Column(Text)
    description = Column(Text)
    shortlink = Column(String(500))
    status = Column(String(20), default="draft")  # draft, queued, posted, failed
    metrics_json = Column(Text)
    language = Column(String(10), index=True)
    hashtags = Column(String(500), index=True)
    ab_group = Column(String(50), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime)
    
    asset = relationship("Asset", back_populates="posts")
    experiments = relationship("Experiment", back_populates="post")
    metric_events = relationship("MetricEvent", back_populates="post")


class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    variant = Column(String(50))  # title:v1, title:v2, etc
    arm_key = Column(String(100), index=True)
    status = Column(String(20), default="active")  # active, completed, paused
    metrics_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    post = relationship("Post", back_populates="experiments")


class MetricEvent(Base):
    __tablename__ = "metric_events"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    platform = Column(String(50), index=True)
    kind = Column(String(50))  # views, clicks, likes, etc.
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text)  # JSON for additional data
    session_id = Column(String(32), nullable=True)  # Session tracking
    amount_eur = Column(Float, default=0.0)  # Revenue amount
    
    # Relationship
    post = relationship("Post", back_populates="metric_events")


class Account(Base):
    __tablename__ = "accounts"

    # Conçu pour être compatible avec les routes ig_oauth/ig_publish
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(100), index=True, nullable=True)
    platform = Column(String(50), index=True, nullable=False)
    token = Column(Text, nullable=True)
    enabled = Column(Boolean, default=False)
    oauth_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)


class Link(Base):
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String(16), unique=True, index=True)  # Short hash for /l/{hash}
    target_url = Column(Text)  # Target URL to redirect to
    platform = Column(String(50), nullable=True)  # Platform origin
    epc_override_eur = Column(Float, nullable=True)  # Override default EPC
    description = Column(Text, nullable=True)  # Description
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(50), index=True)  # ingest, transform, publish, metrics
    status = Column(String(20), default="queued")  # queued, running, completed, failed, dlq
    payload = Column(JSON)  # JSON payload for job
    idempotency_key = Column(String(32), unique=True, index=True)
    attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    dlq_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True)  # feature_flags, denylist_keywords, etc.
    value = Column(Text)  # JSON value
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# --- IA ORCHESTRATOR ---
class AgentState(Base):
    __tablename__ = "agent_state"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    key = Column(String, unique=True, index=True)   # ex: 'ema_ctr', 'ema_epc'
    value_json = Column(Text, nullable=False, default="{}")
    updated_at = Column(DateTime, server_default=sa.func.now(), onupdate=sa.func.now())


class AgentAction(Base):
    __tablename__ = "agent_actions"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    tick_ts = Column(DateTime, server_default=sa.func.now(), index=True)
    kind = Column(String, index=True)   # ex: 'ROUTE_PLATFORM', 'SPAWN_QUERY', 'A_B_PROMOTE', ...
    target = Column(String, nullable=True)   # asset_id | platform | partner_id | rule_key ...
    payload_json = Column(Text, nullable=False, default="{}")
    decision_score = Column(Float, default=0.0)
    executed = Column(Boolean, default=False)
    success = Column(Boolean, default=False)
    error = Column(String, nullable=True)


class Partner(Base):
    __tablename__ = "partners"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, nullable=False, unique=True, index=True)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    withdraw_requests = relationship("WithdrawRequest")


class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    partner_id = Column(String, ForeignKey("partners.id", ondelete="CASCADE"), index=True)
    amount_eur = Column(Float, nullable=False)
    method = Column(String, nullable=False)
    details = Column(String, nullable=True)
    status = Column(String, nullable=False, default="requested")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    partner = relationship("Partner", overlaps="withdraw_requests")


