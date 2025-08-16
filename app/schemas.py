from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class AssetBase(BaseModel):
    source_id: int
    status: str = "new"
    meta_json: Optional[str] = None
    s3_key: Optional[str] = None
    duration: Optional[float] = None
    lang: Optional[str] = None


class Asset(AssetBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PostBase(BaseModel):
    asset_id: int
    platform: str
    title: Optional[str] = None
    description: Optional[str] = None
    shortlink: Optional[str] = None
    status: str = "draft"
    metrics_json: Optional[str] = None


class Post(PostBase):
    id: int
    created_at: datetime
    posted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RunBase(BaseModel):
    kind: str
    status: str = "running"
    logs: Optional[str] = None


class Run(RunBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RevenueCalculation(BaseModel):
    views: int
    ctr: float
    epc: float
    platform: str = "mixed"


class RevenueResult(BaseModel):
    monthly_revenue: float
    monthly_clicks: int
    daily_revenue: float
    weekly_revenue: float
    annual_revenue: float
    rpm_revenue: float
