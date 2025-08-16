from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db

router = APIRouter(prefix="/api/byop", tags=["byop"]) 

@router.get("/health")
def byop_health():
    return {"ok": True, "feature": "byop"}

@router.get("/accounts")
def list_byop_accounts(db: Session = Depends(get_db)):
    # Placeholder endpoint to satisfy frontend calls; extend later
    return []
