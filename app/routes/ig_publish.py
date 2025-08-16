"""
Routes de publication Instagram Reels via l'API Meta Graph
Gestion complète du workflow: création container → polling → publication
"""

import json
import time
import logging
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import get_session
from app.models import Account
from app.providers.meta_client import (
    ig_create_media, 
    ig_check_creation, 
    ig_publish_media,
    validate_video_url
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ig", tags=["instagram_publish"])

class ReelsPublishRequest(BaseModel):
    """Modèle de requête pour publier un Reel"""
    video_url: str
    caption: str = ""
    share_to_feed: bool = True

def _get_meta_account(db: Session) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
    """Récupère les informations du compte Meta configuré"""
    
    try:
        account = db.query(Account).filter_by(platform="meta_ig", enabled=True).first()
        
        if not account:
            return None, None, None
        
        oauth_data = json.loads(account.oauth_json or "{}")
        
        ig_user_id = oauth_data.get("ig_user_id")
        page_token = oauth_data.get("page_token") 
        
        # Vérifier l'expiration du token
        expires_at = oauth_data.get("user_token_expires_at", 0)
        if expires_at and expires_at < int(time.time()):
            logger.warning("Token Meta expiré")
            return None, None, oauth_data
        
        return ig_user_id, page_token, oauth_data
        
    except Exception as e:
        logger.error(f"Erreur récupération compte Meta: {e}")
        return None, None, None

@router.post("/reels/publish")
def publish_reel(
    request: ReelsPublishRequest,
    db: Session = Depends(get_session)
):
    """
    Publie un Reel Instagram via l'API Meta Graph
    
    Workflow complet:
    1. Validation du compte et des paramètres
    2. Création du container média
    3. Polling du statut jusqu'à FINISHED
    4. Publication du média
    """
    
    # Étape 1: Vérifier la configuration Meta
    ig_user_id, page_token, oauth_data = _get_meta_account(db)
    
    if not ig_user_id or not page_token:
        return JSONResponse(
            {
                "ok": False, 
                "error": "meta_ig_not_connected",
                "message": "Compte Instagram non configuré. Veuillez vous connecter via OAuth."
            }, 
            status_code=400
        )
    
    # Étape 2: Validation des paramètres
    video_url = request.video_url.strip()
    caption = request.caption.strip()
    
    if not video_url:
        return JSONResponse(
            {"ok": False, "error": "video_url_required"}, 
            status_code=400
        )
    
    # Validation optionnelle de l'URL (peut être désactivée pour les URLs internes)
    if not video_url.startswith(('http://', 'https://')):
        return JSONResponse(
            {"ok": False, "error": "invalid_video_url"}, 
            status_code=400
        )
    
    logger.info(f"Début publication Reel: {video_url[:100]}...")
    
    try:
        # Étape 3: Créer le container média
        logger.info("Création du container média Instagram")
        creation_result = ig_create_media(
            ig_user_id=ig_user_id,
            page_token=page_token,
            video_url=video_url,
            caption=caption,
            share_to_feed=request.share_to_feed
        )
        
        if not creation_result.get("ok"):
            logger.error(f"Échec création container: {creation_result}")
            return JSONResponse(creation_result, status_code=400)
        
        creation_id = creation_result.get("id")
        logger.info(f"Container créé: {creation_id}")
        
        # Étape 4: Polling du statut container
        logger.info("Début du polling du statut container")
        deadline = time.time() + 180  # Timeout de 3 minutes
        status_code = "IN_PROGRESS"
        poll_count = 0
        
        while time.time() < deadline:
            poll_count += 1
            
            try:
                status_result = ig_check_creation(creation_id, page_token)
                status_code = status_result.get("status_code") or status_result.get("status", "IN_PROGRESS")
                
                logger.debug(f"Poll #{poll_count}: {status_code}")
                
                if status_code == "FINISHED":
                    logger.info("Container finalisé avec succès")
                    break
                elif status_code == "ERROR":
                    logger.error(f"Erreur lors de la création: {status_result}")
                    return JSONResponse(
                        {
                            "ok": False, 
                            "creation_id": creation_id, 
                            "status": status_result,
                            "error": "container_creation_failed"
                        }, 
                        status_code=400
                    )
                
                # Attendre 3 secondes avant le prochain poll
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Erreur pendant polling: {e}")
                # Continuer le polling malgré les erreurs ponctuelles
                time.sleep(5)
        
        # Vérifier si le timeout a été atteint
        if status_code != "FINISHED":
            logger.error(f"Timeout atteint, statut final: {status_code}")
            return JSONResponse(
                {
                    "ok": False, 
                    "creation_id": creation_id, 
                    "status": status_code, 
                    "error": "timeout_container_creation",
                    "message": f"Le container n'a pas été finalisé dans les temps (statut: {status_code})"
                }, 
                status_code=504
            )
        
        # Étape 5: Publier le média
        logger.info("Publication du média Instagram")
        publish_result = ig_publish_media(ig_user_id, page_token, creation_id)
        
        if not publish_result.get("ok"):
            logger.error(f"Échec publication: {publish_result}")
            return JSONResponse(
                {
                    "ok": False, 
                    "creation_id": creation_id, 
                    **publish_result
                }, 
                status_code=400
            )
        
        media_id = publish_result.get("id")
        logger.info(f"Reel publié avec succès: {media_id}")
        
        # Retourner le succès avec tous les détails
        return {
            "ok": True,
            "creation_id": creation_id,
            "media_id": media_id,
            "ig_user_id": ig_user_id,
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": request.share_to_feed,
            "published_at": int(time.time()),
            "polls_count": poll_count
        }
        
    except Exception as e:
        logger.error(f"Erreur publication Reel: {e}")
        return JSONResponse(
            {
                "ok": False, 
                "error": "publication_failed",
                "message": str(e)
            }, 
            status_code=500
        )

@router.get("/account/status")
def get_account_status(db: Session = Depends(get_session)):
    """Retourne le statut du compte Instagram configuré"""
    
    try:
        ig_user_id, page_token, oauth_data = _get_meta_account(db)
        
        if not ig_user_id:
            return {
                "connected": False,
                "error": "Compte Instagram non configuré"
            }
        
        # Informations du compte
        return {
            "connected": True,
            "ig_user_id": ig_user_id,
            "page_name": oauth_data.get("page_name"),
            "user_name": oauth_data.get("user_info", {}).get("name"),
            "connected_at": oauth_data.get("connected_at"),
            "token_expires_at": oauth_data.get("user_token_expires_at"),
            "days_until_expiry": max(0, (oauth_data.get("user_token_expires_at", 0) - int(time.time())) // 86400)
        }
        
    except Exception as e:
        logger.error(f"Erreur statut compte: {e}")
        return {"connected": False, "error": str(e)}

@router.post("/test/connection")
def test_connection(db: Session = Depends(get_session)):
    """Test la connexion Instagram sans publier de contenu"""
    
    try:
        ig_user_id, page_token, oauth_data = _get_meta_account(db)
        
        if not ig_user_id or not page_token:
            return {
                "ok": False,
                "error": "Compte Instagram non configuré"
            }
        
        # Test simple: vérifier que les tokens sont valides en récupérant les infos du compte
        from app.providers.meta_client import get_account_info
        
        user_token = oauth_data.get("user_token")
        if user_token:
            account_info = get_account_info(user_token)
            
            return {
                "ok": True,
                "message": "Connexion Instagram valide",
                "account_info": account_info,
                "ig_user_id": ig_user_id
            }
        else:
            return {
                "ok": False,
                "error": "Token utilisateur manquant"
            }
            
    except Exception as e:
        logger.error(f"Erreur test connexion: {e}")
        return {
            "ok": False,
            "error": str(e)
        }