from typing import Dict, Any
import json
from app.utils.logger import logger
from app.utils.datetime import iso_utc


class MetricsCollector:
    """Collect and store performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_event(self, event_type: str, data: Dict[str, Any]):
        """Record a metrics event"""
        timestamp = iso_utc()
        
        if event_type not in self.metrics:
            self.metrics[event_type] = []
        
        self.metrics[event_type].append({
            "timestamp": timestamp,
            "data": data
        })
        
        logger.info(f"Recorded {event_type}: {data}")
    
    def get_metrics(self, event_type: str = None) -> Dict[str, Any]:
        """Get collected metrics"""
        if event_type:
            return self.metrics.get(event_type, [])
        return self.metrics
    
    def calculate_performance(self, platform: str, timeframe_hours: int = 24) -> Dict[str, Any]:
        """Calculate performance metrics for a platform"""
        # Mock calculation for demo
        return {
            "views": 15000,
            "clicks": 375,
            "ctr": 2.5,
            "revenue": 281.25,
            "posts": 12
        }


# Global metrics collector
metrics = MetricsCollector()
