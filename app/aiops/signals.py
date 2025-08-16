import datetime as dt
import json
import math
from collections import defaultdict
from sqlalchemy import func
from app.db import SessionLocal
from app.models import MetricEvent, Post, Asset, Job


def _since(days: int) -> dt.datetime:
    return dt.datetime.utcnow() - dt.timedelta(days=days)


def fetch_kpis(lookback_days: int = 7) -> dict:
    """Collecte les KPIs sur une fenêtre glissante."""
    db = SessionLocal()
    since = _since(lookback_days)
    
    res = {
        "by_platform": defaultdict(lambda: {"views": 0, "clicks": 0, "revenue": 0.0}),
        "global": {"views": 0, "clicks": 0, "revenue": 0.0, "ctr": 0.0, "epc": 0.0}
    }
    
    try:
        # Requête views par plateforme
        qv = db.query(MetricEvent.platform, func.count().label("views")).filter(
            MetricEvent.kind == "view", 
            MetricEvent.timestamp >= since
        ).group_by(MetricEvent.platform).all()
        
        # Requête clicks + revenue par plateforme
        qc = db.query(
            MetricEvent.platform, 
            func.count().label("clicks"), 
            func.coalesce(func.sum(MetricEvent.amount_eur), 0.0).label("amount")
        ).filter(
            MetricEvent.kind == "click", 
            MetricEvent.timestamp >= since
        ).group_by(MetricEvent.platform).all()
        
        views_by = {p: v for p, v in qv}
        
        for p, clicks, amount in qc:
            res["by_platform"][p]["clicks"] += clicks
            res["by_platform"][p]["revenue"] += float(amount or 0.0)
        
        for p, v in views_by.items():
            res["by_platform"][p]["views"] += v
        
        # Agrégation globale
        for p, row in res["by_platform"].items():
            res["global"]["views"] += row["views"]
            res["global"]["clicks"] += row["clicks"]
            res["global"]["revenue"] += row["revenue"]
        
        res["global"]["ctr"] = (res["global"]["clicks"] / max(1, res["global"]["views"]))
        res["global"]["epc"] = (res["global"]["revenue"] / max(1, res["global"]["clicks"])) if res["global"]["clicks"] > 0 else 0.0
        
    except Exception as e:
        print(f"Error fetching KPIs: {e}")
    finally:
        db.close()
    
    return res


def ready_assets(limit: int = 50):
    """Retourne les assets prêts pour publication."""
    db = SessionLocal()
    try:
        return db.query(Asset).filter(Asset.status == "ready").order_by(Asset.created_at.desc()).limit(limit).all()
    finally:
        db.close()


def bottlenecks() -> dict:
    """Retourne un aperçu des files: assets new/ready, posts queued, failed last 24h."""
    db = SessionLocal()
    since = _since(1)
    
    try:
        return {
            "assets_new": db.query(Asset).filter(Asset.status == "new").count(),
            "assets_ready": db.query(Asset).filter(Asset.status == "ready").count(),
            "posts_queued": db.query(Post).filter(Post.status == "queued").count(),
            "posts_failed_24h": db.query(Post).filter(Post.status == "failed", Post.created_at >= since).count(),
            "jobs_running": db.query(Job).filter(Job.status == "running").count(),
            "jobs_failed_24h": db.query(Job).filter(Job.status == "failed", Job.created_at >= since).count(),
        }
    finally:
        db.close()