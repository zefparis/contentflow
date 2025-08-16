from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import Asset, Post, Run

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard page"""
    # Get KPI data
    assets_new = db.query(Asset).filter(Asset.status == "new").count()
    assets_ready = db.query(Asset).filter(Asset.status == "ready").count()
    posts_queued = db.query(Post).filter(Post.status == "queued").count()
    posts_published = db.query(Post).filter(Post.status == "posted").count()
    
    # Get recent runs
    recent_runs = db.query(Run).order_by(Run.created_at.desc()).limit(10).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "assets_new": assets_new,
        "assets_ready": assets_ready,
        "posts_queued": posts_queued,
        "posts_published": posts_published,
        "recent_runs": recent_runs
    })


@router.get("/assets")
async def assets_page(request: Request, db: Session = Depends(get_db)):
    """Assets management page"""
    assets = db.query(Asset).order_by(Asset.created_at.desc()).limit(50).all()
    return templates.TemplateResponse("assets.html", {
        "request": request,
        "assets": assets
    })


@router.get("/composer")
async def composer_page(request: Request, db: Session = Depends(get_db)):
    """Content composer page"""
    posts = db.query(Post).filter(Post.status.in_(["draft", "queued"])).all()
    return templates.TemplateResponse("composer.html", {
        "request": request,
        "posts": posts
    })


@router.get("/scheduler")
async def scheduler_page(request: Request):
    """Scheduler page"""
    return templates.TemplateResponse("scheduler.html", {
        "request": request
    })


@router.get("/runs")
async def runs_page(request: Request, db: Session = Depends(get_db)):
    """Job runs page"""
    runs = db.query(Run).order_by(Run.created_at.desc()).limit(100).all()
    return templates.TemplateResponse("runs.html", {
        "request": request,
        "runs": runs
    })


@router.get("/reports")
async def reports_page(request: Request):
    """Reports page"""
    return templates.TemplateResponse("reports.html", {
        "request": request
    })
