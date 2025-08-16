from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from app.db import SessionLocal
from app.config import settings
from app.services.earnings import leaderboard, partner_balance, mask_email, request_withdraw
from app.models import Partner

router = APIRouter(tags=["partners_ui"])


@router.get("/partners")
def partners_landing():
    """Landing publique pour les partenaires."""
    from app.services.pricing import current_offer
    
    offer = current_offer()
    mode = offer["terms"]["mode"]
    is_rev = (mode == "revshare")
    badge = f"jusqu'à €{offer['headline_cpc']:.2f} par clic" if not is_rev else f"jusqu'à €{offer['headline_cpc']:.2f} indicatif"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Plug & Earn — Deviens partenaire</title>
        <style>
            body {{ font-family: system-ui; max-width: 860px; margin: 40px auto; padding: 20px; }}
            .highlight {{ background: #f0f8ff; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .method {{ display: inline-block; background: #e8f5e8; padding: 4px 8px; border-radius: 4px; margin: 2px; }}
            form {{ background: #fafafa; padding: 15px; border-radius: 8px; margin: 16px 0; }}
            input, button {{ padding: 10px; margin: 5px; border: 1px solid #ccc; border-radius: 4px; }}
            button {{ background: #007bff; color: white; border: none; cursor: pointer; }}
            .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
            .stat {{ text-align: center; }}
        </style>
    </head>
    <body>
        <h1>🚀 Plug & Earn — Deviens partenaire ContentFlow</h1>
        
        <div class="highlight">
            <p><strong>Connecte tes comptes. Valide nos posts. {badge}.</strong></p>
            <ul>
                <li>✅ Zéro création de contenu — on fait tout</li>
                <li>✅ Cap anti-spam & contrôle manuel total</li>
                <li>✅ Paiement dès <strong>{int(settings.PAYOUT_MIN_EUR)}€</strong></li>
                <li>✅ Méthodes: {settings.PAYOUT_METHODS.replace(',', ', ')}</li>
            </ul>
        </div>
        
        <h2>🎯 Comment ça marche ?</h2>
        <ol>
            <li><strong>Inscription</strong> — Connecte tes comptes sociaux</li>
            <li><strong>Validation</strong> — Approuve ou rejette nos contenus</li>
            <li><strong>Publication</strong> — On poste automatiquement</li>
            <li><strong>Revenus</strong> — Tu gagnes sur chaque clic généré</li>
        </ol>
        
        <form method="post" action="/partner/magic">
            <h3>🔑 Recevoir le lien d'accès</h3>
            <input name="email" type="email" placeholder="ton@email.com" required style="width: 250px;">
            <button type="submit">Recevoir le lien magique</button>
        </form>
        
        <div class="stats">
            <div class="stat">
                <h3>📊 Découvrir</h3>
                <p><a href="/partners/leaderboard">Voir le leaderboard</a></p>
            </div>
            <div class="stat">
                <h3>❓ Questions</h3>
                <p><a href="/partners/faq">FAQ complète</a></p>
            </div>
            <div class="stat">
                <h3>💰 Mes gains</h3>
                <p><a href="/partners/earnings">Dashboard revenus</a></p>
            </div>
        </div>
        
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666;">
            <p>ContentFlow Partners — Automatisation intelligente, revenus garantis</p>
            <small style="opacity:.7;">Mode: {mode}. EPC7j={offer['epc_7d']:.2f}€.</small>
        </footer>
    </body>
    </html>
    """
    return HTMLResponse(html)


@router.get("/partners/leaderboard")
def partners_leaderboard(days: int = Query(7)):
    """Leaderboard anonymisé des partenaires."""
    rows = leaderboard(days=days, limit=20)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Leaderboard Partenaires</title>
        <style>
            body {{ font-family: system-ui; max-width: 860px; margin: 40px auto; padding: 20px; }}
            .leaderboard {{ background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .rank {{ display: flex; align-items: center; padding: 15px; border-bottom: 1px solid #f0f0f0; }}
            .rank:nth-child(odd) {{ background: #f9f9f9; }}
            .rank-number {{ font-weight: bold; width: 40px; }}
            .rank-label {{ flex: 1; margin-left: 15px; }}
            .rank-clicks {{ font-weight: bold; color: #007bff; }}
            .medal {{ font-size: 1.2em; margin-right: 5px; }}
        </style>
    </head>
    <body>
        <h1>🏆 Leaderboard Partenaires ({days} derniers jours)</h1>
        
        <div class="leaderboard">
    """
    
    if not rows:
        html += "<div class='rank'><p>Aucun clic récent. Soyez le premier ! 🚀</p></div>"
    else:
        for r in rows:
            medal = ""
            if r['rank'] == 1:
                medal = "🥇"
            elif r['rank'] == 2:
                medal = "🥈"
            elif r['rank'] == 3:
                medal = "🥉"
                
            html += f"""
            <div class="rank">
                <div class="rank-number">{medal} #{r['rank']}</div>
                <div class="rank-label">{r['label']}</div>
                <div class="rank-clicks">{r['clicks']} clics</div>
            </div>
            """
    
    html += f"""
        </div>
        
        <p style="margin-top: 20px;">
            <a href="/partners">← Retour à l'accueil</a> | 
            <a href="/partners/earnings">Mes revenus</a>
        </p>
    </body>
    </html>
    """
    return HTMLResponse(html)


@router.get("/partners/earnings")
def partners_earnings(request: Request):
    """Dashboard des gains pour un partenaire connecté."""
    pid = request.cookies.get("partner_id")
    if not pid:
        return HTMLResponse("""
        <h3>🔒 Non authentifié</h3>
        <p>Vous devez être connecté pour voir vos gains.</p>
        <p><a href="/partners">← Retour à l'accueil</a></p>
        """, status_code=401)
    
    db = SessionLocal()
    p = db.query(Partner).filter_by(id=pid).first()
    db.close()
    if not p:
        return HTMLResponse("""
        <h3>❌ Partenaire introuvable</h3>
        <p>Votre session a expiré.</p>
        <p><a href="/partners">← Retour à l'accueil</a></p>
        """, status_code=404)
    
    from app.services.pricing import current_offer
    offer = current_offer()
    tarif = (f"{offer['terms'].get('cpc','?'):.2f}€/clic" 
             if offer["terms"]["mode"].startswith("cpc") 
             else f"{int(offer['terms'].get('revshare_pct',.4)*100)}% rev-share")
    
    bal = partner_balance(pid)
    methods_options = "".join([
        f"<option value='{m.strip()}'>{m.strip().title()}</option>" 
        for m in (settings.PAYOUT_METHODS or 'paypal').split(",")
    ])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mes Gains — ContentFlow Partners</title>
        <style>
            body {{ font-family: system-ui; max-width: 860px; margin: 40px auto; padding: 20px; }}
            .balance {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin: 20px 0; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
            .metric {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
            .metric-value {{ font-size: 1.8em; font-weight: bold; color: #007bff; }}
            .metric-label {{ color: #666; font-size: 0.9em; }}
            .withdraw-form {{ background: #f8f9fa; padding: 25px; border-radius: 8px; margin: 25px 0; }}
            .form-row {{ display: flex; gap: 10px; margin: 10px 0; align-items: center; }}
            input, select, button {{ padding: 12px; border: 1px solid #ddd; border-radius: 6px; }}
            button {{ background: #28a745; color: white; border: none; cursor: pointer; font-weight: bold; }}
            button:hover {{ background: #218838; }}
            .available {{ font-size: 2em; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>💰 Mes Gains</h1>
        
        <div class="balance">
            <p><strong>Compte:</strong> {mask_email(p.email)}</p>
            <p class="available">Disponible: {bal['available']:.2f} €</p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{bal['clicks']}</div>
                <div class="metric-label">Clics (90j)</div>
            </div>
            <div class="metric">
                <div class="metric-value">{bal['epc']:.2f} €</div>
                <div class="metric-label">EPC moyen</div>
            </div>
            <div class="metric">
                <div class="metric-value">{bal['gross']:.2f} €</div>
                <div class="metric-label">Gains bruts</div>
            </div>
            <div class="metric">
                <div class="metric-value">{bal['pending']:.2f} €</div>
                <div class="metric-label">En attente</div>
            </div>
            <div class="metric">
                <div class="metric-value">{bal['paid']:.2f} €</div>
                <div class="metric-label">Déjà payé</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: #28a745;">{tarif}</div>
                <div class="metric-label">Barème actuel</div>
            </div>
        </div>
        
        <div class="withdraw-form">
            <h3>💸 Demander un retrait</h3>
            <form method="post" action="/partners/withdraw">
                <div class="form-row">
                    <input type="number" step="0.01" min="{settings.PAYOUT_MIN_EUR}" max="{bal['available']}" 
                           name="amount" placeholder="Montant (≥ {settings.PAYOUT_MIN_EUR}€)" required>
                    <select name="method" required>{methods_options}</select>
                </div>
                <div class="form-row">
                    <input name="details" placeholder="Email PayPal / IBAN (sera masqué)" 
                           style="flex: 1;" maxlength="100">
                    <button type="submit">Demander le retrait</button>
                </div>
            </form>
            <p style="color: #666; font-size: 0.9em; margin-top: 10px;">
                ⏱️ Traitement sous 24-48h ouvrées. Seuil minimum: {settings.PAYOUT_MIN_EUR}€
            </p>
        </div>
        
        <p style="margin-top: 30px;">
            <a href="/partner/portal">🔧 Gérer mes comptes</a> | 
            <a href="/partners/leaderboard">🏆 Leaderboard</a> | 
            <a href="/partners">🏠 Accueil partenaires</a>
        </p>
    </body>
    </html>
    """
    return HTMLResponse(html)


@router.post("/partners/withdraw")
def partners_withdraw(request: Request, amount: float = Form(...), method: str = Form(...), details: str = Form("")):
    """Traite une demande de retrait."""
    pid = request.cookies.get("partner_id")
    if not pid:
        return HTMLResponse("<h3>🔒 Non authentifié</h3>", status_code=401)
    
    res = request_withdraw(pid, float(amount), method.strip(), details.strip())
    
    if not res.get("ok"):
        error_msg = res.get("error", "Erreur inconnue")
        html = f"""
        <h3>❌ Demande refusée</h3>
        <p>Erreur: {error_msg}</p>
        <p>Vérifiez le montant (≥ seuil minimum & ≤ disponible) et la méthode de paiement.</p>
        <p><a href='/partners/earnings'>← Retour à mes gains</a></p>
        """
        return HTMLResponse(html, status_code=400)
    
    # Succès - redirection vers earnings avec message
    return RedirectResponse("/partners/earnings", status_code=303)


@router.get("/partners/faq")
def partners_faq():
    """FAQ pour les partenaires."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>FAQ Partenaires — ContentFlow</title>
        <style>
            body {{ font-family: system-ui; max-width: 860px; margin: 40px auto; padding: 20px; }}
            details {{ background: white; border: 1px solid #e0e0e0; border-radius: 8px; margin: 10px 0; }}
            summary {{ padding: 15px; cursor: pointer; font-weight: bold; background: #f8f9fa; }}
            summary:hover {{ background: #e9ecef; }}
            details[open] summary {{ background: #007bff; color: white; }}
            details p {{ padding: 15px; margin: 0; }}
            .amount {{ color: #28a745; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>❓ FAQ Partenaires ContentFlow</h1>
        
        <details>
            <summary>💰 Comment je gagne de l'argent ?</summary>
            <p>Tu gagnes au <strong>clic</strong> sur nos liens promotionnels. Chaque clic rapporte environ <span class="amount">{settings.DEFAULT_EPC_EUR:.2f} €</span>. Plus tu as d'audience engagée, plus tu gagnes !</p>
        </details>
        
        <details>
            <summary>🎯 Contrôle de ce qui est posté ?</summary>
            <p>Par défaut, <strong>review manuelle</strong> obligatoire. Tu peux activer l'<strong>autopublish</strong> avec un cap quotidien. Tu gardes toujours le contrôle total de ton image.</p>
        </details>
        
        <details>
            <summary>🛡️ Protection contre le ban ?</summary>
            <p>Anti-spam intégré : caps de publication, randomisation, variations visuelles, respect strict des règles de chaque plateforme. Zéro risque pour tes comptes.</p>
        </details>
        
        <details>
            <summary>💸 Paiements et seuils ?</summary>
            <p>Seuil minimum: <span class="amount">{int(settings.PAYOUT_MIN_EUR)}€</span>. Méthodes disponibles: {settings.PAYOUT_METHODS.replace(',', ', ')}. Demande depuis ton <a href='/partners/earnings'>dashboard revenus</a>.</p>
        </details>
        
        <details>
            <summary>📊 Transparence des gains ?</summary>
            <p>Dashboard temps réel avec détail des clics, EPC, revenus par plateforme. Historique complet et leaderboard anonymisé.</p>
        </details>
        
        <details>
            <summary>⚙️ Types de contenu ?</summary>
            <p>Tech, IA, productivité, outils créateurs. Contenu de qualité aligné avec ton audience. Pas de spam, pas de contenu douteux.</p>
        </details>
        
        <details>
            <summary>🚀 Comment commencer ?</summary>
            <p>1) Inscris-toi avec ton email 2) Connecte tes comptes sociaux 3) Configure tes préférences 4) Valide les premiers posts 5) Encaisse tes premiers gains !</p>
        </details>
        
        <p style="margin-top: 40px; text-align: center;">
            <a href="/partners">🏠 Retour à l'accueil</a> | 
            <a href="/partners/earnings">💰 Mes revenus</a> | 
            <a href="/partners/leaderboard">🏆 Leaderboard</a>
        </p>
        
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666;">
            <p>ContentFlow Partners — L'automation qui respecte tes comptes</p>
        </footer>
    </body>
    </html>
    """
    return HTMLResponse(html)