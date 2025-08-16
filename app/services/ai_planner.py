import json
import logging
import re
import os
from typing import Dict, Any, List
from app.models import Asset, Post, Experiment
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Import ContentFlow configuration
try:
    from app.services.contentflow_config import get_config
    contentflow_config = get_config()
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger.warning("ContentFlow config not available")

# OpenAI integration
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    openai_available = True
except ImportError:
    client = None
    openai_available = False
    logger.warning("OpenAI not available - using fallback methods")


def generate_plan_heuristic(asset: Asset) -> Dict[str, Any]:
    """
    Generate AI plan using heuristic approach.
    
    Returns plan with segments, overlays, hashtags, language, quality_score
    """
    try:
        meta = json.loads(asset.meta_json) if asset.meta_json else {}
        title = meta.get('title', '')
        description = meta.get('description', '')
        
        # Basic duration handling
        duration = asset.duration or 30
        
        # Generate segments (≤30s, HOOK ≤5s, CTA at 20-28s)
        segments = []
        if duration > 30:
            # Cut to 30 seconds max, hook at start
            segments = [{"start": 0, "end": min(duration, 30)}]
        else:
            segments = [{"start": 0, "end": duration}]
        
        # Generate overlays with ContentFlow optimized hooks
        hook_variants = generate_hooks_for_asset(asset)
        
        # Use ContentFlow niche-specific content if available
        if CONFIG_AVAILABLE:
            # Try to detect niche from keywords or title
            detected_niche = detect_niche_from_content(title + " " + description)
            if detected_niche:
                niche_hook = contentflow_config.get_hook_for_niche(detected_niche)
                hook_variants.insert(0, niche_hook)  # Prioritize niche-specific hooks
        overlays = {
            "hook_text": hook_variants[0] if hook_variants else generate_hook_text(title, description),
            "hook_variants": hook_variants,
            "cta_text": "Suivez pour plus de contenu tech! 👆",
            "attribution": "ContentFlow"
        }
        
        # Generate hashtags from keywords and title
        hashtags = generate_hashtags(title, description, asset.keywords)
        
        # Language detection/inheritance
        language = asset.lang or "fr"
        
        # Calculate quality score (0..1)
        quality_score = calculate_quality_score(asset, title, description, duration)
        
        plan = {
            "segments": segments,
            "overlays": overlays,
            "hashtags": hashtags,
            "language": language,
            "quality_score": quality_score,
            "srt": None,  # Subtitle file path if available
            "video_format": "vertical",  # 1080x1920
            "audio_enabled": True
        }
        
        logger.info(f"Generated plan for asset {asset.id}, quality: {quality_score:.2f}")
        return plan
        
    except Exception as e:
        logger.error(f"Error generating plan for asset {asset.id}: {e}")
        return {
            "segments": [{"start": 0, "end": 15}],
            "overlays": {"hook_text": "Découvrez ce contenu!", "cta_text": "Suivez-nous!", "attribution": "ContentFlow"},
            "hashtags": ["#tech", "#innovation"],
            "language": "fr",
            "quality_score": 0.5
        }

def detect_niche_from_content(content: str) -> str:
    """Detect niche from content using keyword matching"""
    if not CONFIG_AVAILABLE:
        return None
        
    content_lower = content.lower()
    
    # Define niche keywords
    niche_keywords = {
        "vpn": ["vpn", "proxy", "sécurité", "confidentialité", "privacy", "netflix", "géolocalisation", "wifi", "streaming"],
        "hosting": ["hébergement", "serveur", "hosting", "vps", "cloud", "wordpress", "domain", "ssl", "performance", "nvme"],
        "ai_saas": ["ia", "ai", "saas", "automation", "nocode", "chatbot", "agent", "llm", "prompt", "productivité"]
    }
    
    # Score each niche
    niche_scores = {}
    for niche, keywords in niche_keywords.items():
        score = sum(1 for keyword in keywords if keyword in content_lower)
        if score > 0:
            niche_scores[niche] = score
    
    # Return highest scoring niche
    if niche_scores:
        return max(niche_scores, key=niche_scores.get)
    
    return None


