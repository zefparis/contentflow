from fastapi import APIRouter, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel, EmailStr
from app.db import SessionLocal
from app.models import Partner, MagicLink
from app.services.brevo_auth import (
    generate_magic_token,
    validate_magic_token,
    cleanup_magic_token,
    send_magic_link_email,
)
from app.config import settings
import datetime as dt
from app.utils.datetime import utcnow
import secrets

router = APIRouter(tags=["partner_auth"])


# ----------------------------
# Schemas
# ----------------------------
class MagicLinkRequest(BaseModel):
    email: EmailStr


# ----------------------------
# Helpers
# ----------------------------
async def _handle_magic_link(email: str) -> tuple[bool, str | None]:
    """
    Handle magic link creation + email send
    Returns: (success, error_message_or_dev_link)
    """
    email = (email or "").lower().strip()
    if not email:
        return False, "invalid_email"

    db = SessionLocal()
    try:
        # Create or get partner
        partner = db.query(Partner).filter(Partner.email == email).first()
        if not partner:
            partner = Partner(email=email)
            db.add(partner)
            db.commit()
            db.refresh(partner)

        # Generate secure token and persist in DB
        token = secrets.token_urlsafe(32)
        expires = utcnow() + dt.timedelta(minutes=15)
        ml = MagicLink(
            partner_id=partner.id, email=email, token=token, expires_at=expires
        )
        db.add(ml)
        db.commit()

        # Build login URL
        base_url = (
            getattr(settings, "PUBLIC_BASE_URL", None)
            or getattr(settings, "APP_BASE_URL", None)
            or "http://localhost:5000"
        )
        login_url = f"{base_url}/partner/login?token={token}"

        # Check Brevo config
        if not getattr(settings, "BREVO_API_KEY", None):
            # Pas de Brevo → fallback dev
            return True, login_url

        # Send email via Brevo
        if not send_magic_link_email(email, login_url):
            return False, "email_send_failed"

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        db.close()


# ----------------------------
# JSON APIs
# ----------------------------
@router.post("/api/partner/auth/magic-link")
async def api_send_magic_link(req: MagicLinkRequest):
    """JSON API pour générer et envoyer un magic link"""
    success, result = await _handle_magic_link(req.email)
    if success:
        return {"success": True}
    return JSONResponse(
        {"error": result}, status_code=500 if result != "invalid_email" else 400
    )


@router.post("/api/auth/magic-link")
async def api_send_magic_link_alias(req: MagicLinkRequest):
    """Alias pour compat frontend"""
    return await api_send_magic_link(req)


# ----------------------------
# Legacy HTML form (partners UI)
# ----------------------------
@router.post("/partner/magic")
async def send_magic_link(email: str = Form(...)):
    """Envoie un magic link via formulaire HTML"""
    success, result = await _handle_magic_link(email)
    if success and (result is None):
        # Email envoyé via Brevo
        html = f"""
        <h1>📧 Email envoyé</h1>
        <p>Un lien d'accès a été envoyé à <b>{email}</b>.</p>
        <p>Vérifiez votre boîte de réception (et vos spams).</p>
        <a href="/partners">← Retour</a>
        """
        return HTMLResponse(html)

    if success and result:  # Fallback dev: afficher le lien
        html = f"""
        <h1>⚠️ Mode développement</h1>
        <p>Brevo non configuré, voici ton lien temporaire :</p>
        <a href="{result}">{result}</a>
        """
        return HTMLResponse(html)

    return HTMLResponse(
        f"<h3>Erreur</h3><p>{result}</p><a href='/partners'>Retour</a>",
        status_code=400,
    )


# ----------------------------
# Login + Portal
# ----------------------------
@router.get("/partner/login")
def partner_login(token: str = Query(...)):
    """Valide un magic link et redirige vers le portail partenaire"""
    db = SessionLocal()
    partner_id = None
    now = utcnow()
    try:
        # 1) Vérifier token DB
        ml = (
            db.query(MagicLink)
            .filter(MagicLink.token == token, MagicLink.used == False)
            .first()
        )
        if ml and ml.expires_at and ml.expires_at > now:
            partner_id = ml.partner_id
            ml.used = True
            db.commit()
        else:
            # 2) Fallback mémoire
            token_data = validate_magic_token(token)
            if token_data:
                partner_id = token_data["partner_id"]
                cleanup_magic_token(token)

        if not partner_id:
            return HTMLResponse(
                "<h3>❌ Lien invalide ou expiré</h3><a href='/partners'>Retour</a>",
                status_code=400,
            )

        # Update last_login
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if partner:
            partner.last_login = now
            db.commit()
    finally:
        db.close()

    resp = RedirectResponse("/partner/portal", status_code=303)
    resp.set_cookie("partner_id", partner_id, max_age=86400 * 7, httponly=True)
    return resp


