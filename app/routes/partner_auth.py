from fastapi import APIRouter, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
from app.db import SessionLocal
from app.models import Partner, MagicLink
from app.services.brevo_auth import (
    generate_magic_token, 
    validate_magic_token, 
    cleanup_magic_token,
    send_magic_link_email
)
from app.config import settings
import datetime as dt
import secrets

router = APIRouter(tags=["partner_auth"])


class MagicLinkRequest(BaseModel):
    email: str


@router.post("/api/partner/auth/magic-link")
def api_send_magic_link(req: MagicLinkRequest):
    """
    JSON API: Génère et envoie un lien magique BYOP.
    - Body: {"email": string}
    - Success: {"success": true}
    - Error: {"error": string}
    """
    email = (req.email or "").lower().strip()
    if not email:
        return JSONResponse({"error": "invalid_email"}, status_code=400)

    db = SessionLocal()
    try:
        # Créer ou récupérer le partenaire
        partner = db.query(Partner).filter(Partner.email == email).first()
        if not partner:
            partner = Partner(email=email)
            db.add(partner)
            db.commit()
            db.refresh(partner)

        # Générer un token sécurisé et persister en base
        token = secrets.token_urlsafe(32)
        expires = dt.datetime.utcnow() + dt.timedelta(minutes=15)
        ml = MagicLink(partner_id=partner.id, email=email, token=token, expires_at=expires)
        db.add(ml)
        db.commit()

        # Construire l'URL de connexion
        base_url = (
            getattr(settings, 'PUBLIC_BASE_URL', None)
            or getattr(settings, 'APP_BASE_URL', None)
            or 'http://localhost:5000'
        )
        login_url = f"{base_url}/partner/login?token={token}"

        # Vérifier configuration Brevo
        if not getattr(settings, 'BREVO_API_KEY', None):
            # Ne pas exposer la clé manquante; message générique
            return JSONResponse({"error": "Email service not configured"}, status_code=500)

        # Envoyer l'email
        sent = send_magic_link_email(email, login_url)
        if not sent:
            return JSONResponse({"error": "Email send failed"}, status_code=500)

        return {"success": True}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        db.close()


