"""
Risk assessment module for content evaluation.
"""
import re
from typing import Union, Dict, Any
from app.models import Post
from app.utils.logger import logger

# Simple taboo words list for content filtering
TABOO_WORDS = [
    'hate', 'violence', 'discrimination', 'illegal', 'scam', 'fraud', 
    'piracy', 'stolen', 'fake news', 'misinformation', 'spam',
    'haine', 'violence', 'arnaque', 'fraude', 'piratage', 'vol',
    'fausses nouvelles', 'désinformation', 'spam'
]

def calculate_risk_score(content: Union[Post, Dict[str, Any]]) -> float:
    """
    Calculate risk score for a post or content dictionary.
    
    Args:
        content: Either a Post object or a dictionary containing post content
        
    Returns:
        float: Risk score between 0.0 (safe) and 1.0 (high risk)
    """
    try:
        # Extract text content
        if hasattr(content, 'title'):  # Post object
            text = f"{content.title or ''} {getattr(content, 'description', '') or ''} {getattr(content, 'content', '') or ''}"
        elif isinstance(content, dict):  # Dictionary
            text = f"{content.get('title', '')} {content.get('description', '')} {content.get('content', '')}"
        else:
            logger.warning(f"Unsupported content type for risk calculation: {type(content)}")
            return 0.5  # Medium risk for unknown content types
        
        text = text.lower()
        
        # Initialize risk score
        risk_score = 0.0
        
        # Check for taboo words
        for word in TABOO_WORDS:
            if word.lower() in text:
                risk_score += 0.1
        
        # Check for excessive length (potential spam)
        if len(text) > 5000:
            risk_score += 0.2
            
        # Check for excessive links (potential spam)
        link_count = len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text))
        if link_count > 3:
            risk_score += 0.1 * min(link_count, 5)  # Max 0.5 for links
            
        # Check for excessive punctuation (potential spam)
        if sum(1 for c in text if c in '!?') > 10:
            risk_score += 0.1
            
        # Cap the risk score at 1.0
        return min(risk_score, 1.0)
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {e}")
        return 0.5  # Default to medium risk if there's an error

__all__ = ['calculate_risk_score']
