from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from app.aiops.autopilot import ai_tick, get_agent_status, force_action
from app.aiops.signals import fetch_kpis, bottlenecks
from app.models import AgentAction, AgentState
from app.db import SessionLocal
import json

router = APIRouter(prefix="/ai", tags=["autopilot"])


@router.post("/tick")
def api_ai_tick(dry: bool = Query(False)):
    """Déclenche un tick de l'IA Orchestrator."""
    res = ai_tick(dry_run=dry)
    return JSONResponse(res)


@router.get("/status")
def api_agent_status():
    """Retourne le statut de l'agent."""
    return get_agent_status()


@router.get("/kpis")
def api_get_kpis(days: int = Query(7)):
    """Récupère les KPIs sur une période donnée."""
    kpis = fetch_kpis(days)
    return JSONResponse(kpis)


@router.get("/bottlenecks")
def api_get_bottlenecks():
    """Récupère les bottlenecks du pipeline."""
    return bottlenecks()


@router.post("/actions/{action_name}")
def api_force_action(action_name: str, dry: bool = Query(True)):
    """Force l'exécution d'une action spécifique."""
    res = force_action(action_name, dry_run=dry)
    return JSONResponse(res)


@router.get("/actions/history")
def api_action_history(limit: int = Query(50)):
    """Récupère l'historique des actions."""
    db = SessionLocal()
    try:
        actions = db.query(AgentAction).order_by(AgentAction.tick_ts.desc()).limit(limit).all()
        return [
            {
                "id": a.id,
                "tick_ts": a.tick_ts.isoformat() if a.tick_ts else None,
                "kind": a.kind,
                "target": a.target,
                "payload": json.loads(a.payload_json) if a.payload_json else {},
                "decision_score": a.decision_score,
                "executed": a.executed,
                "success": a.success,
                "error": a.error
            }
            for a in actions
        ]
    finally:
        db.close()


@router.get("/state")
def api_agent_state():
    """Récupère l'état persistant de l'agent."""
    db = SessionLocal()
    try:
        states = db.query(AgentState).all()
        return {
            state.key: json.loads(state.value_json) if state.value_json else {}
            for state in states
        }
    finally:
        db.close()


@router.get("/console")
def ai_console():
    """Interface web simple pour l'autopilot."""
    try:
        # Dry run pour avoir un aperçu
        res = ai_tick(dry_run=True)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Orchestrator - Console</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .status {{ padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .ok {{ background-color: #d4edda; color: #155724; }}
                .error {{ background-color: #f8d7da; color: #721c24; }}
                .kpi {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
                pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                button {{ padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }}
                .primary {{ background: #007bff; color: white; }}
                .secondary {{ background: #6c757d; color: white; }}
                .danger {{ background: #dc3545; color: white; }}
            </style>
        </head>
        <body>
            <h1>🤖 AI Orchestrator Console</h1>
            
            <div class="status {'ok' if res.get('ok') else 'error'}">
                Status: {'✅ Operational' if res.get('ok') else '❌ Error'}
                {'(Dry Run Mode)' if res.get('dry_run') else '(Live Mode)'}
            </div>
            
            <h2>📊 KPIs</h2>
            <div class="kpi">
                <strong>Global CTR:</strong> {res.get('kpis', {}).get('global', {}).get('ctr', 0):.4f}
            </div>
            <div class="kpi">
                <strong>Revenue:</strong> €{res.get('kpis', {}).get('global', {}).get('revenue', 0):.2f}
            </div>
            <div class="kpi">
                <strong>Views:</strong> {res.get('kpis', {}).get('global', {}).get('views', 0)}
            </div>
            <div class="kpi">
                <strong>Clicks:</strong> {res.get('kpis', {}).get('global', {}).get('clicks', 0)}
            </div>
            
            <h2>🎯 Proposed Actions</h2>
            <ul>
        """
        
        for action, score in res.get('proposed_actions', []):
            html += f"<li><strong>{action}</strong> (score: {score:.3f})</li>"
        
        html += f"""
            </ul>
            
            <h2>🚧 Bottlenecks</h2>
            <pre>{json.dumps(res.get('bottlenecks', {}), indent=2)}</pre>
            
            <h2>🎮 Controls</h2>
            <form method="post" action="/api/ai/tick?dry=false" style="display: inline;">
                <button type="submit" class="primary">Execute Tick (Live)</button>
            </form>
            <form method="post" action="/api/ai/tick?dry=true" style="display: inline;">
                <button type="submit" class="secondary">Dry Run Tick</button>
            </form>
            
            <h2>📝 Full Response</h2>
            <pre>{json.dumps(res, indent=2)}</pre>
        </body>
        </html>
        """
        
        return HTMLResponse(html)
        
    except Exception as e:
        return HTMLResponse(f"<h1>Error</h1><pre>{str(e)}</pre>", status_code=500)