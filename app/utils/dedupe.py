"""Image deduplication utilities using perceptual hashing."""

import io
from typing import Optional

try:
    import httpx
    from PIL import Image
    import imagehash
    DEDUPE_AVAILABLE = True
except ImportError:
    DEDUPE_AVAILABLE = False


def phash_from_url(url: str) -> Optional[str]:
    """Generate perceptual hash from image URL."""
    if not DEDUPE_AVAILABLE or not url:
        return None
    
    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(url)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            return str(imagehash.phash(img))
    except Exception:
        return None


def hamming(a: str, b: str) -> int:
    """Calculate Hamming distance between two hashes."""
    if not a or not b or not DEDUPE_AVAILABLE:
        return 999
    
    try:
        return imagehash.hex_to_hash(a) - imagehash.hex_to_hash(b)
    except Exception:
        return 999