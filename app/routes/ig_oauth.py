"""
Routes OAuth Instagram pour l'authentification Meta et configuration des comptes
"""

import json
import time
import secrets
import logging
from typing import Dict, Optional

from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Account
from app.providers.meta_client import (
    oauth_start_url, 
    oauth_exchange_code, 
    oauth_extend_long_lived, 
    list_pages, 
    get_ig_user_id,
    get_account_info
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ig/oauth", tags=["instagram_oauth"])

@router.get("/start")
def ig_oauth_start():
    """Démarre le flux OAuth Instagram/Facebook"""
    
    # Vérifier que les variables d'environnement sont configurées
    if not settings.META_APP_ID or not settings.META_APP_SECRET:
        return JSONResponse(
            {"error": "Configuration Meta incomplète. Veuillez configurer META_APP_ID et META_APP_SECRET."},
            status_code=400
        )
    
    try:
        # Générer un state unique pour sécuriser OAuth
        state = secrets.token_urlsafe(16)
        oauth_url = oauth_start_url(state)
        
        logger.info("Redirection vers OAuth Facebook")
        return RedirectResponse(oauth_url)
        
    except Exception as e:
        logger.error(f"Erreur démarrage OAuth: {e}")
        return JSONResponse(
            {"error": f"Erreur démarrage OAuth: {str(e)}"},
            status_code=500
        )

@router.get("/callback")
def ig_oauth_callback(
    code: str = Query(..., description="Code d'autorisation OAuth"),
    state: Optional[str] = Query(None, description="State de sécurité"),
    error: Optional[str] = Query(None, description="Erreur OAuth"),
    db: Session = Depends(get_session)
):
    """Callback OAuth - traite la réponse de Facebook"""
    
    # Vérifier s'il y a une erreur OAuth
    if error:
        logger.error(f"Erreur OAuth reçue: {error}")
        return HTMLResponse(
            f"<h3>Erreur d'authentification: {error}</h3><a href='/settings'>Retour</a>",
            status_code=400
        )
    
    try:
        # Étape 1: Échanger le code contre un token court
        logger.info("Échange du code OAuth contre token court")
        short_token_data = oauth_exchange_code(code)
        short_token = short_token_data["access_token"]
        
        # Étape 2: Convertir en token long-lived (60 jours)
        logger.info("Conversion en token long-lived")
        long_token_data = oauth_extend_long_lived(short_token)
        user_token = long_token_data["access_token"]
        token_expires_at = long_token_data.get("expires_at")
        
        # Étape 3: Récupérer les pages Facebook de l'utilisateur
        logger.info("Récupération des pages Facebook")
        pages = list_pages(user_token)
        
        if not pages:
            return HTMLResponse(
                "<h3>❌ Aucune page Facebook trouvée</h3>"
                "<p>Vous devez avoir au moins une page Facebook pour utiliser l'API Instagram.</p>"
                "<a href='/settings'>Retour</a>",
                status_code=400
            )
        
        # Prendre la première page (dans une interface complète, on laisserait l'utilisateur choisir)
        page = pages[0]
        page_id = page["id"]
        page_token = page["access_token"]
        page_name = page.get("name", "Page sans nom")
        
        logger.info(f"Page sélectionnée: {page_name} (ID: {page_id})")
        
        # Étape 4: Récupérer l'ID du compte Instagram Business
        logger.info("Récupération de l'ID Instagram Business")
        ig_user_id = get_ig_user_id(page_id, page_token)
        
        if not ig_user_id:
            return HTMLResponse(
                f"<h3>❌ Aucun compte Instagram Business lié</h3>"
                f"<p>La page '{page_name}' n'a pas de compte Instagram Business connecté.</p>"
                f"<p>Veuillez connecter un compte Instagram Business à votre page Facebook.</p>"
                "<a href='/settings'>Retour</a>",
                status_code=400
            )
        
        # Étape 5: Récupérer les infos utilisateur
        user_info = get_account_info(user_token)
        
        # Étape 6: Sauvegarder en base de données
        logger.info("Sauvegarde des tokens en base de données")
        
        # Chercher un compte Meta existant ou en créer un nouveau
        account = db.query(Account).filter_by(platform="meta_ig").first()
        
        if not account:
            from uuid import uuid4
            account = Account(
                id=str(uuid4()), 
                platform="meta_ig", 
                enabled=True
            )
            db.add(account)
        
        # Préparer les données OAuth à sauvegarder
        oauth_data = {
            "user_token": user_token,
            "user_token_expires_at": token_expires_at,
            "page_id": page_id,
            "page_token": page_token,
            "page_name": page_name,
            "ig_user_id": ig_user_id,
            "user_info": user_info,
            "connected_at": int(time.time()),
            "updated_at": int(time.time())
        }
        
        account.oauth_json = json.dumps(oauth_data)
        account.enabled = True
        
        db.commit()
        
        logger.info(f"Compte Instagram connecté avec succès: {ig_user_id}")
        
        return HTMLResponse(f"""
        <html>
        <head><title>Instagram Connecté</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
            <h2>✅ Instagram connecté avec succès!</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Informations du compte:</h3>
                <ul>
                    <li><strong>Utilisateur:</strong> {user_info.get('name', 'N/A')}</li>
                    <li><strong>Page Facebook:</strong> {page_name}</li>
                    <li><strong>Instagram ID:</strong> {ig_user_id}</li>
                    <li><strong>Token expire:</strong> Dans {(token_expires_at - int(time.time())) // 86400} jours</li>
                </ul>
            </div>
            <p>Votre compte Instagram est maintenant configuré pour la publication automatique de Reels via ContentFlow.</p>
            <a href="/settings" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                Retour aux paramètres
            </a>
        </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"Erreur callback OAuth: {e}")
        return HTMLResponse(
            f"<h3>❌ Erreur lors de la connexion</h3>"
            f"<p>Détails: {str(e)}</p>"
            "<a href='/settings'>Retour</a>",
            status_code=500
        )

@router.get("/status")
def ig_oauth_status(db: Session = Depends(get_session)):
    """Retourne le statut de la connexion Instagram"""
    
    try:
        account = db.query(Account).filter_by(platform="meta_ig", enabled=True).first()
        
        if not account:
            return {
                "connected": False,
                "error": "Aucun compte Instagram configuré"
            }
        
        oauth_data = json.loads(account.oauth_json or "{}")
        
        # Vérifier l'expiration du token
        expires_at = oauth_data.get("user_token_expires_at", 0)
        now = int(time.time())
        days_until_expiry = (expires_at - now) // 86400 if expires_at > now else 0
        
        return {
            "connected": True,
            "page_name": oauth_data.get("page_name"),
            "ig_user_id": oauth_data.get("ig_user_id"),
            "user_name": oauth_data.get("user_info", {}).get("name"),
            "connected_at": oauth_data.get("connected_at"),
            "token_expires_in_days": days_until_expiry,
            "token_valid": days_until_expiry > 0
        }
        
    except Exception as e:
        logger.error(f"Erreur vérification statut Instagram: {e}")
        return {
            "connected": False,
            "error": str(e)
        }

@router.post("/disconnect")
def ig_oauth_disconnect(db: Session = Depends(get_session)):
    """Déconnecte le compte Instagram"""
    
    try:
        account = db.query(Account).filter_by(platform="meta_ig").first()
        
        if account:
            account.enabled = False
            account.oauth_json = "{}"
            db.commit()
            
            logger.info("Compte Instagram déconnecté")
            return {"success": True, "message": "Compte Instagram déconnecté"}
        else:
            return {"success": False, "message": "Aucun compte à déconnecter"}
            
    except Exception as e:
        logger.error(f"Erreur déconnexion Instagram: {e}")
        return {"success": False, "error": str(e)}