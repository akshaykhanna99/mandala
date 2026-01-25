"""Caching layer for intelligence retrieval.

Provides simple in-memory caching to reduce database load for repeated queries.
Cache is invalidated when new data is refreshed.
"""
from typing import Optional, Tuple, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import json

from .geo_risk_characterization import AssetProfile
from .geo_risk_theme_mapper import ThemeRelevance
from .geo_risk_intelligence import retrieve_intelligence, IntelligenceSignal, IntelligenceRetrievalResult


# Simple in-memory cache
_cache: dict[str, Tuple[IntelligenceRetrievalResult, datetime]] = {}
_cache_ttl = timedelta(minutes=10)  # Cache for 10 minutes


def _make_cache_key(
    profile: AssetProfile,
    themes: List[ThemeRelevance],
    days_lookback: int,
    use_semantic_filtering: bool,
    semantic_threshold: float,
    use_batch_validation: bool
) -> str:
    """Generate cache key from query parameters."""
    # Create a hash of the relevant parameters
    key_data = {
        "country": profile.country,
        "region": profile.region,
        "sector": profile.sector,
        "asset_type": profile.asset_type,
        "themes": [t.theme for t in themes],
        "days_lookback": days_lookback,
        "use_semantic_filtering": use_semantic_filtering,
        "semantic_threshold": semantic_threshold,
        "use_batch_validation": use_batch_validation,
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def retrieve_intelligence_cached(
    profile: AssetProfile,
    themes: List[ThemeRelevance],
    days_lookback: int | None = None,
    max_signals: int | None = None,
    use_cache: bool = True,
    use_semantic_filtering: bool | None = None,
    semantic_threshold: float | None = None,
    use_batch_validation: bool | None = None,
) -> IntelligenceRetrievalResult:
    """
    Retrieve intelligence signals with caching.

    Args:
        profile: Asset profile
        themes: Relevant themes
        days_lookback: Days to look back (uses settings default if None)
        max_signals: Maximum signals to return (uses settings default if None)
        use_cache: Whether to use cache (default True)
        use_semantic_filtering: Use Claude for semantic filtering (uses settings default if None)
        semantic_threshold: Minimum semantic relevance to pass (uses settings default if None)
        use_batch_validation: Use Claude for batch validation (Phase 2, uses settings default if None)

    Returns:
        List of intelligence signals
    """
    # Get defaults from settings if not provided
    from .scoring_settings_service import get_active_scoring_settings
    settings = get_active_scoring_settings()

    if days_lookback is None:
        days_lookback = settings.get("days_lookback_default", 90) if settings else 90
    if max_signals is None:
        max_signals = settings.get("max_signals_default", 20) if settings else 20
    if use_semantic_filtering is None:
        use_semantic_filtering = settings.get("use_semantic_filtering", True) if settings else True
    if semantic_threshold is None:
        semantic_threshold = settings.get("semantic_threshold", 0.6) if settings else 0.6
    if use_batch_validation is None:
        use_batch_validation = settings.get("use_batch_validation", True) if settings else True

    if not use_cache:
        return retrieve_intelligence(
            profile, themes, days_lookback, max_signals,
            use_semantic_filtering, semantic_threshold, use_batch_validation
        )

    cache_key = _make_cache_key(
        profile, themes, days_lookback,
        use_semantic_filtering, semantic_threshold, use_batch_validation
    )

    # Check cache
    if cache_key in _cache:
        cached_result, cached_time = _cache[cache_key]

        # Check if cache is still valid
        if datetime.now() - cached_time < _cache_ttl:
            # Return cached results (limit signals to max_signals)
            if isinstance(cached_result, IntelligenceRetrievalResult):
                # Return full result with limited signals
                return IntelligenceRetrievalResult(
                    signals=cached_result.signals[:max_signals],
                    web_searches=cached_result.web_searches,
                )
            else:
                # Backward compatibility: old cache format (just signals)
                return IntelligenceRetrievalResult(
                    signals=cached_result[:max_signals] if isinstance(cached_result, list) else [],
                    web_searches=[],
                )
        else:
            # Cache expired, remove it
            del _cache[cache_key]

    # Cache miss or expired, fetch fresh data
    result = retrieve_intelligence(
        profile, themes, days_lookback, max_signals,
        use_semantic_filtering, semantic_threshold, use_batch_validation
    )

    # Store full result in cache
    _cache[cache_key] = (result, datetime.now())

    return result


def invalidate_cache():
    """Invalidate all cached intelligence data.
    
    Call this when new data is refreshed (e.g., after /refresh endpoint).
    """
    global _cache
    _cache.clear()


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        "cache_size": len(_cache),
        "cache_ttl_minutes": _cache_ttl.total_seconds() / 60,
        "cached_keys": list(_cache.keys()),
    }
