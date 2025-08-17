import datetime as dt
from app.utils.datetime import utcnow
from sqlalchemy import func
from app.db import SessionLocal
from app.config import settings
from app.models import MetricEvent, WalletEntry, Payout, Assignment, PartnerFlag, Partner
from app.services.pricing import current_offer

def _utcnow(): return utcnow()

def summary():
    db = SessionLocal()
    now = _utcnow()
    d1 = now - dt.timedelta(days=1)
    d7 = now - dt.timedelta(days=7)
    
    try:
        # Clicks / Conv / Revenue
        clicks_7d = db.query(func.count()).select_from(MetricEvent)\
            .filter(MetricEvent.kind=="click", MetricEvent.ts>=d7).scalar() or 0
        conv_7d = db.query(func.count()).select_from(WalletEntry)\
            .filter(WalletEntry.type=="conversion", WalletEntry.status=="confirmed", WalletEntry.created_at>=d7).scalar() or 0
        rev_7d = db.query(func.coalesce(func.sum(WalletEntry.amount_eur),0.0)).select_from(WalletEntry)\
            .filter(WalletEntry.type=="conversion", WalletEntry.status=="confirmed", WalletEntry.created_at>=d7).scalar() or 0.0
        epc_7d = (float(rev_7d) / clicks_7d) if clicks_7d else 0.0

        # Payouts: confirmed/reserve/paid/available (mêmes règles que ledger)
        reserve_cutoff = now - dt.timedelta(days=getattr(settings, "PAYOUT_RELEASE_DAYS", 30))
        confirmed = db.query(func.coalesce(func.sum(WalletEntry.amount_eur),0.0))\
            .filter(WalletEntry.type=="conversion", WalletEntry.status=="confirmed").scalar() or 0.0
        to_reserve = db.query(func.coalesce(func.sum(WalletEntry.amount_eur),0.0))\
            .filter(WalletEntry.type=="conversion", WalletEntry.status=="confirmed", WalletEntry.created_at>reserve_cutoff).scalar() or 0.0
        reserved = to_reserve * float(getattr(settings, "PAYOUT_RESERVE_PCT", 0.30))
        paid = abs(db.query(func.coalesce(func.sum(WalletEntry.amount_eur),0.0))\
            .filter(WalletEntry.type=="payout", WalletEntry.status=="paid").scalar() or 0.0)
        available = max(0.0, confirmed - reserved - paid)

        # Queue publish
        try:
            pending = db.query(func.count()).select_from(Assignment).filter(Assignment.status=="pending").scalar() or 0
            approved = db.query(func.count()).select_from(Assignment).filter(Assignment.status=="approved").scalar() or 0
            failed = db.query(func.count()).select_from(Assignment).filter(Assignment.status=="failed").scalar() or 0
            posted = db.query(func.count()).select_from(Assignment).filter(Assignment.status=="posted").scalar() or 0
        except Exception:
            pending=approved=failed=posted=0

        # Risk / health
        holds = db.query(func.count()).select_from(PartnerFlag).filter(PartnerFlag.flag=="hold").scalar() or 0
        postbacks_24h = db.query(func.count()).select_from(WalletEntry)\
            .filter(WalletEntry.type=="conversion", WalletEntry.created_at>=d1).scalar() or 0

        # Partners actifs (clics 7j)
        partners_active = db.query(func.count(func.distinct(MetricEvent.partner_id)))\
            .filter(MetricEvent.kind=="click", MetricEvent.ts>=d7, MetricEvent.partner_id.isnot(None)).scalar() or 0

        offer = {}
        try:
            offer = current_offer()
        except Exception:
            offer = {"headline_cpc": 0.0, "epc_7d": round(epc_7d,2), "terms": {"mode": "unknown"}}

        return {
            "clicks_7d": int(clicks_7d),
            "conv_7d": int(conv_7d),
            "rev_7d": round(float(rev_7d), 2),
            "epc_7d": round(float(epc_7d), 3),
            "available": round(float(available),2),
            "reserved": round(float(reserved),2),
            "paid": round(float(paid),2),
            "pending": int(pending), "approved": int(approved), "posted": int(posted), "failed": int(failed),
            "holds": int(holds), "postbacks_24h": int(postbacks_24h),
            "partners_active": int(partners_active),
            "offer": offer,
        }
    except Exception as e:
        print(f"Analytics summary error: {e}")
        # Return zero-state fallback
        return {
            "clicks_7d": 0,
            "conv_7d": 0,
            "rev_7d": 0.0,
            "epc_7d": 0.0,
            "available": 0.0,
            "reserved": 0.0,
            "paid": 0.0,
            "pending": 0, "approved": 0, "posted": 0, "failed": 0,
            "holds": 0, "postbacks_24h": 0,
            "partners_active": 0,
            "offer": {"headline_cpc": 0.0, "epc_7d": 0.0, "terms": {"mode": "development"}},
        }
    finally:
        db.close()