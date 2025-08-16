import json
import logging
import numpy as np
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models import Rule, MetricEvent
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ThompsonSampling:
    """Thompson Sampling implementation for multi-armed bandit optimization."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_bandit_state(self, context: str) -> Dict[str, Dict[str, int]]:
        """Get current bandit state (alpha, beta parameters) for a context."""
        rule = self.db.query(Rule).filter(Rule.key == f"bandit:{context}").first()
        
        if rule and rule.value_json:
            try:
                return json.loads(rule.value_json)
            except:
                pass
        
        # Default state - start with uniform priors
        return {}
    
    def save_bandit_state(self, context: str, state: Dict[str, Dict[str, int]]):
        """Save bandit state to database."""
        rule = self.db.query(Rule).filter(Rule.key == f"bandit:{context}").first()
        
        if rule:
            rule.value_json = json.dumps(state)
        else:
            rule = Rule(
                key=f"bandit:{context}",
                value_json=json.dumps(state),
                enabled=True
            )
            self.db.add(rule)
        
        self.db.commit()
    
    def choose_arm(self, context: str, available_arms: List[str]) -> str:
        """
        Choose an arm using Thompson Sampling.
        
        Args:
            context: Context identifier (e.g., "platform:fr:hook_type")
            available_arms: List of available arm identifiers
            
        Returns:
            Selected arm identifier
        """
        try:
            state = self.get_bandit_state(context)
            
            # Ensure all arms have state
            for arm in available_arms:
                if arm not in state:
                    state[arm] = {"alpha": 1, "beta": 1}  # Uniform prior
            
            # Sample from beta distribution for each arm
            arm_samples = {}
            for arm in available_arms:
                alpha = state[arm]["alpha"]
                beta = state[arm]["beta"]
                
                # Sample from Beta(alpha, beta)
                sample = np.random.beta(alpha, beta)
                arm_samples[arm] = sample
            
            # Choose arm with highest sample
            chosen_arm = max(arm_samples.keys(), key=lambda x: arm_samples[x])
            
            logger.info(f"Thompson sampling chose arm '{chosen_arm}' for context '{context}'")
            logger.debug(f"Arm samples: {arm_samples}")
            
            return chosen_arm
            
        except Exception as e:
            logger.error(f"Error in Thompson sampling for context '{context}': {e}")
            # Fallback to round-robin
            return available_arms[hash(context) % len(available_arms)]
    
    def update_reward(self, context: str, arm: str, reward: float):
        """
        Update bandit with observed reward.
        
        Args:
            context: Context identifier
            arm: Arm that was chosen
            reward: Observed reward (0.0 for failure, 1.0 for success)
        """
        try:
            state = self.get_bandit_state(context)
            
            if arm not in state:
                state[arm] = {"alpha": 1, "beta": 1}
            
            # Update beta distribution parameters
            if reward > 0.5:  # Success
                state[arm]["alpha"] += 1
            else:  # Failure
                state[arm]["beta"] += 1
            
            self.save_bandit_state(context, state)
            
            logger.info(f"Updated bandit: context='{context}', arm='{arm}', reward={reward}")
            logger.debug(f"New state for arm '{arm}': {state[arm]}")
            
        except Exception as e:
            logger.error(f"Error updating bandit reward: {e}")


def update_from_metrics(db: Session):
    """Update bandit states from real metrics data (closed loop)."""
    from app.models import Post, MetricEvent, Rule
    from datetime import datetime, timedelta
    
    logger.info("Starting bandit update from metrics")
    
    # Get posts from last 7 days with metrics
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    posts_with_metrics = db.query(Post).join(MetricEvent).filter(
        Post.created_at >= cutoff_date,
        MetricEvent.timestamp >= cutoff_date
    ).distinct().all()
    
    arm_rewards = {}  # arm_key -> list of rewards
    
    for post in posts_with_metrics:
        # Calculate reward for this post
        metrics = db.query(MetricEvent).filter(
            MetricEvent.post_id == post.id,
            MetricEvent.timestamp >= cutoff_date
        ).all()
        
        clicks = sum(m.value for m in metrics if m.kind == "click")
        views = sum(m.value for m in metrics if m.kind in ["view", "impression"])
        
        # Calculate reward (CTR or engagement rate)
        if views > 0:
            reward = min(clicks / views, 1.0)  # Cap at 100% CTR
        else:
            reward = 0.0
        
        # Generate arm key for this post
        arm_key = f"{post.platform}_{post.language}_{post.ab_group or 'default'}"
        
        if arm_key not in arm_rewards:
            arm_rewards[arm_key] = []
        arm_rewards[arm_key].append(reward)
    
    # Update bandit states
    updates_made = 0
    for arm_key, rewards in arm_rewards.items():
        if not rewards:
            continue
            
        # Get current bandit state
        bandit_rule = db.query(Rule).filter(Rule.key == f"bandit_state_{arm_key}").first()
        
        if bandit_rule:
            import json
            state = json.loads(bandit_rule.value)
        else:
            state = {"alpha": 1.0, "beta": 1.0}
            bandit_rule = Rule(
                key=f"bandit_state_{arm_key}",
                value=json.dumps(state),
                description=f"Bandit state for {arm_key}"
            )
            db.add(bandit_rule)
        
        # Update Beta parameters based on rewards
        for reward in rewards:
            state["alpha"] += reward
            state["beta"] += (1.0 - reward)
        
        # Save updated state
        bandit_rule.value = json.dumps(state)
        bandit_rule.updated_at = datetime.utcnow()
        updates_made += 1
    
    db.commit()
    
    logger.info(f"Bandit update completed: {updates_made} arms updated from {len(posts_with_metrics)} posts")
    return updates_made

def choose_arm(context: str, db: Session, available_arms: List[str] = None) -> str:
    """
    Convenience function to choose an arm using Thompson Sampling.
    
    Args:
        context: Context for the bandit (e.g., "platform:fr:hook")
        db: Database session
        available_arms: List of available arms, defaults to common ones
        
    Returns:
        Selected arm identifier
    """
    if available_arms is None:
        # Default arms for different contexts
        if "platform" in context:
            available_arms = ["youtube", "reddit", "pinterest", "instagram", "tiktok"]
        elif "hook" in context:
            available_arms = ["curiosity", "value", "question", "statistic", "story"]
        elif "language" in context:
            available_arms = ["fr", "en"]
        else:
            available_arms = ["default"]
    
    bandit = ThompsonSampling(db)
    return bandit.choose_arm(context, available_arms)


def update_bandit_from_metrics(db: Session, lookback_hours: int = 24):
    """
    Update all bandits based on recent metric events.
    
    This should be called periodically to learn from user interactions.
    """
    try:
        # Get recent click events
        since = datetime.utcnow() - timedelta(hours=lookback_hours)
        
        click_events = db.query(MetricEvent).filter(
            MetricEvent.kind == "click",
            MetricEvent.ts >= since
        ).all()
        
        bandit = ThompsonSampling(db)
        
        for event in click_events:
            try:
                meta = json.loads(event.meta_json) if event.meta_json else {}
                
                # Extract context and arm from metadata
                arm_key = meta.get("arm_key")
                if not arm_key:
                    continue
                
                # Parse arm_key like "title:curiosity:youtube"
                parts = arm_key.split(":")
                if len(parts) >= 3:
                    variant_type = parts[0]  # title, description, etc.
                    variant = parts[1]       # curiosity, value, etc.
                    platform = parts[2]      # youtube, instagram, etc.
                    
                    context = f"{variant_type}:{platform}"
                    
                    # Reward is 1.0 for click (binary success)
                    bandit.update_reward(context, variant, 1.0)
                
            except Exception as e:
                logger.warning(f"Error processing metric event {event.id}: {e}")
                continue
        
        logger.info(f"Updated bandits from {len(click_events)} click events")
        
    except Exception as e:
        logger.error(f"Error updating bandits from metrics: {e}")


def get_bandit_stats(context: str, db: Session) -> Dict[str, Any]:
    """Get current bandit statistics for a context."""
    bandit = ThompsonSampling(db)
    state = bandit.get_bandit_state(context)
    
    stats = {}
    for arm, params in state.items():
        alpha = params["alpha"]
        beta = params["beta"]
        
        # Calculate statistics
        total_trials = alpha + beta - 2  # Subtract priors
        successes = alpha - 1
        
        success_rate = successes / total_trials if total_trials > 0 else 0.0
        confidence = 1.0 / (1.0 + beta / alpha)  # Simple confidence measure
        
        stats[arm] = {
            "trials": total_trials,
            "successes": successes,
            "success_rate": success_rate,
            "confidence": confidence,
            "alpha": alpha,
            "beta": beta
        }
    
    return stats


def reset_bandit(context: str, db: Session):
    """Reset a bandit to initial state."""
    rule = db.query(Rule).filter(Rule.key == f"bandit:{context}").first()
    if rule:
        db.delete(rule)
        db.commit()
        logger.info(f"Reset bandit for context: {context}")