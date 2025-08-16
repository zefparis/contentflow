from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Asset
from app.services.assets import transform_asset

router = APIRouter()


@router.get("/assets")
async def list_assets(db: Session = Depends(get_db)):
    """List all assets"""
    assets = db.query(Asset).order_by(Asset.created_at.desc()).limit(100).all()
    return [
        {
            "id": asset.id,
            "source_id": asset.source_id,
            "status": asset.status,
            "s3_key": asset.s3_key,
            "duration": asset.duration,
            "created_at": asset.created_at.isoformat()
        }
        for asset in assets
    ]


@router.post("/assets/{asset_id}/transform")
async def transform_asset_endpoint(asset_id: int, db: Session = Depends(get_db)):
    """Transform a specific asset"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    success = await transform_asset(db, asset)
    
    return {
        "success": success,
        "status": asset.status,
        "message": f"Asset {asset_id} transformation {'completed' if success else 'failed'}"
    }
