import random
from app.config import settings
from app.aiops.policies import min_ctr


def propose_actions(kpis: dict) -> list[tuple]:
    """
    Retourne une liste [(action_name, score), ...] ordonnée par score desc.
    Heuristique simple basée sur KPI globaux.
    """
    actions = []
    g = kpis.get("global", {})
    ctr = g.get("ctr", 0.0)
    rev = g.get("revenue", 0.0)
    views = g.get("views", 0.0)
    clicks = g.get("clicks", 0.0)
    
    # Score de base ajusté selon les performances
    base = 0.6
    
    # Ajustements selon les KPIs
    if ctr < min_ctr(): 
        base += 0.15  # Priorité sur l'amélioration du CTR
    if rev < 20: 
        base += 0.05  # Boost revenue si faible
    if views < 100:
        base += 0.10  # Priorité discovery si peu de vues
    
    # Calcul des scores par action
    actions = [
        ("act_run_ingest_transform_publish", base + 0.05 + (0.1 if views < 50 else 0)),
        ("act_promote_best_ab", base + 0.10 + (0.15 if ctr < min_ctr() else 0)),
        ("act_spawn_discovery_serp", base + 0.08 + (0.12 if views < 100 else 0)),
        ("act_route_to_partners", base + 0.12 + (0.05 if clicks > 10 else 0)),
        ("act_adjust_windows", base + random.uniform(-0.05, 0.05)),  # Variabilité
        ("act_optimize_content_strategy", base + 0.15 + (0.1 if rev > 10 else 0)),
        ("act_reprice_offers", base + 0.06),
    ]
    
    # Trier par score décroissant
    actions.sort(key=lambda x: x[1], reverse=True)
    
    return actions


def should_take_action(kpis: dict, action_name: str, score: float) -> bool:
    """Détermine si une action spécifique doit être prise."""
    
    # Vérifications globales
    if score < settings.AI_CONFIDENCE_THRESHOLD:
        return False
    
    g = kpis.get("global", {})
    
    # Logique spécifique par action
    if action_name == "act_spawn_discovery_serp":
        # Ne pas spam les sources si on en a déjà beaucoup
        return g.get("views", 0) < 200
    
    if action_name == "act_run_ingest_transform_publish":
        # Toujours autorisé si score OK
        return True
    
    if action_name == "act_promote_best_ab":
        # Seulement si on a des données d'expérience
        return g.get("clicks", 0) > 5
    
    return True


def get_action_priority(action_name: str, context: dict) -> str:
    """Retourne la priorité d'une action (high, medium, low)."""
    if action_name in ["act_run_ingest_transform_publish", "act_optimize_content_strategy"]:
        return "high"
    elif action_name in ["act_promote_best_ab", "act_spawn_discovery_serp"]:
        return "medium"
    else:
        return "low"