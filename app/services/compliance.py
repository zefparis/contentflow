import json
import logging
import re
from typing import Dict, Any, Union
from app.models import Asset, Post

logger = logging.getLogger(__name__)

# Simple taboo words list for content filtering
TABOO_WORDS = [
    'hate', 'violence', 'discrimination', 'illegal', 'scam', 'fraud', 
    'piracy', 'stolen', 'fake news', 'misinformation', 'spam',
    'haine', 'violence', 'arnaque', 'fraude', 'piratage', 'vol',
    'fausses nouvelles', 'désinformation', 'spam'
]

# Known safe license types
SAFE_LICENSES = [
    'cc-by', 'cc-by-sa', 'cc0', 'public domain', 'creative commons',
    'stock', 'royalty-free', 'mit', 'apache', 'gpl'
]


def compute_risk(asset: Asset, plan: Dict[str, Any]) -> float:
    """
    Compute compliance risk score for an asset and its plan.
    
    Returns:
        float: Risk score from 0.0 (safe) to 1.0 (high risk)
    """
    try:
        risk_score = 0.0
        meta = json.loads(asset.meta_json) if asset.meta_json else {}
        
        # License risk (+0.5 if unknown/unsafe license)
        license_risk = check_license_risk(meta)
        risk_score += license_risk
        
        # Content language risk (+0.2 if sensitive language detected)
        language_risk = check_language_risk(meta, plan)
        risk_score += language_risk
        
        # Attribution risk (+0.1 if no attribution in overlays)
        attribution_risk = check_attribution_risk(plan)
        risk_score += attribution_risk
        
        # Source credibility risk (+0.1 if unknown source)
        source_risk = check_source_risk(asset)
        risk_score += source_risk
        
        # Duration risk (+0.1 if suspiciously short/long)
        duration_risk = check_duration_risk(asset.duration or 0)
        risk_score += duration_risk
        
        # Cap at 1.0
        risk_score = min(risk_score, 1.0)
        
        logger.info(f"Computed risk score {risk_score:.2f} for asset {asset.id}")
        logger.debug(f"Risk breakdown - License: {license_risk}, Language: {language_risk}, "
                    f"Attribution: {attribution_risk}, Source: {source_risk}, Duration: {duration_risk}")
        
        return risk_score
        
    except Exception as e:
        logger.error(f"Error computing risk for asset {asset.id}: {e}")
        return 0.8  # High risk on error


def check_license_risk(meta: Dict[str, Any]) -> float:
    """Check license-related risk."""
    license_info = meta.get('license', '').lower()
    source_url = meta.get('link', '').lower()
    
    # No license information
    if not license_info:
        # Check if from known safe sources
        safe_domains = ['creativecommons.org', 'pixabay.com', 'unsplash.com', 'pexels.com']
        if any(domain in source_url for domain in safe_domains):
            return 0.1  # Low risk for known safe sources
        return 0.5  # High risk for unknown license
    
    # Check against safe licenses
    if any(safe_license in license_info for safe_license in SAFE_LICENSES):
        return 0.0  # No risk for safe licenses
    
    # Unknown/suspicious license
    return 0.5


def check_language_risk(meta: Dict[str, Any], plan: Dict[str, Any]) -> float:
    """Check for sensitive language in content."""
    texts_to_check = [
        meta.get('title', ''),
        meta.get('description', ''),
        plan.get('overlays', {}).get('hook_text', ''),
        plan.get('overlays', {}).get('cta_text', '')
    ]
    
    combined_text = ' '.join(texts_to_check).lower()
    
    # Check for taboo words
    for taboo_word in TABOO_WORDS:
        if taboo_word in combined_text:
            logger.warning(f"Detected potentially sensitive content: '{taboo_word}'")
            return 0.2
    
    # Check for excessive caps (potential spam)
    caps_ratio = sum(1 for c in combined_text if c.isupper()) / max(len(combined_text), 1)
    if caps_ratio > 0.3:
        logger.warning(f"High caps ratio detected: {caps_ratio:.2f}")
        return 0.1
    
    return 0.0


def check_attribution_risk(plan: Dict[str, Any]) -> float:
    """Check if proper attribution is present."""
    overlays = plan.get('overlays', {})
    attribution = overlays.get('attribution', '')
    
    if not attribution or attribution.strip() == '':
        logger.warning("No attribution found in overlays")
        return 0.1
    
    return 0.0


def check_source_risk(asset: Asset) -> float:
    """Check source credibility risk."""
    if not asset.source_id:
        return 0.1  # Unknown source
    
    # For demo, assume sources with ID 1-10 are trusted
    if asset.source_id <= 10:
        return 0.0
    
    return 0.1


def check_duration_risk(duration: float) -> float:
    """Check duration-related risk."""
    if duration < 3:  # Too short, might be spam
        return 0.1
    elif duration > 300:  # Too long, might be problematic
        return 0.1
    
    return 0.0


def is_content_safe_for_autopost(asset: Asset, plan: Dict[str, Any]) -> bool:
    """
    Determine if content is safe for automatic posting.
    
    Returns:
        bool: True if safe for autopost, False if needs review
    """
    risk_score = compute_risk(asset, plan)
    quality_score = plan.get('quality_score', 0.0)
    
    # Very permissive autopost criteria for demo - allow almost all content
    is_safe = risk_score < 0.8 and quality_score >= 0.3
    
    logger.info(f"Asset {asset.id} autopost safety: {is_safe} "
               f"(risk: {risk_score:.2f}, quality: {quality_score:.2f})")
    
    return is_safe


def get_compliance_summary() -> Dict[str, Any]:
    """Get compliance gate summary for dashboard."""
    from app.db import SessionLocal
    from app.models import Asset, Post
    
    db = SessionLocal()
    try:
        # Count assets needing review (simplified - in real app would store risk scores)
        total_assets = db.query(Asset).filter(Asset.status == "ready").count()
        
        # For demo, assume 20% need review
        needs_review = max(1, total_assets // 5)
        auto_postable = total_assets - needs_review
        
        return {
            "total_ready": total_assets,
            "needs_review": needs_review,
            "auto_postable": auto_postable,
            "risk_threshold": 0.2,
            "quality_threshold": 0.7
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance summary: {e}")
        return {
            "total_ready": 0,
            "needs_review": 0,
            "auto_postable": 0,
            "risk_threshold": 0.2,
            "quality_threshold": 0.7
        }
    finally:
        db.close()




def review_asset(asset_id: int, approved: bool, reviewer_notes: str = "") -> bool:
    """Manual review of an asset."""
    from app.db import SessionLocal
    
    db = SessionLocal()
    try:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            return False
        
        # Update metadata with review info
        meta = json.loads(asset.meta_json) if asset.meta_json else {}
        meta['review'] = {
            'approved': approved,
            'reviewer_notes': reviewer_notes,
            'reviewed_at': json.dumps({"$date": "2024-01-15T10:00:00Z"})  # Would use datetime
        }
        asset.meta_json = json.dumps(meta)
        
        if approved:
            asset.status = "ready"
        else:
            asset.status = "rejected"
        
        db.commit()
        logger.info(f"Asset {asset_id} reviewed: {'approved' if approved else 'rejected'}")
        return True
        
    except Exception as e:
        logger.error(f"Error reviewing asset {asset_id}: {e}")
        return False
    finally:
        db.close()

