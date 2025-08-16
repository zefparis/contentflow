from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from app.services.earnings import get_withdraw_requests, update_withdraw_status, partner_balance
from app.models import Partner, WithdrawRequest
from app.db import SessionLocal

router = APIRouter(prefix="/admin/partners", tags=["partners_admin"])


@router.get("/withdrawals")
def admin_withdrawals(status: str = Query(None), limit: int = Query(50)):
    """API admin pour voir les demandes de retrait."""
    try:
        requests = get_withdraw_requests(status=status, limit=limit)
        return JSONResponse({
            "success": True,
            "data": requests,
            "total": len(requests)
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/withdrawals/{withdraw_id}/approve")
def admin_approve_withdrawal(withdraw_id: str):
    """Approuve une demande de retrait."""
    try:
        result = update_withdraw_status(withdraw_id, "approved")
        if not result.get("ok"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return JSONResponse({
            "success": True,
            "message": "Withdrawal approved",
            "withdraw_id": withdraw_id
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/withdrawals/{withdraw_id}/reject")
def admin_reject_withdrawal(withdraw_id: str):
    """Rejette une demande de retrait."""
    try:
        result = update_withdraw_status(withdraw_id, "rejected")
        if not result.get("ok"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return JSONResponse({
            "success": True,
            "message": "Withdrawal rejected",
            "withdraw_id": withdraw_id
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.post("/withdrawals/{withdraw_id}/paid")
def admin_mark_paid(withdraw_id: str):
    """Marque une demande comme payée."""
    try:
        result = update_withdraw_status(withdraw_id, "paid")
        if not result.get("ok"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return JSONResponse({
            "success": True,
            "message": "Withdrawal marked as paid",
            "withdraw_id": withdraw_id
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/dashboard")
def admin_dashboard():
    """Dashboard HTML pour l'administration des partenaires."""
    db = SessionLocal()
    try:
        # Statistiques rapides
        total_partners = db.query(Partner).count()
        pending_withdrawals = db.query(WithdrawRequest).filter(
            WithdrawRequest.status == "requested"
        ).count()
        
        # Demandes récentes
        recent_withdrawals = db.query(WithdrawRequest).order_by(
            WithdrawRequest.created_at.desc()
        ).limit(10).all()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Partners — ContentFlow</title>
            <style>
                body {{ font-family: system-ui; max-width: 1200px; margin: 20px auto; padding: 20px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .stat {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
                .stat-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
                .withdrawals {{ background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .withdrawal {{ display: flex; align-items: center; padding: 15px; border-bottom: 1px solid #f0f0f0; }}
                .withdrawal:hover {{ background: #f8f9fa; }}
                .w-id {{ font-family: monospace; color: #666; width: 100px; }}
                .w-amount {{ font-weight: bold; color: #28a745; width: 80px; }}
                .w-method {{ width: 80px; }}
                .w-status {{ width: 100px; }}
                .w-date {{ color: #666; width: 120px; font-size: 0.9em; }}
                .w-actions {{ margin-left: auto; }}
                button {{ padding: 5px 10px; margin: 0 2px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8em; }}
                .btn-approve {{ background: #28a745; color: white; }}
                .btn-reject {{ background: #dc3545; color: white; }}
                .btn-paid {{ background: #17a2b8; color: white; }}
                .status-requested {{ color: #ffc107; font-weight: bold; }}
                .status-approved {{ color: #28a745; font-weight: bold; }}
                .status-paid {{ color: #17a2b8; font-weight: bold; }}
                .status-rejected {{ color: #dc3545; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>👥 Administration Partenaires</h1>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{total_partners}</div>
                    <div>Partenaires totaux</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{pending_withdrawals}</div>
                    <div>Retraits en attente</div>
                </div>
            </div>
            
            <h2>📤 Demandes de retrait récentes</h2>
            
            <div class="withdrawals">
        """
        
        if not recent_withdrawals:
            html += "<div class='withdrawal'>Aucune demande de retrait récente</div>"
        else:
            for wr in recent_withdrawals:
                status_class = f"status-{wr.status}"
                date_str = wr.created_at.strftime("%d/%m %H:%M") if wr.created_at else ""
                
                actions = ""
                if wr.status == "requested":
                    actions = f"""
                    <button class="btn-approve" onclick="updateStatus('{wr.id}', 'approve')">Approuver</button>
                    <button class="btn-reject" onclick="updateStatus('{wr.id}', 'reject')">Rejeter</button>
                    """
                elif wr.status == "approved":
                    actions = f"""
                    <button class="btn-paid" onclick="updateStatus('{wr.id}', 'paid')">Marquer payé</button>
                    """
                
                html += f"""
                <div class="withdrawal" id="wr-{wr.id}">
                    <div class="w-id">{wr.id[:8]}...</div>
                    <div class="w-amount">{wr.amount_eur:.2f}€</div>
                    <div class="w-method">{wr.method}</div>
                    <div class="w-status {status_class}">{wr.status}</div>
                    <div class="w-date">{date_str}</div>
                    <div class="w-actions">{actions}</div>
                </div>
                """
        
        html += f"""
            </div>
            
            <script>
            async function updateStatus(id, action) {{
                try {{
                    const response = await fetch(`/admin/partners/withdrawals/${{id}}/${{action}}`, {{
                        method: 'POST'
                    }});
                    const result = await response.json();
                    
                    if (result.success) {{
                        location.reload();
                    }} else {{
                        alert('Erreur: ' + result.error);
                    }}
                }} catch (e) {{
                    alert('Erreur réseau: ' + e.message);
                }}
            }}
            </script>
            
            <p style="margin-top: 30px;">
                <a href="/admin">← Retour admin</a> | 
                <a href="/partners">Interface publique</a>
            </p>
        </body>
        </html>
        """
        
        return HTMLResponse(html)
        
    finally:
        db.close()


@router.get("/stats")
def admin_stats():
    """Statistiques détaillées pour l'admin."""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        
        # Stats partenaires
        total_partners = db.query(Partner).count()
        active_partners = db.query(Partner).filter(Partner.status == "active").count()
        
        # Stats retraits
        total_withdrawals = db.query(WithdrawRequest).count()
        pending_amount = db.query(func.coalesce(func.sum(WithdrawRequest.amount_eur), 0.0))\
            .filter(WithdrawRequest.status == "requested").scalar()
        
        approved_amount = db.query(func.coalesce(func.sum(WithdrawRequest.amount_eur), 0.0))\
            .filter(WithdrawRequest.status == "approved").scalar()
            
        paid_amount = db.query(func.coalesce(func.sum(WithdrawRequest.amount_eur), 0.0))\
            .filter(WithdrawRequest.status == "paid").scalar()
        
        return JSONResponse({
            "success": True,
            "data": {
                "partners": {
                    "total": total_partners,
                    "active": active_partners
                },
                "withdrawals": {
                    "total_requests": total_withdrawals,
                    "pending_amount": round(pending_amount, 2),
                    "approved_amount": round(approved_amount, 2),
                    "paid_amount": round(paid_amount, 2)
                }
            }
        })
        
    finally:
        db.close()