"""
Service d'intégration Brevo pour campagnes email automatisées dans ContentFlow
Gestion des campagnes, listes, contacts et séquences email basées sur la performance
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmailCampaign:
    """Modèle de campagne email Brevo"""
    id: Optional[int] = None
    name: str = ""
    subject: str = ""
    content: str = ""
    list_ids: List[int] = None
    status: str = "draft"
    scheduled_at: Optional[datetime] = None
    stats: Dict[str, Any] = None

@dataclass
class ContactList:
    """Modèle de liste de contacts Brevo"""
    id: Optional[int] = None
    name: str = ""
    folder_id: Optional[int] = None
    total_contacts: int = 0

class BrevoClient:
    """Client pour l'API Brevo (ex-Sendinblue)"""
    
    def __init__(self):
        self.api_key = os.getenv("BREVO_API_KEY")
        self.base_url = "https://api.brevo.com/v3"
        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if not self.api_key:
            logger.warning("BREVO_API_KEY non configurée")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Effectue une requête à l'API Brevo"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {"success": True}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur API Brevo {method} {endpoint}: {e}")
            return {"error": str(e), "success": False}
    
    def get_account_info(self) -> Dict:
        """Récupère les informations du compte Brevo"""
        return self._make_request("GET", "/account")
    
    def get_email_campaigns(self, limit: int = 50) -> Dict:
        """Récupère la liste des campagnes email"""
        return self._make_request("GET", "/emailCampaigns", {"limit": limit})
    
    def create_email_campaign(self, campaign: EmailCampaign) -> Dict:
        """Crée une nouvelle campagne email"""
        data = {
            "name": campaign.name,
            "subject": campaign.subject,
            "htmlContent": campaign.content,
            "recipients": {"listIds": campaign.list_ids or []},
            "type": "classic"
        }
        
        if campaign.scheduled_at:
            data["scheduledAt"] = campaign.scheduled_at.isoformat()
        
        return self._make_request("POST", "/emailCampaigns", data)
    
    def send_campaign(self, campaign_id: int) -> Dict:
        """Envoie une campagne email"""
        return self._make_request("POST", f"/emailCampaigns/{campaign_id}/sendNow")
    
    def get_campaign_stats(self, campaign_id: int) -> Dict:
        """Récupère les statistiques d'une campagne"""
        return self._make_request("GET", f"/emailCampaigns/{campaign_id}")
    
    def get_contact_lists(self) -> Dict:
        """Récupère toutes les listes de contacts"""
        return self._make_request("GET", "/contacts/lists")
    
    def create_contact_list(self, name: str, folder_id: Optional[int] = None) -> Dict:
        """Crée une nouvelle liste de contacts"""
        data = {"name": name}
        if folder_id:
            data["folderId"] = folder_id
        
        return self._make_request("POST", "/contacts/lists", data)
    
    def add_contact(self, email: str, attributes: Dict = None, list_ids: List[int] = None) -> Dict:
        """Ajoute un contact"""
        data = {
            "email": email,
            "attributes": attributes or {},
            "listIds": list_ids or []
        }
        return self._make_request("POST", "/contacts", data)
    
    def get_contact(self, email: str) -> Dict:
        """Récupère un contact par email"""
        return self._make_request("GET", f"/contacts/{email}")

