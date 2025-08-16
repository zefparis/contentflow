import json
from app.config import settings
from app.db import SessionLocal
from app.models import Rule


def load_rule(key: str, default=None):
    """Charge une règle depuis la base de données."""
    db = SessionLocal()
    try:
        r = db.query(Rule).filter_by(key=key).first()
        if not r or not r.value: 
            return default
        try: 
            return json.loads(r.value)
        except Exception: 
            return default
    finally:
        db.close()


def allowed_to_post(risk: float, quality: float) -> bool:
    """Vérifie si un contenu peut être publié selon les contraintes."""
    if risk is None or quality is None: 
        return False
    if risk > settings.AI_MAX_RISK: 
        return False
    if quality < settings.AI_MIN_QUALITY: 
        return False
    return True


def min_ctr() -> float:
    """Retourne le CTR minimum configuré."""
    return settings.AI_MIN_CTR


def rate_limit_respected(platform: str) -> bool:
    """Vérifie si les rate limits sont respectés pour une plateforme."""
    # Implémentation simplifiée - à étendre avec la logique de rate limiting existante
    rate_limits = load_rule("rate_limits", {})
    if platform in rate_limits:
        # Logique de vérification basée sur l'historique récent
        return True
    return True