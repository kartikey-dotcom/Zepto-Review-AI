import os
import json
import logging
from typing import Dict, Any, List, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """
    High-Speed In-Memory & Disk Cache Manager for Zepto Reviews AI.
    Loads and serves pre-compiled review cache for ultra-fast API responses.
    """

    _CACHE: Optional[Dict[str, Any]] = None
    CACHE_FILE_PATH = os.path.join(os.getcwd(), "reviews_cache.json")

    @classmethod
    def load_cache(cls) -> Dict[str, Any]:
        """Loads the review cache into memory."""
        if cls._CACHE is not None:
            return cls._CACHE

        if os.path.exists(cls.CACHE_FILE_PATH):
            try:
                with open(cls.CACHE_FILE_PATH, "r", encoding="utf-8") as f:
                    cls._CACHE = json.load(f)
                logger.info(f"Loaded {cls._CACHE.get('summary', {}).get('total_cached_reviews')} reviews into memory cache.")
                return cls._CACHE
            except Exception as e:
                logger.error(f"Failed to load cache file: {e}")

        cls._CACHE = {
            "summary": {"total_cached_reviews": 0},
            "reviews": []
        }
        return cls._CACHE

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Returns cache summary analytics."""
        cache = cls.load_cache()
        return cache.get("summary", {})

    @classmethod
    def get_cached_reviews(cls, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Returns paginated reviews directly from in-memory cache."""
        cache = cls.load_cache()
        reviews = cache.get("reviews", [])
        total = len(reviews)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = reviews[start_idx:end_idx]

        return {
            "total_count": total,
            "page": page,
            "page_size": page_size,
            "reviews": paginated
        }
