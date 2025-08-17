"""
Content Performance Prediction AI

This module implements machine learning models to predict content performance
before publication, enabling data-driven content optimization decisions.
"""

import logging
import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import timedelta
from app.utils.datetime import utcnow
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import os

from app.db import SessionLocal
from app.models import Post, Asset, MetricEvent
from app.utils.logger import logger

class PerformancePredictionAI:
    """AI system for predicting content performance metrics."""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.model_path = "/tmp/ai_models"
        self.min_training_samples = 50
        
        # Ensure model directory exists
        os.makedirs(self.model_path, exist_ok=True)
        
        # Load existing models
        self._load_models()
    
    def extract_features(self, post: Post, asset: Asset) -> Dict[str, Any]:
        """Extract features from post and asset for ML prediction."""
        
        # Parse metadata
        asset_meta = json.loads(asset.meta_json or "{}")
        plan = asset_meta.get("plan", {})
        
        # Basic features
        features = {
            # Content features
            "title_length": len(post.title or ""),
            "description_length": len(post.description or ""),
            "hashtag_count": len((post.hashtags or "").split(",")) if post.hashtags else 0,
            "duration": asset.duration or 30.0,
            "quality_score": plan.get("quality_score", 0.5),
            
            # Temporal features
            "hour_of_day": utcnow().hour,
            "day_of_week": utcnow().weekday(),
            "is_weekend": 1 if utcnow().weekday() >= 5 else 0,
            
            # Platform features
            "platform_youtube": 1 if post.platform == "youtube" else 0,
            "platform_tiktok": 1 if post.platform == "tiktok" else 0,
            "platform_instagram": 1 if post.platform == "instagram" else 0,
            "platform_reddit": 1 if post.platform == "reddit" else 0,
            "platform_pinterest": 1 if post.platform == "pinterest" else 0,
            
            # Language features
            "lang_en": 1 if (post.language or asset.lang) == "en" else 0,
            "lang_fr": 1 if (post.language or asset.lang) == "fr" else 0,
            "lang_es": 1 if (post.language or asset.lang) == "es" else 0,
            
            # Content type features
            "has_hook": 1 if plan.get("hook") else 0,
            "has_cta": 1 if plan.get("cta") else 0,
            "sentiment_score": plan.get("sentiment_score", 0.5),
            
            # Title features
            "title_has_question": 1 if post.title and "?" in post.title else 0,
            "title_has_numbers": 1 if post.title and any(c.isdigit() for c in post.title) else 0,
            "title_has_exclamation": 1 if post.title and "!" in post.title else 0,
        }
        
        # Add keyword density features
        keywords = asset.keywords or ""
        if keywords:
            keyword_list = [k.strip().lower() for k in keywords.split(",")]
            text_content = f"{post.title} {post.description}".lower()
            
            features["keyword_density"] = sum(
                text_content.count(kw) for kw in keyword_list
            ) / max(len(text_content.split()), 1)
        else:
            features["keyword_density"] = 0.0
        
        return features
    
    def get_training_data(self, platform: Optional[str] = None, days: int = 90) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Collect training data from historical posts and metrics."""
        
        db = SessionLocal()
        try:
            # Get posts with metrics from last N days
            cutoff_date = utcnow() - timedelta(days=days)
            
            query = db.query(Post, Asset).join(Asset).filter(
                Post.posted_at >= cutoff_date,
                Post.status == "posted"
            )
            
            if platform:
                query = query.filter(Post.platform == platform)
            
            posts_assets = query.all()
            
            if len(posts_assets) < self.min_training_samples:
                logger.warning(f"Insufficient training data: {len(posts_assets)} samples")
                return np.array([]), np.array([]), []
            
            # Extract features and targets
            features_list = []
            targets = []
            feature_names = None
            
            for post, asset in posts_assets:
                # Extract features
                features = self.extract_features(post, asset)
                
                if feature_names is None:
                    feature_names = list(features.keys())
                
                features_list.append([features[name] for name in feature_names])
                
                # Calculate performance target (engagement rate)
                metrics = db.query(MetricEvent).filter(
                    MetricEvent.post_id == post.id
                ).all()
                
                # Calculate engagement metrics
                clicks = sum(m.value for m in metrics if m.kind == "click")
                views = sum(m.value for m in metrics if m.kind == "view")
                likes = sum(m.value for m in metrics if m.kind == "like")
                shares = sum(m.value for m in metrics if m.kind == "share")
                
                # Engagement rate calculation
                if views > 0:
                    engagement_rate = (clicks + likes + shares) / views
                else:
                    engagement_rate = 0.0
                
                targets.append(engagement_rate)
            
            return np.array(features_list), np.array(targets), feature_names
            
        finally:
            db.close()
    
    def train_model(self, platform: str) -> Dict[str, Any]:
        """Train performance prediction model for a specific platform."""
        
        logger.info(f"Training performance prediction model for {platform}")
        
        # Get training data
        X, y, feature_names = self.get_training_data(platform)
        
        if len(X) == 0:
            return {"success": False, "error": "Insufficient training data"}
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train ensemble model
        models = {
            "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "gradient_boost": GradientBoostingRegressor(n_estimators=100, random_state=42)
        }
        
        best_model = None
        best_score = -float('inf')
        best_name = None
        
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            predictions = model.predict(X_test_scaled)
            score = r2_score(y_test, predictions)
            
            logger.info(f"{name} R² score: {score:.3f}")
            
            if score > best_score:
                best_score = score
                best_model = model
                best_name = name
        
        # Save model, scaler, and metadata
        model_data = {
            "model": best_model,
            "scaler": scaler,
            "feature_names": feature_names,
            "platform": platform,
            "trained_at": utcnow(),
            "r2_score": best_score,
            "training_samples": len(X),
            "model_type": best_name
        }
        
        # Save to disk
        model_file = os.path.join(self.model_path, f"{platform}_model.pkl")
        with open(model_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        # Store in memory
        self.models[platform] = model_data
        
        logger.info(f"Trained {best_name} model for {platform} with R² score: {best_score:.3f}")
        
        return {
            "success": True,
            "platform": platform,
            "model_type": best_name,
            "r2_score": best_score,
            "training_samples": len(X),
            "feature_count": len(feature_names)
        }
    
    def predict_performance(self, post: Post, asset: Asset) -> Dict[str, Any]:
        """Predict performance metrics for a post before publishing."""
        
        platform = post.platform
        
        # Check if model exists for platform
        if platform not in self.models:
            # Try to train model if we have data
            training_result = self.train_model(platform)
            if not training_result["success"]:
                return {
                    "success": False,
                    "error": f"No model available for {platform}",
                    "predicted_engagement": 0.0,
                    "confidence": 0.0
                }
        
        model_data = self.models[platform]
        model = model_data["model"]
        scaler = model_data["scaler"]
        feature_names = model_data["feature_names"]
        
        # Extract features
        features = self.extract_features(post, asset)
        
        # Prepare feature vector
        feature_vector = np.array([[features.get(name, 0.0) for name in feature_names]])
        
        # Scale features
        feature_vector_scaled = scaler.transform(feature_vector)
        
        # Make prediction
        predicted_engagement = model.predict(feature_vector_scaled)[0]
        
        # Calculate confidence based on model performance
        confidence = min(1.0, max(0.0, model_data["r2_score"]))
        
        # Provide recommendations
        recommendations = self._generate_recommendations(features, predicted_engagement)
        
        return {
            "success": True,
            "predicted_engagement": float(predicted_engagement),
            "confidence": float(confidence),
            "model_info": {
                "platform": platform,
                "model_type": model_data["model_type"],
                "trained_at": model_data["trained_at"].isoformat(),
                "training_samples": model_data["training_samples"]
            },
            "recommendations": recommendations
        }
    
    def _generate_recommendations(self, features: Dict[str, Any], predicted_engagement: float) -> List[str]:
        """Generate optimization recommendations based on feature analysis."""
        
        recommendations = []
        
        # Title optimization
        if features["title_length"] < 30:
            recommendations.append("Consider making the title longer for better engagement")
        elif features["title_length"] > 100:
            recommendations.append("Consider shortening the title for better readability")
        
        if not features["title_has_question"] and not features["title_has_exclamation"]:
            recommendations.append("Add a question or exclamation to make title more engaging")
        
        # Content optimization
        if features["description_length"] < 50:
            recommendations.append("Add more detail to the description")
        
        if features["hashtag_count"] < 3:
            recommendations.append("Add more relevant hashtags to increase discoverability")
        elif features["hashtag_count"] > 10:
            recommendations.append("Reduce number of hashtags to avoid looking spammy")
        
        # Timing optimization
        if features["is_weekend"]:
            recommendations.append("Consider posting on weekdays for potentially better engagement")
        
        if features["hour_of_day"] < 8 or features["hour_of_day"] > 22:
            recommendations.append("Consider posting during peak hours (8am-10pm)")
        
        # Quality optimization
        if features["quality_score"] < 0.7:
            recommendations.append("Improve content quality score before publishing")
        
        if not features["has_hook"]:
            recommendations.append("Add an engaging hook in the first 3 seconds")
        
        if not features["has_cta"]:
            recommendations.append("Include a clear call-to-action")
        
        # Performance prediction feedback
        if predicted_engagement < 0.02:
            recommendations.append("Low engagement predicted - consider major content revisions")
        elif predicted_engagement > 0.1:
            recommendations.append("High engagement predicted - great content!")
        
        return recommendations
    
    def _load_models(self):
        """Load existing models from disk."""
        
        if not os.path.exists(self.model_path):
            return
        
        for filename in os.listdir(self.model_path):
            if filename.endswith("_model.pkl"):
                platform = filename.replace("_model.pkl", "")
                model_file = os.path.join(self.model_path, filename)
                
                try:
                    with open(model_file, 'rb') as f:
                        model_data = pickle.load(f)
                    
                    self.models[platform] = model_data
                    logger.info(f"Loaded {platform} performance model")
                    
                except Exception as e:
                    logger.error(f"Failed to load model {filename}: {e}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all trained models."""
        
        status = {}
        
        for platform, model_data in self.models.items():
            status[platform] = {
                "model_type": model_data["model_type"],
                "r2_score": model_data["r2_score"],
                "training_samples": model_data["training_samples"],
                "trained_at": model_data["trained_at"].isoformat(),
                "feature_count": len(model_data["feature_names"])
            }
        
        return {
            "models_available": list(self.models.keys()),
            "model_details": status,
            "total_models": len(self.models)
        }
    
    def retrain_all_models(self) -> Dict[str, Any]:
        """Retrain all models with latest data."""
        
        platforms = ["youtube", "tiktok", "instagram", "reddit", "pinterest"]
        results = {}
        
        for platform in platforms:
            try:
                result = self.train_model(platform)
                results[platform] = result
            except Exception as e:
                results[platform] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results


# Global AI instance
performance_ai = PerformancePredictionAI()


def predict_post_performance(post: Post, asset: Asset) -> Dict[str, Any]:
    """Convenience function to predict post performance."""
    return performance_ai.predict_performance(post, asset)


def train_performance_models() -> Dict[str, Any]:
    """Convenience function to train all performance models."""
    return performance_ai.retrain_all_models()


def get_ai_model_status() -> Dict[str, Any]:
    """Convenience function to get AI model status."""
    return performance_ai.get_model_status()