def objective_score(kpis: dict, objective: str) -> float:
    """Calcule le score d'objectif selon la stratégie choisie."""
    g = kpis.get("global", {})
    ctr = g.get("ctr", 0.0)
    rev = g.get("revenue", 0.0)
    views = g.get("views", 0.0)
    clicks = g.get("clicks", 0.0)
    
    if objective == "clicks_growth":
        return clicks
    
    if objective == "views_growth":
        return views
    
    # Default: revenue_ctr_safe - revenue balancé par le plancher CTR
    penalty = 0.0 if ctr >= 0.008 else (0.008 - ctr) * 1000.0
    return rev - penalty


def calculate_action_reward(action_name: str, kpis_before: dict, kpis_after: dict, objective: str) -> float:
    """Calcule la récompense d'une action basée sur l'amélioration des KPIs."""
    score_before = objective_score(kpis_before, objective)
    score_after = objective_score(kpis_after, objective)
    return score_after - score_before


def get_platform_performance_score(platform: str, kpis: dict) -> float:
    """Score de performance d'une plateforme spécifique."""
    platform_data = kpis.get("by_platform", {}).get(platform, {})
    views = platform_data.get("views", 0)
    clicks = platform_data.get("clicks", 0)
    revenue = platform_data.get("revenue", 0.0)
    
    if views == 0:
        return 0.0
    
    ctr = clicks / views
    epc = revenue / clicks if clicks > 0 else 0.0
    
    # Score composite: CTR * EPC * volume (normalisé)
    volume_score = min(views / 1000, 1.0)  # Normalise à 1000 vues max
    return ctr * epc * volume_score * 100  # Scaling pour avoir des scores plus lisibles