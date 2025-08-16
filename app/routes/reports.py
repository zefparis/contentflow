from fastapi import APIRouter, Form
from app.schemas import RevenueCalculation, RevenueResult

router = APIRouter()


@router.post("/reports/calculate")
async def calculate_revenue(
    views: int = Form(...),
    ctr: float = Form(...),
    epc: float = Form(...),
    platform: str = Form(...)
):
    """Calculate revenue projections"""
    
    # Calculate metrics
    monthly_clicks = int(views * (ctr / 100))
    monthly_revenue = monthly_clicks * epc
    daily_revenue = monthly_revenue / 30
    weekly_revenue = monthly_revenue / 4.33
    annual_revenue = monthly_revenue * 12
    rpm_revenue = (monthly_revenue / views) * 1000 if views > 0 else 0
    
    result = RevenueResult(
        monthly_revenue=monthly_revenue,
        monthly_clicks=monthly_clicks,
        daily_revenue=daily_revenue,
        weekly_revenue=weekly_revenue,
        annual_revenue=annual_revenue,
        rpm_revenue=rpm_revenue
    )
    
    return {
        "monthly_revenue": f"€{result.monthly_revenue:,.0f}",
        "monthly_clicks": f"{result.monthly_clicks:,}",
        "daily_revenue": f"€{result.daily_revenue:.2f}",
        "weekly_revenue": f"€{result.weekly_revenue:.2f}",
        "annual_revenue": f"€{result.annual_revenue:,.0f}",
        "rpm_revenue": f"€{result.rpm_revenue:.2f}"
    }
