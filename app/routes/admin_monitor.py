from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.config import settings
from app.services.analytics_admin import summary

router = APIRouter(prefix="/admin", tags=["admin"])

def _guard(req: Request) -> bool:
    return req.headers.get("x-admin-secret") == getattr(settings, "ADMIN_SECRET", "admin123")

@router.get("/monitoring")
def admin_monitoring(request: Request):
    if not _guard(request): 
        return HTMLResponse("<h3>Unauthorized</h3>", status_code=401)
    
    s = summary()
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ContentFlow Admin Monitoring</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; background: #f8fafc; }}
            .container {{ max-width: 1200px; margin: 32px auto; padding: 0 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 24px; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin: 24px 0; }}
            .metric-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid #667eea; }}
            .metric-title {{ font-size: 14px; color: #64748b; font-weight: 600; margin-bottom: 8px; }}
            .metric-value {{ font-size: 28px; font-weight: bold; color: #1e293b; margin-bottom: 4px; }}
            .metric-subtitle {{ font-size: 12px; color: #64748b; }}
            .section-title {{ font-size: 20px; font-weight: bold; color: #1e293b; margin: 32px 0 16px 0; }}
            .status-good {{ color: #22c55e; }}
            .status-warning {{ color: #f59e0b; }}
            .status-danger {{ color: #ef4444; }}
            .links {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 24px; }}
            .link {{ display: inline-block; padding: 10px 16px; background: #667eea; color: white; text-decoration: none; border-radius: 6px; font-size: 14px; }}
            .link:hover {{ background: #5b6dd6; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0 0 8px 0;">📊 ContentFlow Admin Monitoring</h1>
                <p style="margin: 0; opacity: 0.9;">Tableau de bord en temps réel - Revenus, performance et santé de la plateforme</p>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">💰 Revenus 7 jours</div>
                    <div class="metric-value">€{s['rev_7d']:.2f}</div>
                    <div class="metric-subtitle">EPC 7j: €{s['epc_7d']:.3f}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">👆 Clics 7 jours</div>
                    <div class="metric-value">{s['clicks_7d']:,}</div>
                    <div class="metric-subtitle">Conversions: {s['conv_7d']}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">💳 Paiements disponibles</div>
                    <div class="metric-value">€{s['available']:.2f}</div>
                    <div class="metric-subtitle">Réservé: €{s['reserved']:.2f} • Payé: €{s['paid']:.2f}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">📈 Offre actuelle</div>
                    <div class="metric-value">€{s['offer'].get('headline_cpc',0):.2f}</div>
                    <div class="metric-subtitle">Mode: {s['offer'].get('terms',{}).get('mode','dev')} • par clic</div>
                </div>
            </div>

            <div class="section-title">🔄 Pipeline de publication</div>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-title">📝 Assignments en cours</div>
                    <div class="metric-value">{s['pending'] + s['approved']}</div>
                    <div class="metric-subtitle">
                        Pending: {s['pending']} • Approved: {s['approved']} • Posted: {s['posted']} • Failed: {s['failed']}
                    </div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">🛡️ Sécurité & Santé</div>
                    <div class="metric-value {'status-danger' if s['holds'] > 0 else 'status-good'}">{s['holds']}</div>
                    <div class="metric-subtitle">Holds actifs • Postbacks 24h: {s['postbacks_24h']}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">👥 Partenaires actifs</div>
                    <div class="metric-value">{s['partners_active']}</div>
                    <div class="metric-subtitle">Avec activité 7 derniers jours</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">⚡ Performance système</div>
                    <div class="metric-value {'status-good' if s['postbacks_24h'] > 0 else 'status-warning'}">
                        {'OK' if s['postbacks_24h'] > 0 else 'IDLE'}
                    </div>
                    <div class="metric-subtitle">Postbacks reçus dernières 24h</div>
                </div>
            </div>

            <div class="section-title">🔗 Actions rapides</div>
            <div class="links">
                <a href="/ops/payouts/pending" class="link">💰 Valider les payouts</a>
                <a href="/ops/holds" class="link">🛡️ Gérer les holds</a>
                <a href="/admin/payouts" class="link">📊 Journal des paiements</a>
                <a href="/admin/partners" class="link">👥 Gestion partenaires</a>
                <a href="/admin/config" class="link">⚙️ Configuration</a>
            </div>
            
            <div style="margin-top: 40px; padding: 16px; background: #f1f5f9; border-radius: 8px; font-size: 12px; color: #64748b;">
                <strong>Dernière mise à jour:</strong> {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                <br><strong>Mode:</strong> {s['offer'].get('terms',{}).get('mode','development').upper()}
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)

@router.get("/monitoring/api")
def admin_monitoring_api(request: Request):
    """API endpoint pour le monitoring en JSON"""
    if not _guard(request): 
        return {"error": "Unauthorized"}
    
    return {"success": True, "data": summary()}