def generate_hooks_for_asset(asset: Asset) -> List[str]:
    """Generate multiple hook variants using OpenAI for A/B testing."""
    if not openai_available or not client:
        return [
            "🔥 Découvrez cette innovation incroyable!",
            "⚡ L'IA qui va tout changer!",
            "🚀 Une révolution tech en 30 secondes!"
        ]
    
    try:
        meta = json.loads(asset.meta_json) if asset.meta_json else {}
        title = meta.get('title', '')
        description = meta.get('description', '')
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Using the newest model
            messages=[
                {
                    "role": "system", 
                    "content": "Tu es un expert en création de contenu viral pour les réseaux sociaux. Génère des accroches captivantes en français de maximum 8 mots pour les 5 premières secondes d'une vidéo. Utilise des émojis et crée de l'urgence/curiosité."
                },
                {
                    "role": "user",
                    "content": f"Titre: {title}\nDescription: {description}\n\nGénère 5 accroches différentes au format JSON: {{\"hooks\": [\"accroche1\", \"accroche2\", ...]}}"
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=200
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('hooks', [])[:5]
        
    except Exception as e:
        logger.error(f"OpenAI hook generation failed: {e}")
        return [
            "🔥 Découvrez cette innovation incroyable!",
            "⚡ L'IA qui va tout changer!",
            "🚀 Une révolution tech en 30 secondes!"
        ]


def generate_hook_text(title: str, description: str) -> str:
    """Generate engaging hook text for the first 5 seconds."""
    hooks = [
        f"🚀 {title[:50]}...",
        f"💡 Saviez-vous que {title.lower()[:40]}?",
        f"🔥 BREAKING: {title[:45]}",
        f"⚡ Découvrez: {title[:45]}",
        f"🎯 {title[:50]}"
    ]
    
    # Choose hook based on title content
    if any(word in title.lower() for word in ['nouvelle', 'nouveau', 'breaking', 'découverte']):
        return hooks[2]  # BREAKING
    elif any(word in title.lower() for word in ['guide', 'comment', 'tutorial']):
        return hooks[3]  # Découvrez
    else:
        return hooks[0]  # Default rocket


def generate_hashtags(title: str, description: str, keywords: str = None) -> List[str]:
    """Generate relevant hashtags from content."""
    hashtags = set()
    
    # Base hashtags
    hashtags.update(["#tech", "#innovation"])
    
    # Extract from keywords if available
    if keywords:
        keyword_list = [k.strip() for k in keywords.split(',')]
        for keyword in keyword_list[:4]:  # Max 4 from keywords
            if len(keyword) > 3:
                hashtags.add(f"#{keyword.lower()}")
    
    # Extract from title - look for tech terms
    tech_terms = {
        'intelligence artificielle': '#ia',
        'machine learning': '#ml',
        'blockchain': '#blockchain',
        'crypto': '#crypto',
        'startup': '#startup',
        'fintech': '#fintech',
        'deeptech': '#deeptech',
        'saas': '#saas',
        'api': '#api',
        'cloud': '#cloud'
    }
    
    title_lower = title.lower()
    for term, tag in tech_terms.items():
        if term in title_lower:
            hashtags.add(tag)
    
    # Limit to 6 hashtags max
    return list(hashtags)[:6]


def calculate_quality_score(asset: Asset, title: str, description: str, duration: float) -> float:
    """Calculate content quality score (0..1)."""
    score = 0.0
    
    # Duration score (+0.1 if in optimal range 10-30s)
    if 10 <= duration <= 30:
        score += 0.2
    elif duration > 5:
        score += 0.1
    
    # Title quality (+0.2 for good title)
    if title and len(title) > 10:
        score += 0.1
        if any(word in title.lower() for word in ['innovation', 'découverte', 'nouveau', 'guide']):
            score += 0.1
    
    # Description quality (+0.2 for good description)
    if description and len(description) > 50:
        score += 0.1
        if len(description) > 100:
            score += 0.1
    
    # Keywords presence (+0.1)
    if asset.keywords:
        score += 0.1
    
    # Language detection (+0.1 if proper language)
    if asset.lang in ['fr', 'en']:
        score += 0.1
    
    # Source quality (+0.1 for known good sources)
    if asset.source_id:
        score += 0.1
    
    # Cap at 0.9 max (never perfect)
    return min(score, 0.9)


def choose_variants_for_ab(post: Post, db: Session) -> List[Dict[str, Any]]:
    """
    Generate A/B test variants for a post.
    
    Returns list of variant configurations for experimentation.
    """
    try:
        variants = []
        
        # Variant A: "Curiosité" approach
        variant_a = {
            "arm_key": f"title:curiosity:{post.platform}",
            "title": generate_curiosity_title(post.title),
            "description": generate_curiosity_description(post.description),
            "variant": "curiosity"
        }
        variants.append(variant_a)
        
        # Variant B: "Valeur" approach  
        variant_b = {
            "arm_key": f"title:value:{post.platform}",
            "title": generate_value_title(post.title),
            "description": generate_value_description(post.description),
            "variant": "value"
        }
        variants.append(variant_b)
        
        # Create Experiment records
        for variant in variants:
            experiment = Experiment(
                post_id=post.id,
                variant=variant["variant"],
                arm_key=variant["arm_key"],
                status="active",
                metrics_json=json.dumps({"clicks": 0, "views": 0, "conversions": 0})
            )
            db.add(experiment)
        
        db.commit()
        logger.info(f"Created A/B variants for post {post.id}")
        return variants
        
    except Exception as e:
        logger.error(f"Error creating A/B variants for post {post.id}: {e}")
        return []


def generate_curiosity_title(original_title: str) -> str:
    """Generate curiosity-driven title variant."""
    curiosity_prefixes = [
        "🤔 Vous ne devinerez jamais:",
        "😱 INCROYABLE:",
        "🚨 Personne ne parle de ça:",
        "💭 Et si je vous disais que:",
        "🔥 Le secret que personne ne dit:"
    ]
    
    import random
    prefix = random.choice(curiosity_prefixes)
    
    # Truncate original title to fit
    max_length = 100 - len(prefix) - 3
    truncated = original_title[:max_length] + "..." if len(original_title) > max_length else original_title
    
    return f"{prefix} {truncated}"


def generate_value_title(original_title: str) -> str:
    """Generate value-focused title variant."""
    value_prefixes = [
        "💡 Apprenez:",
        "🎯 Découvrez comment:",
        "✅ Guide complet:",
        "📈 Boostez vos résultats avec:",
        "🏆 Maîtrisez:"
    ]
    
    import random
    prefix = random.choice(value_prefixes)
    
    max_length = 100 - len(prefix) - 1
    truncated = original_title[:max_length]
    
    return f"{prefix} {truncated}"


def generate_curiosity_description(original_description: str) -> str:
    """Generate curiosity-driven description variant."""
    if not original_description:
        return "Vous allez être surpris par ce que vous découvrirez dans cette vidéo..."
    
    curiosity_endings = [
        "...et la suite va vous surprendre! 👀",
        "...mais ce n'est que le début! 🤯", 
        "...attendez de voir la suite! 😮",
        "...vous ne vous attendez pas à la fin! 🎬"
    ]
    
    import random
    ending = random.choice(curiosity_endings)
    
    # Truncate and add curiosity ending
    max_length = 200 - len(ending)
    truncated = original_description[:max_length]
    
    return truncated + ending


def generate_value_description(original_description: str) -> str:
    """Generate value-focused description variant."""
    if not original_description:
        return "Dans cette vidéo, vous découvrirez des insights précieux et actionnables."
    
    value_endings = [
        "\n\n✅ Conseils pratiques\n✅ Exemples concrets\n✅ À appliquer immédiatement",
        "\n\n🎯 Ce que vous apprendrez:\n• Techniques éprouvées\n• Stratégies efficaces",
        "\n\n💪 Transformez vos résultats avec ces méthodes testées.",
        "\n\n🚀 Boostez votre expertise avec ces insights exclusifs."
    ]
    
    import random
    ending = random.choice(value_endings)
    
    max_length = 200 - len(ending)
    truncated = original_description[:max_length]
    
    return truncated + ending