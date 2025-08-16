"""
Client Meta pour l'intégration Instagram Graph API
Gestion OAuth Facebook, récupération tokens long-lived, publication Reels
"""

import time
import json
import httpx
import urllib.parse
import logging
from typing import Dict, List, Optional, Union

from app.config import settings

logger = logging.getLogger(__name__)

def get_base_url() -> str:
    """Retourne l'URL de base de l'API Graph"""
    return settings.META_BASE

def oauth_start_url(state: str) -> str:
    """Génère l'URL de démarrage OAuth Facebook"""
    
    if not settings.META_APP_ID or not settings.META_REDIRECT_URL:
        raise ValueError("META_APP_ID et META_REDIRECT_URL requis pour OAuth")
    
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": settings.META_REDIRECT_URL,
        "response_type": "code",
        "scope": settings.META_SCOPES,
        "state": state
    }
    
    query_string = urllib.parse.urlencode(params)
    return f"https://www.facebook.com/{settings.META_GRAPH_VERSION}/dialog/oauth?{query_string}"

def oauth_exchange_code(code: str) -> Dict:
    """Échange le code OAuth contre un access token court"""
    
    params = {
        "client_id": settings.META_APP_ID,
        "client_secret": settings.META_APP_SECRET,
        "redirect_uri": settings.META_REDIRECT_URL,
        "code": code
    }
    
    try:
        response = httpx.get(f"{get_base_url()}/oauth/access_token", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        # Ajouter timestamps pour tracking expiration
        data["obtained_at"] = int(time.time())
        data["expires_at"] = data["obtained_at"] + int(data.get("expires_in", 0))
        
        logger.info("Token court obtenu avec succès")
        return data
        
    except httpx.RequestError as e:
        logger.error(f"Erreur requête OAuth exchange: {e}")
        raise
    except Exception as e:
        logger.error(f"Erreur échange code OAuth: {e}")
        raise

def oauth_extend_long_lived(user_token: str) -> Dict:
    """Convertit un token court en token long-lived (60 jours)"""
    
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": settings.META_APP_ID,
        "client_secret": settings.META_APP_SECRET,
        "fb_exchange_token": user_token
    }
    
    try:
        response = httpx.get(f"{get_base_url()}/oauth/access_token", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        data["obtained_at"] = int(time.time())
        data["expires_at"] = data["obtained_at"] + int(data.get("expires_in", 0))
        
        logger.info("Token long-lived obtenu avec succès")
        return data
        
    except httpx.RequestError as e:
        logger.error(f"Erreur requête extend token: {e}")
        raise
    except Exception as e:
        logger.error(f"Erreur extension token: {e}")
        raise

def list_pages(user_token: str) -> List[Dict]:
    """Liste les pages Facebook de l'utilisateur"""
    
    try:
        params = {"access_token": user_token}
        response = httpx.get(f"{get_base_url()}/me/accounts", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        pages = data.get("data", [])
        
        logger.info(f"{len(pages)} pages trouvées")
        return pages
        
    except httpx.RequestError as e:
        logger.error(f"Erreur requête list pages: {e}")
        raise
    except Exception as e:
        logger.error(f"Erreur récupération pages: {e}")
        raise

def get_ig_user_id(page_id: str, page_token: str) -> Optional[str]:
    """Récupère l'ID du compte Instagram Business lié à une page"""
    
    try:
        params = {
            "fields": "instagram_business_account",
            "access_token": page_token
        }
        
        response = httpx.get(f"{get_base_url()}/{page_id}", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        iga = data.get("instagram_business_account")
        
        if iga and iga.get("id"):
            ig_user_id = iga["id"]
            logger.info(f"Instagram User ID trouvé: {ig_user_id}")
            return ig_user_id
        else:
            logger.warning("Aucun compte Instagram Business lié à cette page")
            return None
            
    except httpx.RequestError as e:
        logger.error(f"Erreur requête IG user ID: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur récupération IG user ID: {e}")
        return None

# === Publication de Reels ===

def ig_create_media(ig_user_id: str, page_token: str, video_url: str, caption: str, share_to_feed: bool = True) -> Dict:
    """Crée un container de média Reel sur Instagram"""
    
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption or "",
        "share_to_feed": "true" if share_to_feed else "false",
        "access_token": page_token
    }
    
    try:
        response = httpx.post(f"{get_base_url()}/{ig_user_id}/media", data=params, timeout=90)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Container créé avec succès: {data.get('id')}")
        return {"ok": True, **data}
        
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        logger.error(f"Erreur HTTP création container: {e.response.status_code} - {error_detail}")
        return {"ok": False, "status": e.response.status_code, "error": error_detail}
    except Exception as e:
        logger.error(f"Erreur création container: {e}")
        return {"ok": False, "error": str(e)}

def ig_check_creation(creation_id: str, page_token: str) -> Dict:
    """Vérifie le statut de création d'un container média"""
    
    try:
        params = {
            "fields": "status_code,status",
            "access_token": page_token
        }
        
        response = httpx.get(f"{get_base_url()}/{creation_id}", params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        status = data.get("status_code") or data.get("status", "UNKNOWN")
        logger.debug(f"Statut container {creation_id}: {status}")
        
        return data
        
    except httpx.RequestError as e:
        logger.error(f"Erreur requête statut création: {e}")
        raise
    except Exception as e:
        logger.error(f"Erreur vérification création: {e}")
        raise

def ig_publish_media(ig_user_id: str, page_token: str, creation_id: str) -> Dict:
    """Publie un container média finalisé sur Instagram"""
    
    params = {
        "creation_id": creation_id,
        "access_token": page_token
    }
    
    try:
        response = httpx.post(f"{get_base_url()}/{ig_user_id}/media_publish", data=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Média publié avec succès: {data.get('id')}")
        return {"ok": True, **data}
        
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text
        logger.error(f"Erreur HTTP publication média: {e.response.status_code} - {error_detail}")
        return {"ok": False, "status": e.response.status_code, "error": error_detail}
    except Exception as e:
        logger.error(f"Erreur publication média: {e}")
        return {"ok": False, "error": str(e)}

def validate_video_url(video_url: str) -> bool:
    """Valide qu'une URL de vidéo est accessible par Meta"""
    
    try:
        response = httpx.head(video_url, timeout=10)
        return response.status_code == 200
    except:
        return False

def get_account_info(user_token: str) -> Dict:
    """Récupère les informations du compte utilisateur"""
    
    try:
        params = {
            "fields": "id,name,email",
            "access_token": user_token
        }
        
        response = httpx.get(f"{get_base_url()}/me", params=params, timeout=30)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Erreur récupération info compte: {e}")
        return {}