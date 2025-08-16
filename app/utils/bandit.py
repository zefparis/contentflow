import random
import math
from typing import Dict, List, Tuple
from app.utils.logger import logger


class ThompsonBandit:
    """Thompson Sampling for multi-armed bandit optimization"""
    
    def __init__(self):
        self.arms = {}  # {arm_id: {"alpha": int, "beta": int}}
    
    def get_or_create_arm(self, arm_id: str) -> Dict[str, int]:
        """Get or create arm with prior Beta(1,1)"""
        if arm_id not in self.arms:
            self.arms[arm_id] = {"alpha": 1, "beta": 1}
        return self.arms[arm_id]
    
    def sample_arm(self, arm_ids: List[str]) -> str:
        """Sample arm using Thompson Sampling"""
        if not arm_ids:
            return None
        
        best_sample = -1
        best_arm = arm_ids[0]
        
        for arm_id in arm_ids:
            arm = self.get_or_create_arm(arm_id)
            sample = random.betavariate(arm["alpha"], arm["beta"])
            
            if sample > best_sample:
                best_sample = sample
                best_arm = arm_id
        
        logger.info(f"Selected arm: {best_arm} (sample: {best_sample:.3f})")
        return best_arm
    
    def update_arm(self, arm_id: str, reward: bool):
        """Update arm with reward (True for success, False for failure)"""
        arm = self.get_or_create_arm(arm_id)
        
        if reward:
            arm["alpha"] += 1
        else:
            arm["beta"] += 1
        
        expected_reward = arm["alpha"] / (arm["alpha"] + arm["beta"])
        logger.info(f"Updated arm {arm_id}: α={arm['alpha']}, β={arm['beta']}, E[reward]={expected_reward:.3f}")
    
    def get_arm_stats(self, arm_id: str) -> Dict[str, float]:
        """Get statistics for an arm"""
        arm = self.get_or_create_arm(arm_id)
        alpha, beta = arm["alpha"], arm["beta"]
        
        mean = alpha / (alpha + beta)
        variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
        
        return {
            "mean": mean,
            "variance": variance,
            "trials": alpha + beta - 2,  # Subtract prior
            "successes": alpha - 1
        }


# Global bandit instance
bandit = ThompsonBandit()