class ContentFlowEmailService:
    """Service de campagnes email pour ContentFlow"""
    
    def __init__(self):
        self.brevo = BrevoClient()
        self.default_lists = {
            "subscribers": "ContentFlow Subscribers",
            "high_engagement": "High Engagement Users", 
            "content_creators": "Content Creators"
        }
    
    def setup_default_lists(self) -> Dict:
        """Configure les listes par défaut pour ContentFlow"""
        results = {}
        
        for list_key, list_name in self.default_lists.items():
            result = self.brevo.create_contact_list(list_name)
            results[list_key] = result
            logger.info(f"Liste créée: {list_name}")
        
        return results
    
    def create_performance_newsletter(self, post_data: List[Dict], metrics: Dict) -> EmailCampaign:
        """Crée une newsletter de performance basée sur les meilleurs posts"""
        
        # Sélectionne les top 3 posts par engagement
        top_posts = sorted(post_data, key=lambda x: x.get('engagement', 0), reverse=True)[:3]
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #333;">📊 ContentFlow - Newsletter Performance</h1>
            <p>Voici vos meilleurs contenus de la semaine :</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>🎯 Métriques Globales</h3>
                <ul>
                    <li><strong>Total Posts:</strong> {metrics.get('total_posts', 0)}</li>
                    <li><strong>Engagement Moyen:</strong> {metrics.get('avg_engagement', 0):.1f}%</li>
                    <li><strong>Revenus Générés:</strong> {metrics.get('revenue', 0):.2f}€</li>
                </ul>
            </div>
        """
        
        for i, post in enumerate(top_posts, 1):
            html_content += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 8px;">
                <h4>#{i} - {post.get('title', 'Sans titre')}</h4>
                <p><strong>Plateforme:</strong> {post.get('platform', 'N/A')}</p>
                <p><strong>Engagement:</strong> {post.get('engagement', 0):.1f}%</p>
                <p><strong>Clics:</strong> {post.get('clicks', 0)}</p>
                <p><strong>Revenus:</strong> {post.get('revenue', 0):.2f}€</p>
            </div>
            """
        
        html_content += """
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://contentflow.app/dashboard" 
                   style="background: #007bff; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    🚀 Voir Dashboard Complet
                </a>
            </div>
            
            <p style="color: #666; font-size: 12px; text-align: center;">
                ContentFlow - Votre pipeline de contenu automatisé<br>
                <a href="{unsubscribe_link}">Se désabonner</a>
            </p>
        </body>
        </html>
        """
        
        campaign = EmailCampaign(
            name=f"ContentFlow Newsletter - {datetime.now().strftime('%Y-%m-%d')}",
            subject=f"📈 Vos {len(top_posts)} meilleurs contenus cette semaine",
            content=html_content
        )
        
        return campaign
    
    def create_revenue_alert(self, revenue_data: Dict) -> EmailCampaign:
        """Crée une alerte de revenus"""
        
        total_revenue = revenue_data.get('total', 0)
        growth = revenue_data.get('growth_percent', 0)
        top_source = revenue_data.get('top_source', 'N/A')
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #28a745;">💰 Alerte Revenus ContentFlow</h1>
            
            <div style="background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h2 style="color: #155724; text-align: center;">
                    {total_revenue:.2f}€ générés aujourd'hui!
                </h2>
                <p style="text-align: center; color: #155724;">
                    {'+' if growth > 0 else ''}{growth:.1f}% vs hier
                </p>
            </div>
            
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px;">
                <h3>📊 Détails</h3>
                <ul>
                    <li><strong>Source principale:</strong> {top_source}</li>
                    <li><strong>Posts actifs:</strong> {revenue_data.get('active_posts', 0)}</li>
                    <li><strong>Taux conversion:</strong> {revenue_data.get('conversion_rate', 0):.2f}%</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://contentflow.app/analytics" 
                   style="background: #28a745; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    📈 Voir Analytics Détaillées
                </a>
            </div>
        </body>
        </html>
        """
        
        campaign = EmailCampaign(
            name=f"Revenue Alert - {datetime.now().strftime('%Y-%m-%d')}",
            subject=f"💰 {total_revenue:.0f}€ générés aujourd'hui! ({growth:+.1f}%)",
            content=html_content
        )
        
        return campaign
    
    def create_content_promotion(self, niche: str, posts: List[Dict]) -> EmailCampaign:
        """Crée une campagne de promotion pour une niche spécifique"""
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #007bff;">🎯 Nouveaux Contenus {niche.title()}</h1>
            <p>Découvrez nos derniers contenus optimisés par IA dans la niche {niche} :</p>
        """
        
        for post in posts[:5]:  # Top 5 posts
            html_content += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 8px;">
                <h3>{post.get('title', 'Sans titre')}</h3>
                <p>{post.get('description', '')[:150]}...</p>
                <div style="margin: 10px 0;">
                    <span style="background: #e9ecef; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                        {post.get('platform', 'Multi-plateforme')}
                    </span>
                </div>
                <a href="{post.get('url', '#')}" 
                   style="color: #007bff; text-decoration: none;">
                    👉 Voir le contenu →
                </a>
            </div>
            """
        
        html_content += """
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://contentflow.app/content" 
                   style="background: #007bff; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    🚀 Découvrir Tous les Contenus
                </a>
            </div>
        </body>
        </html>
        """
        
        campaign = EmailCampaign(
            name=f"Content Promo {niche.title()} - {datetime.now().strftime('%Y-%m-%d')}",
            subject=f"🔥 Nouveaux contenus {niche} optimisés IA",
            content=html_content
        )
        
        return campaign
    
    def send_automated_campaign(self, campaign_type: str, data: Dict = None) -> Dict:
        """Envoie une campagne automatisée basée sur le type"""
        
        try:
            if campaign_type == "performance_newsletter":
                campaign = self.create_performance_newsletter(
                    data.get('posts', []), 
                    data.get('metrics', {})
                )
            elif campaign_type == "revenue_alert":
                campaign = self.create_revenue_alert(data.get('revenue', {}))
            elif campaign_type == "content_promotion":
                campaign = self.create_content_promotion(
                    data.get('niche', ''), 
                    data.get('posts', [])
                )
            else:
                return {"error": f"Type de campagne non supporté: {campaign_type}"}
            
            # Créer la campagne dans Brevo
            result = self.brevo.create_email_campaign(campaign)
            
            if result.get('id'):
                # Envoyer immédiatement si configuré
                if data.get('send_immediately', False):
                    send_result = self.brevo.send_campaign(result['id'])
                    result['send_status'] = send_result
                
                logger.info(f"Campagne {campaign_type} créée avec succès: {result['id']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur création campagne {campaign_type}: {e}")
            return {"error": str(e), "success": False}
    
    def get_service_status(self) -> Dict:
        """Retourne le statut du service Brevo"""
        
        try:
            account_info = self.brevo.get_account_info()
            campaigns = self.brevo.get_email_campaigns(limit=10)
            lists = self.brevo.get_contact_lists()
            
            return {
                "success": True,
                "brevo_connected": bool(account_info.get('email')),
                "account_email": account_info.get('email'),
                "total_campaigns": len(campaigns.get('campaigns', [])),
                "total_lists": len(lists.get('lists', [])),
                "api_key_configured": bool(self.brevo.api_key),
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "brevo_connected": False,
                "api_key_configured": bool(self.brevo.api_key)
            }

# Instance globale du service
email_service = ContentFlowEmailService()