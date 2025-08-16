"""
AI Scheduler - Gestion automatisée des tâches d'autopilot
"""
import time
import threading
from datetime import datetime, timedelta
from app.config import settings
from app.aiops.autopilot import ai_tick
from app.utils.logger import logger


class AIScheduler:
    """Scheduler pour l'AI Orchestrator avec ticks automatiques."""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.last_tick = None
        
    def start(self):
        """Démarre le scheduler en arrière-plan."""
        if self.running:
            logger.warning("AI Scheduler already running")
            return
            
        if not settings.FEATURE_AUTOPILOT:
            logger.info("AI Autopilot disabled, scheduler not started")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"AI Scheduler started with {settings.AI_TICK_INTERVAL_MIN} minute intervals")
        
    def stop(self):
        """Arrête le scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("AI Scheduler stopped")
        
    def _run_loop(self):
        """Boucle principale du scheduler."""
        while self.running:
            try:
                # Vérifier si il est temps pour un tick
                if self._should_tick():
                    logger.info("Executing AI tick...")
                    result = ai_tick(dry_run=settings.AI_DRY_RUN)
                    
                    if result.get("ok"):
                        executed_count = len(result.get("executed", []))
                        logger.info(f"AI tick completed successfully. {executed_count} actions executed.")
                        self.last_tick = datetime.utcnow()
                    else:
                        logger.error(f"AI tick failed: {result.get('error', 'Unknown error')}")
                
                # Attendre avant le prochain check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in AI scheduler loop: {e}")
                time.sleep(60)
                
    def _should_tick(self) -> bool:
        """Détermine si un tick doit être exécuté."""
        if not self.last_tick:
            return True
            
        interval = timedelta(minutes=settings.AI_TICK_INTERVAL_MIN)
        return datetime.utcnow() - self.last_tick >= interval
        
    def force_tick(self, dry_run: bool = None) -> dict:
        """Force un tick immédiat."""
        logger.info("Forcing AI tick...")
        dry = dry_run if dry_run is not None else settings.AI_DRY_RUN
        result = ai_tick(dry_run=dry)
        
        if result.get("ok") and not dry:
            self.last_tick = datetime.utcnow()
            
        return result
        
    def get_status(self) -> dict:
        """Retourne le statut du scheduler."""
        return {
            "running": self.running,
            "last_tick": self.last_tick.isoformat() if self.last_tick else None,
            "next_tick": (self.last_tick + timedelta(minutes=settings.AI_TICK_INTERVAL_MIN)).isoformat() if self.last_tick else "immediately",
            "interval_minutes": settings.AI_TICK_INTERVAL_MIN,
            "autopilot_enabled": settings.FEATURE_AUTOPILOT,
            "dry_run_mode": settings.AI_DRY_RUN
        }


# Instance globale du scheduler
ai_scheduler = AIScheduler()