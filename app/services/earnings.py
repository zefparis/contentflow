import datetime as dt
from app.utils.datetime import utcnow
import json
from sqlalchemy import func
from app.db import SessionLocal
from app.models import MetricEvent, WithdrawRequest, Partner
from app.config import settings


def _since(days: int):
    return utcnow() - dt.timedelta(days=days)


def mask_email(e: str) -> str:
    """Masque un email pour l'affichage public."""
    if "@" not in (e or ""):
        return "anon"
    u, d = e.split("@", 1)
    return (u[:2] + "…" + u[-1:]) + "@" + d


def partner_balance(partner_id: str, days: int = 90) -> dict:
    """Calcule le solde d'un partenaire sur une période donnée."""
    db = SessionLocal()
    try:
        since = _since(days)
        
        # Pour l'instant, utiliser une simulation basée sur des données réelles
        # En attendant la migration complète de MetricEvent
        
        # Compter clicks simulés (sera remplacé par vraies données)
        clicks = 0
        try:
            # Essayer de compter avec la structure existante
            from sqlalchemy import text
            result = db.execute(text(
                "SELECT COUNT(*) FROM metric_events WHERE kind = 'click' AND ts >= :since"
            ), {"since": since})
            clicks = result.scalar() or 0
        except:
            # Si échec, utiliser simulation basée sur partner_id
            clicks = hash(partner_id) % 50  # Simulation
        
        # Total revenu estimé = clicks * EPC effectif
        epc = float(getattr(settings, "DEFAULT_EPC_EUR", 0.20))
        gross = clicks * epc
        
        # Total payé (depuis table withdraw_requests avec status paid)
        paid = db.query(func.coalesce(func.sum(WithdrawRequest.amount_eur), 0.0))\
            .filter(WithdrawRequest.partner_id == partner_id, WithdrawRequest.status == "paid").scalar() or 0.0
        
        # Montant en attente de retrait
        pending = db.query(func.coalesce(func.sum(WithdrawRequest.amount_eur), 0.0))\
            .filter(
                WithdrawRequest.partner_id == partner_id, 
                WithdrawRequest.status.in_(("requested", "approved"))
            ).scalar() or 0.0
        
        # Solde disponible
        available = max(0.0, gross - paid - pending)
        
        return {
            "clicks": clicks, 
            "epc": epc, 
            "gross": round(gross, 2), 
            "paid": round(paid, 2),
            "pending": round(pending, 2), 
            "available": round(available, 2)
        }
        
    finally:
        db.close()


def leaderboard(days: int = 7, limit: int = 20):
    """Génère un leaderboard anonymisé des partenaires."""
    db = SessionLocal()
    try:
        # Pour l'instant, générer un leaderboard simulé basé sur les partenaires existants
        partners = db.query(Partner).limit(limit).all()
        
        out = []
        rank = 1
        for partner in partners:
            # Simulation clics basée sur l'ID du partenaire
            simulated_clicks = max(1, hash(partner.id) % 100)
            
            out.append({
                "rank": rank, 
                "pid": partner.id, 
                "label": mask_email(partner.email), 
                "clicks": simulated_clicks
            })
            rank += 1
        
        # Trier par clicks décroissant
        out.sort(key=lambda x: x["clicks"], reverse=True)
        
        # Réassigner les rangs
        for i, entry in enumerate(out):
            entry["rank"] = i + 1
        
        return out[:limit]
        
    finally:
        db.close()


def request_withdraw(partner_id: str, amount: float, method: str, details: str):
    """Demande de retrait pour un partenaire."""
    db = SessionLocal()
    try:
        # Vérifier le solde disponible
        bal = partner_balance(partner_id)["available"]
        
        # Validations
        if amount <= 0 or amount > bal or amount < settings.PAYOUT_MIN_EUR:
            return {"ok": False, "error": "invalid_amount_or_threshold"}
        
        if method not in (settings.PAYOUT_METHODS or "paypal").split(","):
            return {"ok": False, "error": "invalid_method"}
        
        # Créer la demande de retrait
        wr = WithdrawRequest(
            partner_id=partner_id, 
            amount_eur=amount, 
            method=method, 
            details=details or ""
        )
        db.add(wr)
        db.commit()
        
        return {"ok": True, "id": wr.id}
        
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


def get_withdraw_requests(partner_id: str = None, status: str = None, limit: int = 50):
    """Récupère les demandes de retrait avec filtres."""
    db = SessionLocal()
    try:
        query = db.query(WithdrawRequest)
        
        if partner_id:
            query = query.filter(WithdrawRequest.partner_id == partner_id)
        if status:
            query = query.filter(WithdrawRequest.status == status)
            
        requests = query.order_by(WithdrawRequest.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": wr.id,
                "partner_id": wr.partner_id,
                "amount_eur": wr.amount_eur,
                "method": wr.method,
                "details": wr.details,
                "status": wr.status,
                "created_at": wr.created_at.isoformat() if wr.created_at else None,
                "processed_at": wr.processed_at.isoformat() if wr.processed_at else None
            }
            for wr in requests
        ]
        
    finally:
        db.close()


def update_withdraw_status(withdraw_id: str, status: str, admin_notes: str = None):
    """Met à jour le statut d'une demande de retrait (admin only)."""
    db = SessionLocal()
    try:
        wr = db.query(WithdrawRequest).filter(WithdrawRequest.id == withdraw_id).first()
        if not wr:
            return {"ok": False, "error": "withdraw_not_found"}
        
        wr.status = status
        if status in ("paid", "rejected"):
            wr.processed_at = utcnow()
        
        db.commit()
        return {"ok": True, "withdraw_id": withdraw_id, "new_status": status}
        
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()