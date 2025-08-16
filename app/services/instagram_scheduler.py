"""
Service de planification et refresh automatique des tokens Instagram
Intégration avec le scheduler APScheduler existant
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.db import SessionLocal
from app.models import Account
from app.providers.meta_client import oauth_extend_long_lived

logger = logging.getLogger(__name__)

def refresh_meta_tokens():
    """
    Job de refresh automatique des tokens Meta Instagram
    Exécuté quotidiennement pour éviter l'expiration
    """
    
    logger.info("Début du job refresh tokens Meta")
    
    try:
        db = SessionLocal()
        
        # Chercher les comptes Meta actifs
        accounts = db.query(Account).filter_by(platform="meta_ig", enabled=True).all()
        
        if not accounts:
            logger.info("Aucun compte Meta à traiter")
            return
        
        for account in accounts:
            try:
                oauth_data = json.loads(account.oauth_json or "{}")
                
                user_token = oauth_data.get("user_token")
                expires_at = oauth_data.get("user_token_expires_at", 0)
                
                if not user_token:
                    logger.warning(f"Token manquant pour compte {account.id}")
                    continue
                
                # Calculer les jours restants
                days_remaining = (expires_at - int(time.time())) // 86400
                
                # Refresh si expiration dans moins de 15 jours
                if days_remaining < 15:
                    logger.info(f"Refresh token pour compte {account.id} (expire dans {days_remaining} jours)")
                    
                    try:
                        # Tenter le refresh
                        refreshed_data = oauth_extend_long_lived(user_token)
                        
                        # Mettre à jour les données
                        oauth_data["user_token"] = refreshed_data["access_token"]
                        oauth_data["user_token_expires_at"] = refreshed_data.get("expires_at")
                        oauth_data["last_refresh"] = int(time.time())
                        
                        account.oauth_json = json.dumps(oauth_data)
                        db.commit()
                        
                        new_days = (refreshed_data.get("expires_at", 0) - int(time.time())) // 86400
                        logger.info(f"Token refreshed avec succès pour compte {account.id} (expire dans {new_days} jours)")
                        
                    except Exception as e:
                        logger.error(f"Échec refresh token pour compte {account.id}: {e}")
                        
                        # Si le refresh échoue, marquer le compte comme nécessitant une reconnexion
                        if "Invalid OAuth" in str(e) or "expired" in str(e).lower():
                            oauth_data["refresh_failed"] = True
                            oauth_data["refresh_error"] = str(e)
                            account.oauth_json = json.dumps(oauth_data)
                            db.commit()
                            
                            logger.warning(f"Compte {account.id} nécessite une reconnexion OAuth")
                
                else:
                    logger.debug(f"Token compte {account.id} encore valide ({days_remaining} jours)")
                    
            except Exception as e:
                logger.error(f"Erreur traitement compte {account.id}: {e}")
                continue
        
        db.close()
        logger.info("Job refresh tokens Meta terminé")
        
    except Exception as e:
        logger.error(f"Erreur générale job refresh tokens: {e}")

def check_instagram_health() -> dict:
    """
    Vérifie la santé des connexions Instagram
    Retourne un rapport de statut
    """
    
    try:
        db = SessionLocal()
        
        accounts = db.query(Account).filter_by(platform="meta_ig").all()
        
        total_accounts = len(accounts)
        active_accounts = len([a for a in accounts if a.enabled])
        
        healthy_accounts = 0
        expiring_soon = 0
        expired_accounts = 0
        
        for account in accounts:
            if not account.enabled:
                continue
                
            try:
                oauth_data = json.loads(account.oauth_json or "{}")
                expires_at = oauth_data.get("user_token_expires_at", 0)
                
                if expires_at:
                    days_remaining = (expires_at - int(time.time())) // 86400
                    
                    if days_remaining > 15:
                        healthy_accounts += 1
                    elif days_remaining > 0:
                        expiring_soon += 1
                    else:
                        expired_accounts += 1
                        
            except Exception:
                expired_accounts += 1
        
        db.close()
        
        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts, 
            "healthy_accounts": healthy_accounts,
            "expiring_soon": expiring_soon,
            "expired_accounts": expired_accounts,
            "health_score": (healthy_accounts / max(active_accounts, 1)) * 100
        }
        
    except Exception as e:
        logger.error(f"Erreur check Instagram health: {e}")
        return {
            "error": str(e),
            "health_score": 0
        }

def get_instagram_account_status() -> Optional[dict]:
    """
    Récupère le statut détaillé du compte Instagram principal
    """
    
    try:
        db = SessionLocal()
        
        account = db.query(Account).filter_by(platform="meta_ig", enabled=True).first()
        
        if not account:
            return None
            
        oauth_data = json.loads(account.oauth_json or "{}")
        
        expires_at = oauth_data.get("user_token_expires_at", 0)
        days_remaining = max(0, (expires_at - int(time.time())) // 86400) if expires_at else 0
        
        status = {
            "account_id": account.id,
            "ig_user_id": oauth_data.get("ig_user_id"),
            "page_name": oauth_data.get("page_name"),
            "user_name": oauth_data.get("user_info", {}).get("name"),
            "connected_at": oauth_data.get("connected_at"),
            "last_refresh": oauth_data.get("last_refresh"),
            "token_expires_at": expires_at,
            "days_until_expiry": days_remaining,
            "status": "healthy" if days_remaining > 15 else "expiring" if days_remaining > 0 else "expired",
            "refresh_failed": oauth_data.get("refresh_failed", False),
            "refresh_error": oauth_data.get("refresh_error")
        }
        
        db.close()
        return status
        
    except Exception as e:
        logger.error(f"Erreur get Instagram status: {e}")
        return None

def setup_instagram_scheduler_jobs(scheduler):
    """
    Configure les jobs Instagram dans le scheduler APScheduler
    """
    
    try:
        from apscheduler.triggers.cron import CronTrigger
        
        # Job de refresh quotidien des tokens à 3h15
        scheduler.add_job(
            func=refresh_meta_tokens,
            trigger=CronTrigger(hour=3, minute=15),
            id="instagram_token_refresh",
            name="Refresh tokens Instagram",
            replace_existing=True
        )
        
        logger.info("Jobs Instagram programmés avec succès")
        
    except Exception as e:
        logger.error(f"Erreur configuration jobs Instagram: {e}")