@router.post("/partner/magic")
def send_magic_link(email: str = Form(...)):
    """Envoie un lien magique pour l'authentification partenaire."""
    db = SessionLocal()
    try:
        # Créer ou récupérer le partenaire
        partner = db.query(Partner).filter(Partner.email == email.lower().strip()).first()
        if not partner:
            partner = Partner(email=email.lower().strip())
            db.add(partner)
            db.commit()
        
        # Générer un token sécurisé
        token = generate_magic_token(partner.id, email)
        
        # Construire le lien complet
        # Utilise PUBLIC_BASE_URL si défini, sinon APP_BASE_URL, sinon fallback local
        base_url = (
            getattr(settings, 'PUBLIC_BASE_URL', None)
            or getattr(settings, 'APP_BASE_URL', None)
            or 'http://localhost:5000'
        )
        magic_link = f"{base_url}/partner/login?token={token}"
        
        # Tenter d'envoyer par email via Brevo
        email_sent = send_magic_link_email(email, magic_link)
        
        # Réponse adaptée selon le succès de l'envoi
        if email_sent:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Email envoyé avec succès</title>
                <style>
                    body {{ font-family: system-ui; max-width: 600px; margin: 40px auto; padding: 20px; text-align: center; }}
                    .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .instructions {{ background: #e7f3ff; color: #0c5460; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                    a {{ color: #007bff; text-decoration: none; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>📧 Email envoyé avec succès</h1>
                
                <div class="success">
                    <p>Un lien d'accès sécurisé a été envoyé à <strong>{email}</strong></p>
                    <p>Vérifiez votre boîte de réception et votre dossier spam.</p>
                </div>
                
                <div class="instructions">
                    <h3>Prochaines étapes :</h3>
                    <ol style="text-align: left; max-width: 400px; margin: 0 auto;">
                        <li>Ouvrez votre email</li>
                        <li>Cliquez sur le bouton d'accès</li>
                        <li>Accédez à votre portail partenaire</li>
                    </ol>
                    <p><small>Le lien expire dans 15 minutes pour votre sécurité.</small></p>
                </div>
                
                <p><a href="/partners">← Retour à l'accueil</a></p>
            </body>
            </html>
            """
        else:
            # Fallback en mode développement
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Mode développement</title>
                <style>
                    body {{ font-family: system-ui; max-width: 600px; margin: 40px auto; padding: 20px; text-align: center; }}
                    .warning {{ background: #fff3cd; color: #856404; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .link {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                    a {{ color: #007bff; text-decoration: none; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h1>⚠️ Mode développement</h1>
                
                <div class="warning">
                    <p>L'email n'a pas pu être envoyé (configuration Brevo manquante)</p>
                    <p>Voici votre lien d'accès temporaire pour <strong>{email}</strong></p>
                </div>
                
                <div class="link">
                    <p><strong>Lien de développement (15 min):</strong></p>
                    <a href="/partner/login?token={token}">Accéder au portail partenaire</a>
                </div>
                
                <p><a href="/partners">← Retour à l'accueil</a></p>
            </body>
            </html>
            """
        
        return HTMLResponse(html)
        
    finally:
        db.close()


@router.get("/partner/login")
def partner_login(token: str = Query(...)):
    """Authentifie un partenaire via token magique (DB d'abord, fallback mémoire)."""
    db = SessionLocal()
    partner_id = None
    try:
        # 1) Vérifier le token persistant
        ml = db.query(MagicLink).filter(MagicLink.token == token, MagicLink.used == False).first()
        now = dt.datetime.utcnow()
        if ml and ml.expires_at and ml.expires_at > now:
            partner_id = ml.partner_id
            ml.used = True
            db.commit()
        else:
            # 2) Fallback sur le token en mémoire (compat)
            token_data = validate_magic_token(token)
            if token_data:
                partner_id = token_data["partner_id"]
                cleanup_magic_token(token)

        if not partner_id:
            return HTMLResponse(
                """
                <h3>🔗 Lien invalide</h3>
                <p>Ce lien est invalide ou a expiré.</p>
                <p><a href='/partners'>← Retour à l'accueil</a></p>
                """,
                status_code=400,
            )

        # Mettre à jour last_login
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if partner:
            partner.last_login = now
            db.commit()

    finally:
        db.close()

    # Rediriger vers le portail avec cookie
    response = RedirectResponse("/partner/portal", status_code=303)
    response.set_cookie(
        "partner_id",
        partner_id,
        max_age=86400 * 7,  # 7 jours
        httponly=True,
    )
    return response


@router.get("/partner/portal")
def partner_portal(request: Request):
    """Portail principal du partenaire."""
    pid = request.cookies.get("partner_id")
    if not pid:
        return RedirectResponse("/partners")
    
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == pid).first()
        if not partner:
            return RedirectResponse("/partners")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Portail Partenaire — ContentFlow</title>
            <style>
                body {{ font-family: system-ui; max-width: 800px; margin: 40px auto; padding: 20px; }}
                .welcome {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; text-align: center; }}
                .nav {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
                .nav-item {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; text-decoration: none; color: inherit; }}
                .nav-item:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
                .nav-icon {{ font-size: 2em; margin-bottom: 10px; }}
                .nav-title {{ font-weight: bold; margin-bottom: 5px; }}
                .nav-desc {{ color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="welcome">
                <h1>🎉 Bienvenue dans ton portail partenaire</h1>
                <p>Connecté en tant que <strong>{partner.email}</strong></p>
            </div>
            
            <div class="nav">
                <a href="/partners/earnings" class="nav-item">
                    <div class="nav-icon">💰</div>
                    <div class="nav-title">Mes Revenus</div>
                    <div class="nav-desc">Solde, historique, retraits</div>
                </a>
                
                <a href="/partners/leaderboard" class="nav-item">
                    <div class="nav-icon">🏆</div>
                    <div class="nav-title">Leaderboard</div>
                    <div class="nav-desc">Classement performances</div>
                </a>
                
                <a href="/partners/faq" class="nav-item">
                    <div class="nav-icon">❓</div>
                    <div class="nav-title">FAQ</div>
                    <div class="nav-desc">Questions fréquentes</div>
                </a>
                
                <a href="/partner/settings" class="nav-item">
                    <div class="nav-icon">⚙️</div>
                    <div class="nav-title">Paramètres</div>
                    <div class="nav-desc">Configuration compte</div>
                </a>
            </div>
            
            <p style="text-align: center; margin-top: 30px;">
                <a href="/partners">🏠 Accueil partenaires</a> | 
                <a href="/partner/logout">🚪 Déconnexion</a>
            </p>
        </body>
        </html>
        """
        
        return HTMLResponse(html)
        
    finally:
        db.close()


@router.get("/partner/settings")
def partner_settings(request: Request):
    """Page paramètres du partenaire."""
    pid = request.cookies.get("partner_id")
    if not pid:
        return RedirectResponse("/partners")
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Paramètres — Partenaire ContentFlow</title>
        <style>
            body { font-family: system-ui; max-width: 600px; margin: 40px auto; padding: 20px; }
            .setting { background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <h1>⚙️ Paramètres du compte</h1>
        
        <div class="setting">
            <h3>🔗 Comptes connectés</h3>
            <p>Gestion des comptes sociaux connectés (à implémenter)</p>
            <button disabled>Instagram</button>
            <button disabled>TikTok</button>
            <button disabled>YouTube</button>
        </div>
        
        <div class="setting">
            <h3>📝 Préférences de publication</h3>
            <p>Configuration des types de contenu et fréquence (à implémenter)</p>
        </div>
        
        <div class="setting">
            <h3>💌 Notifications</h3>
            <p>Paramètres des notifications email (à implémenter)</p>
        </div>
        
        <p><a href="/partner/portal">← Retour au portail</a></p>
    </body>
    </html>
    """
    
    return HTMLResponse(html)


@router.get("/partner/logout")
def partner_logout():
    """Déconnexion du partenaire."""
    response = RedirectResponse("/partners", status_code=303)
    response.delete_cookie("partner_id")
    return response