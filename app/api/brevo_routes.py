"""
Routes API pour l'intégration Brevo dans ContentFlow
Gestion des campagnes email, listes de contacts et automatisations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

from app.services.brevo_integration import email_service, EmailCampaign

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brevo", tags=["Brevo Email Marketing"])

class CampaignRequest(BaseModel):
    """Modèle de requête pour créer une campagne"""
    name: str
    subject: str
    content: str
    list_ids: List[int] = []
    send_immediately: bool = False
    scheduled_at: Optional[datetime] = None

class AutomatedCampaignRequest(BaseModel):
    """Modèle pour campagnes automatisées"""
    campaign_type: str  # "performance_newsletter", "revenue_alert", "content_promotion"
    data: Dict = {}
    send_immediately: bool = False

@router.get("/status")
async def get_brevo_status():
    """Retourne le statut de l'intégration Brevo"""
    
    try:
        status = email_service.get_service_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Erreur status Brevo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns")
async def get_campaigns(limit: int = 20):
    """Récupère la liste des campagnes email"""
    
    try:
        campaigns = email_service.brevo.get_email_campaigns(limit=limit)
        
        return {
            "success": True,
            "data": campaigns
        }
    except Exception as e:
        logger.error(f"Erreur récupération campagnes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns")
async def create_campaign(campaign_request: CampaignRequest):
    """Crée une nouvelle campagne email"""
    
    try:
        campaign = EmailCampaign(
            name=campaign_request.name,
            subject=campaign_request.subject,
            content=campaign_request.content,
            list_ids=campaign_request.list_ids,
            scheduled_at=campaign_request.scheduled_at
        )
        
        result = email_service.brevo.create_email_campaign(campaign)
        
        # Envoyer immédiatement si demandé
        if campaign_request.send_immediately and result.get('id'):
            send_result = email_service.brevo.send_campaign(result['id'])
            result['send_status'] = send_result
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Erreur création campagne: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(campaign_id: int):
    """Envoie une campagne email"""
    
    try:
        result = email_service.brevo.send_campaign(campaign_id)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Erreur envoi campagne {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(campaign_id: int):
    """Récupère les statistiques d'une campagne"""
    
    try:
        stats = email_service.brevo.get_campaign_stats(campaign_id)
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Erreur stats campagne {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lists")
async def get_contact_lists():
    """Récupère toutes les listes de contacts"""
    
    try:
        lists = email_service.brevo.get_contact_lists()
        
        return {
            "success": True,
            "data": lists
        }
    except Exception as e:
        logger.error(f"Erreur récupération listes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lists")
async def create_contact_list(name: str, folder_id: Optional[int] = None):
    """Crée une nouvelle liste de contacts"""
    
    try:
        result = email_service.brevo.create_contact_list(name, folder_id)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Erreur création liste {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lists/setup-defaults")
async def setup_default_lists():
    """Configure les listes par défaut pour ContentFlow"""
    
    try:
        results = email_service.setup_default_lists()
        
        return {
            "success": True,
            "data": results,
            "message": "Listes par défaut configurées avec succès"
        }
    except Exception as e:
        logger.error(f"Erreur setup listes par défaut: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/contacts")
async def add_contact(
    email: str, 
    attributes: Dict = None, 
    list_ids: List[int] = None
):
    """Ajoute un contact aux listes"""
    
    try:
        result = email_service.brevo.add_contact(
            email=email,
            attributes=attributes or {},
            list_ids=list_ids or []
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Erreur ajout contact {email}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contacts/{email}")
async def get_contact(email: str):
    """Récupère un contact par email"""
    
    try:
        contact = email_service.brevo.get_contact(email)
        
        return {
            "success": True,
            "data": contact
        }
    except Exception as e:
        logger.error(f"Erreur récupération contact {email}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/automated")
async def create_automated_campaign(
    request: AutomatedCampaignRequest,
    background_tasks: BackgroundTasks
):
    """Crée et envoie une campagne automatisée"""
    
    try:
        # Créer la campagne en arrière-plan si envoi immédiat
        if request.send_immediately:
            background_tasks.add_task(
                email_service.send_automated_campaign,
                request.campaign_type,
                request.data
            )
            
            return {
                "success": True,
                "message": f"Campagne {request.campaign_type} programmée pour envoi",
                "data": {"status": "scheduled"}
            }
        else:
            result = email_service.send_automated_campaign(
                request.campaign_type, 
                request.data
            )
            
            return {
                "success": True,
                "data": result
            }
            
    except Exception as e:
        logger.error(f"Erreur campagne automatisée {request.campaign_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation/performance-newsletter")
async def send_performance_newsletter(
    background_tasks: BackgroundTasks,
    send_immediately: bool = True
):
    """Déclenche l'envoi de la newsletter de performance hebdomadaire"""
    
    try:
        # Importer les services nécessaires pour récupérer les données
        from app.services.metrics import get_performance_metrics
        from app.db import get_recent_posts
        
        # Récupérer les données de performance
        metrics = get_performance_metrics(days=7)
        posts = get_recent_posts(limit=10, days=7)
        
        campaign_data = {
            "posts": posts,
            "metrics": metrics,
            "send_immediately": send_immediately
        }
        
        if send_immediately:
            background_tasks.add_task(
                email_service.send_automated_campaign,
                "performance_newsletter",
                campaign_data
            )
            
            return {
                "success": True,
                "message": "Newsletter de performance programmée pour envoi"
            }
        else:
            result = email_service.send_automated_campaign(
                "performance_newsletter", 
                campaign_data
            )
            
            return {
                "success": True,
                "data": result
            }
            
    except Exception as e:
        logger.error(f"Erreur newsletter performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation/revenue-alert")
async def send_revenue_alert(
    threshold: float = 50.0,
    background_tasks: BackgroundTasks,
    send_immediately: bool = True
):
    """Déclenche une alerte de revenus si le seuil est atteint"""
    
    try:
        from app.services.metrics import get_daily_revenue
        
        # Récupérer les revenus du jour
        revenue_data = get_daily_revenue()
        
        if revenue_data.get('total', 0) >= threshold:
            campaign_data = {
                "revenue": revenue_data,
                "send_immediately": send_immediately
            }
            
            if send_immediately:
                background_tasks.add_task(
                    email_service.send_automated_campaign,
                    "revenue_alert",
                    campaign_data
                )
                
                return {
                    "success": True,
                    "message": f"Alerte revenus envoyée: {revenue_data['total']:.2f}€"
                }
            else:
                result = email_service.send_automated_campaign(
                    "revenue_alert", 
                    campaign_data
                )
                
                return {
                    "success": True,
                    "data": result
                }
        else:
            return {
                "success": False,
                "message": f"Seuil non atteint: {revenue_data.get('total', 0):.2f}€ < {threshold}€"
            }
            
    except Exception as e:
        logger.error(f"Erreur alerte revenus: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation/content-promotion/{niche}")
async def send_content_promotion(
    niche: str,
    background_tasks: BackgroundTasks,
    send_immediately: bool = True,
    limit: int = 5
):
    """Envoie une campagne de promotion de contenu pour une niche"""
    
    try:
        from app.db import get_posts_by_niche
        
        # Récupérer les posts de la niche
        posts = get_posts_by_niche(niche, limit=limit)
        
        if not posts:
            return {
                "success": False,
                "message": f"Aucun contenu trouvé pour la niche {niche}"
            }
        
        campaign_data = {
            "niche": niche,
            "posts": posts,
            "send_immediately": send_immediately
        }
        
        if send_immediately:
            background_tasks.add_task(
                email_service.send_automated_campaign,
                "content_promotion",
                campaign_data
            )
            
            return {
                "success": True,
                "message": f"Promotion {niche} programmée pour {len(posts)} contenus"
            }
        else:
            result = email_service.send_automated_campaign(
                "content_promotion", 
                campaign_data
            )
            
            return {
                "success": True,
                "data": result
            }
            
    except Exception as e:
        logger.error(f"Erreur promotion contenu {niche}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/summary")
async def get_email_analytics():
    """Récupère un résumé des analyses email"""
    
    try:
        campaigns = email_service.brevo.get_email_campaigns(limit=20)
        
        total_campaigns = len(campaigns.get('campaigns', []))
        total_sent = sum(1 for c in campaigns.get('campaigns', []) if c.get('status') == 'sent')
        
        # Calculer les stats moyennes (simplifié)
        avg_open_rate = 23.5  # Valeur exemple, à calculer depuis les vraies stats
        avg_click_rate = 4.2
        
        return {
            "success": True,
            "data": {
                "total_campaigns": total_campaigns,
                "campaigns_sent": total_sent,
                "avg_open_rate": avg_open_rate,
                "avg_click_rate": avg_click_rate,
                "last_campaign": campaigns.get('campaigns', [{}])[0] if campaigns.get('campaigns') else None,
                "brevo_status": email_service.get_service_status()
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur analytics email: {e}")
        raise HTTPException(status_code=500, detail=str(e))