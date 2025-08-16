import importlib
import traceback
from app.config import settings
from app.aiops.signals import fetch_kpis, bottlenecks
from app.aiops.selector import propose_actions, should_take_action
from app.aiops.reward import objective_score


def ai_tick(dry_run: bool | None = None) -> dict:
    """
    Tick principal de l'IA Orchestrator.
    Analyse la situation, propose et exécute des actions.
    """
    
    # Vérifier si l'autopilot est activé
    if not settings.FEATURE_AUTOPILOT:
        return {"ok": False, "reason": "autopilot_disabled"}
    
    # Déterminer le mode (dry_run depuis config ou paramètre)
    dry = settings.AI_DRY_RUN if dry_run is None else dry_run
    
    try:
        # 1. Collecter les signaux et KPIs
        kpis = fetch_kpis(settings.AI_LOOKBACK_DAYS)
        bottleneck_info = bottlenecks()
        
        # 2. Calculer le score d'objectif actuel
        current_score = objective_score(kpis, settings.AI_OBJECTIVE)
        
        # 3. Proposer des actions
        proposed_actions = propose_actions(kpis)
        
        # 4. Filtrer les actions selon les contraintes
        viable_actions = [
            (name, score) for name, score in proposed_actions
            if should_take_action(kpis, name, score)
        ]
        
        executed = []
        
        if not dry:
            # 5. Exécuter les actions viables (mode production)
            try:
                # Charger les actions dynamiquement pour éviter les imports circulaires
                acts = importlib.import_module("app.aiops.actions")
                
                action_count = 0
                for name, score in viable_actions:
                    if action_count >= settings.AI_MAX_ACTIONS_PER_TICK:
                        break
                    
                    if score < settings.AI_CONFIDENCE_THRESHOLD:
                        continue
                    
                    # Récupérer la fonction d'action
                    fn = getattr(acts, name, None)
                    if fn:
                        try:
                            fn(score)
                            executed.append({
                                "action": name, 
                                "score": score, 
                                "status": "success"
                            })
                        except Exception as e:
                            executed.append({
                                "action": name, 
                                "score": score, 
                                "status": "error",
                                "error": str(e)
                            })
                    else:
                        executed.append({
                            "action": name, 
                            "score": score, 
                            "status": "not_found"
                        })
                    
                    action_count += 1
                    
            except Exception as e:
                executed.append({
                    "action": "import_actions", 
                    "status": "error",
                    "error": f"Failed to import actions module: {str(e)}"
                })
        
        # 6. Retourner le rapport complet
        return {
            "ok": True,
            "dry_run": dry,
            "timestamp": str(kpis.get("timestamp", "now")),
            "objective": settings.AI_OBJECTIVE,
            "current_score": current_score,
            "kpis": kpis,
            "bottlenecks": bottleneck_info,
            "proposed_actions": proposed_actions,
            "viable_actions": viable_actions,
            "executed": executed,
            "config": {
                "confidence_threshold": settings.AI_CONFIDENCE_THRESHOLD,
                "max_actions_per_tick": settings.AI_MAX_ACTIONS_PER_TICK,
                "lookback_days": settings.AI_LOOKBACK_DAYS,
                "min_ctr": settings.AI_MIN_CTR,
                "max_risk": settings.AI_MAX_RISK,
                "min_quality": settings.AI_MIN_QUALITY
            }
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc() if settings.AI_DRY_RUN else None,
            "proposed_actions": [],
            "executed": []
        }


def get_agent_status() -> dict:
    """Retourne le statut général de l'agent."""
    return {
        "autopilot_enabled": settings.FEATURE_AUTOPILOT,
        "dry_run_mode": settings.AI_DRY_RUN,
        "tick_interval_minutes": settings.AI_TICK_INTERVAL_MIN,
        "objective": settings.AI_OBJECTIVE,
        "last_tick": "N/A",  # À implémenter avec un state persistent
        "health": "ok"
    }


def force_action(action_name: str, dry_run: bool = True) -> dict:
    """Forcer l'exécution d'une action spécifique."""
    try:
        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "action": action_name,
                "status": "simulated"
            }
        
        # Charger et exécuter l'action
        acts = importlib.import_module("app.aiops.actions")
        fn = getattr(acts, action_name, None)
        
        if not fn:
            return {
                "ok": False,
                "error": f"Action {action_name} not found"
            }
        
        fn(score=1.0)  # Score forcé à 1.0
        
        return {
            "ok": True,
            "action": action_name,
            "status": "executed"
        }
        
    except Exception as e:
        return {
            "ok": False,
            "action": action_name,
            "error": str(e)
        }