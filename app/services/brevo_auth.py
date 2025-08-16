"""
Service Brevo pour l'authentification par magic-link des partenaires.
Intégration complète avec l'API Brevo pour l'envoi d'emails sécurisés.
"""

import requests
import secrets
import datetime as dt
from typing import Dict, Optional
from app.config import settings

# Store temporaire des tokens (en production: Redis/JWT)
magic_tokens: Dict[str, dict] = {}

def generate_magic_token(partner_id: str, email: str) -> str:
    """Génère un token sécurisé pour l'authentification magic-link."""
    token = secrets.token_urlsafe(32)
    magic_tokens[token] = {
        "partner_id": partner_id,
        "email": email.lower().strip(),
        "expires": dt.datetime.utcnow() + dt.timedelta(minutes=15),
        "created_at": dt.datetime.utcnow()
    }
    return token

def validate_magic_token(token: str) -> Optional[dict]:
    """Valide un token magic-link et retourne les données si valide."""
    if token not in magic_tokens:
        return None
    
    token_data = magic_tokens[token]
    
    # Vérifier expiration
    if dt.datetime.utcnow() > token_data["expires"]:
        del magic_tokens[token]
        return None
    
    return token_data

def cleanup_magic_token(token: str) -> None:
    """Supprime un token après utilisation."""
    if token in magic_tokens:
        del magic_tokens[token]

def send_magic_link_email(email: str, magic_link: str) -> bool:
    """
    Envoie un email avec le magic-link via Brevo.
    Retourne True si envoyé avec succès, False sinon.
    """
    
    if not settings.BREVO_API_KEY:
        print("⚠️ BREVO_API_KEY manquante - Mode développement sans email")
        return False
    
    # Configuration email
    brevo_url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "api-key": settings.BREVO_API_KEY
    }
    
    # Template HTML pour l'email magic-link
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Accès Portail Partenaire - ContentFlow</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }}
            .content {{ padding: 40px 30px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
            .footer {{ background: #f8f9fa; padding: 30px; text-align: center; color: #666; font-size: 14px; }}
            .security {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 ContentFlow</h1>
                <h2>Accès Portail Partenaire</h2>
            </div>
            
            <div class="content">
                <h3>Bonjour !</h3>
                
                <p>Quelqu'un (probablement vous) a demandé un accès au portail partenaire ContentFlow pour l'adresse <strong>{email}</strong>.</p>
                
                <p>Pour accéder à votre espace partenaire, cliquez sur le bouton ci-dessous :</p>
                
                <div style="text-align: center;">
                    <a href="{magic_link}" class="button">🔐 Accéder au portail</a>
                </div>
                
                <div class="security">
                    <h4>🔒 Sécurité</h4>
                    <ul>
                        <li>Ce lien est valide pendant <strong>15 minutes</strong></li>
                        <li>Il ne peut être utilisé qu'<strong>une seule fois</strong></li>
                        <li>Si vous n'avez pas demandé cet accès, ignorez cet email</li>
                    </ul>
                </div>
                
                <p>Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :</p>
                <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace;">
                    {magic_link}
                </p>
            </div>
            
            <div class="footer">
                <p><strong>ContentFlow - Programme Partenaires</strong></p>
                <p>Monétisez votre audience avec du contenu automatisé par IA</p>
                <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Préparer la requête
    payload = {
        "sender": {
            "name": "ContentFlow",
            "email": "noreply@contentflow.app"
        },
        "to": [
            {
                "email": email,
                "name": email.split('@')[0].title()
            }
        ],
        "subject": "🔐 Votre lien d'accès au portail partenaire ContentFlow",
        "htmlContent": html_content,
        "textContent": f"Accédez à votre portail partenaire ContentFlow : {magic_link}\n\nCe lien expire dans 15 minutes.",
        "tags": ["partner-auth", "magic-link"],
        "headers": {
            "X-Priority": "1"
        }
    }
    
    try:
        response = requests.post(brevo_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            print(f"✅ Magic-link envoyé avec succès à {email}")
            return True
        else:
            print(f"❌ Erreur Brevo {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau Brevo: {str(e)}")
        return False

def cleanup_expired_tokens() -> int:
    """Nettoie les tokens expirés. Retourne le nombre de tokens supprimés."""
    now = dt.datetime.utcnow()
    expired_tokens = [
        token for token, data in magic_tokens.items() 
        if now > data["expires"]
    ]
    
    for token in expired_tokens:
        del magic_tokens[token]
    
    if expired_tokens:
        print(f"🧹 Nettoyage: {len(expired_tokens)} tokens expirés supprimés")
    
    return len(expired_tokens)

def get_token_stats() -> dict:
    """Retourne des statistiques sur les tokens actifs."""
    now = dt.datetime.utcnow()
    active_tokens = [
        data for data in magic_tokens.values()
        if now <= data["expires"]
    ]
    
    return {
        "total_tokens": len(magic_tokens),
        "active_tokens": len(active_tokens),
        "expired_tokens": len(magic_tokens) - len(active_tokens),
        "oldest_token": min([data["created_at"] for data in active_tokens]) if active_tokens else None
    }