@router.get("/partner/portal")
def partner_portal(request: Request):
    """Portail partenaire stylé"""
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
                body {{ font-family: system-ui, sans-serif; background: #f4f6f8; margin:0; padding:0; }}
                header {{ background: #4f46e5; color: white; padding: 20px; text-align: center; }}
                header h1 {{ margin: 0; }}
                .container {{ max-width: 900px; margin: 40px auto; padding: 20px; }}
                .card-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: 20px; }}
                .card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; transition: all .2s; text-decoration:none; color: inherit; }}
                .card:hover {{ transform: translateY(-4px); box-shadow: 0 4px 14px rgba(0,0,0,0.15); }}
                .icon {{ font-size: 2.5em; margin-bottom: 10px; }}
                .title {{ font-weight: bold; font-size: 1.2em; margin-bottom: 5px; }}
                .desc {{ color: #666; font-size: 0.9em; }}
                footer {{ text-align:center; padding:20px; font-size:0.9em; color:#777; }}
                a.logout {{ color: #e11d48; font-weight:bold; }}
            </style>
        </head>
        <body>
            <header>
                <h1>🎉 Bienvenue {partner.email}</h1>
                <p>Portail Partenaire ContentFlow</p>
            </header>
            
            <div class="container">
                <div class="card-grid">
                    <a href="/partners/earnings" class="card">
                        <div class="icon">💰</div>
                        <div class="title">Mes Revenus</div>
                        <div class="desc">Solde, historique, retraits</div>
                    </a>
                    
                    <a href="/partners/leaderboard" class="card">
                        <div class="icon">🏆</div>
                        <div class="title">Leaderboard</div>
                        <div class="desc">Classement performances</div>
                    </a>
                    
                    <a href="/partners/faq" class="card">
                        <div class="icon">❓</div>
                        <div class="title">FAQ</div>
                        <div class="desc">Questions fréquentes</div>
                    </a>
                    
                    <a href="/partner/settings" class="card">
                        <div class="icon">⚙️</div>
                        <div class="title">Paramètres</div>
                        <div class="desc">Configuration du compte</div>
                    </a>
                </div>
            </div>
            
            <footer>
                <a href="/partners">🏠 Accueil</a> • 
                <a href="/partner/logout" class="logout">🚪 Déconnexion</a>
            </footer>
        </body>
        </html>
        """
        return HTMLResponse(html)
    finally:
        db.close()

@router.get("/partner/settings")
def partner_settings(request: Request):
    """Page paramètres du partenaire (UI moderne)"""
    pid = request.cookies.get("partner_id")
    if not pid:
        return RedirectResponse("/partners")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Paramètres — Partenaire ContentFlow</title>
        <style>
            body { font-family: system-ui, sans-serif; background: #f4f6f8; margin:0; padding:0; }
            header { background: #4f46e5; color: white; padding: 20px; text-align: center; }
            header h1 { margin: 0; }
            .container { max-width: 800px; margin: 40px auto; padding: 20px; }
            .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .card h2 { margin-top: 0; color: #111827; }
            .card p { color: #555; }
            .actions button { margin: 5px; padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer; }
            .actions button:disabled { background: #e5e7eb; color: #9ca3af; cursor: not-allowed; }
            footer { text-align:center; padding:20px; font-size:0.9em; color:#777; }
            a.back { color:#4f46e5; font-weight:bold; text-decoration:none; }
        </style>
    </head>
    <body>
        <header>
            <h1>⚙️ Paramètres Partenaire</h1>
        </header>

        <div class="container">
            <div class="card">
                <h2>🔗 Comptes connectés</h2>
                <p>Gère tes réseaux sociaux connectés (à venir).</p>
                <div class="actions">
                    <button disabled>Instagram</button>
                    <button disabled>TikTok</button>
                    <button disabled>YouTube</button>
                </div>
            </div>

            <div class="card">
                <h2>📝 Préférences de publication</h2>
                <p>Configure les types de contenu et fréquence (à venir).</p>
            </div>

            <div class="card">
                <h2>💌 Notifications</h2>
                <p>Choisis les alertes que tu souhaites recevoir (à venir).</p>
            </div>
        </div>

        <footer>
            <a href="/partner/portal" class="back">← Retour au portail</a>
        </footer>
    </body>
    </html>
    """
    return HTMLResponse(html)


@router.get("/partner/logout")
def partner_logout():
    """Déconnexion"""
    resp = RedirectResponse("/partners", status_code=303)
    resp.delete_cookie("partner_id")
    return resp
