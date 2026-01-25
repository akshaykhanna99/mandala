"""Scoring functions for intelligence signals.

This module provides scoring functions for intelligence signals based on:
- Recency (exponential decay)
- Source quality
- Activity levels
- Multi-factor combination

All scoring parameters are loaded from database settings with fallback to defaults.
"""
import math
from datetime import datetime
from typing import Dict, Optional
from .scoring_settings_service import get_active_scoring_settings


# Default source quality scores (fallback if database settings not available)
DEFAULT_SOURCE_QUALITY_SCORES: Dict[str, float] = {
    "Reuters": 1.0,
    "BBC": 1.0,
    "Financial Times": 0.95,
    "The Guardian": 0.9,
    "The New York Times": 0.95,
    "The Wall Street Journal": 0.95,
    "Bloomberg": 0.9,
    "Associated Press": 0.95,
    "Al Jazeera": 0.85,
    "CNN": 0.85,
    "The Economist": 0.9,
    "Foreign Policy": 0.85,
    "Foreign Affairs": 0.85,
    "The Diplomat": 0.8,
    "default": 0.7,
}

# Default activity level scores (fallback if database settings not available)
DEFAULT_ACTIVITY_LEVEL_SCORES: Dict[str, float] = {
    "Critical": 1.0,
    "High": 0.8,
    "Medium": 0.5,
    "Low": 0.2,
    "default": 0.3,
}


def _get_source_quality_scores() -> Dict[str, float]:
    """Get source quality scores from database or defaults."""
    settings = get_active_scoring_settings()
    if settings and settings.get("source_quality_scores"):
        return settings["source_quality_scores"]
    return DEFAULT_SOURCE_QUALITY_SCORES


def _get_activity_level_scores() -> Dict[str, float]:
    """Get activity level scores from database or defaults."""
    settings = get_active_scoring_settings()
    if settings and settings.get("activity_level_scores"):
        return settings["activity_level_scores"]
    return DEFAULT_ACTIVITY_LEVEL_SCORES


def get_source_quality_score(source_name: str) -> float:
    """
    Get quality score for a source (from database settings or defaults).
    
    Args:
        source_name: Name of the source
    
    Returns:
        Quality score (0.0 to 1.0)
    """
    source_scores = _get_source_quality_scores()
    
    # Try exact match first
    if source_name in source_scores:
        return source_scores[source_name]
    
    # Try case-insensitive match
    source_lower = source_name.lower()
    for name, score in source_scores.items():
        if name.lower() == source_lower:
            return score
    
    # Check if source name contains a known source
    for name, score in source_scores.items():
        if name.lower() in source_lower or source_lower in name.lower():
            return score
    
    # Default score for unknown sources
    return source_scores.get("default", 0.7)


def get_activity_level_score(activity_level: str) -> float:
    """
    Get score for country activity level (from database settings or defaults).
    
    Args:
        activity_level: Activity level string (Critical/High/Medium/Low)
    
    Returns:
        Activity score (0.0 to 1.0)
    """
    activity_scores = _get_activity_level_scores()
    return activity_scores.get(activity_level, activity_scores.get("default", 0.3))


def calculate_recency_score(published_at: datetime | str, days_lookback: int = 90) -> float:
    """
    Calculate recency score with exponential decay (using database settings or defaults).
    
    Newer signals are weighted higher. The decay function:
    - Today: 1.0
    - 7 days ago: ~0.8
    - 30 days ago: ~0.5
    - 90 days ago: ~0.1
    
    Args:
        published_at: Publication date (datetime or ISO string)
        days_lookback: Maximum days to look back (default 90)
    
    Returns:
        Recency score (0.0 to 1.0)
    """
    # Parse date if string
    if isinstance(published_at, str):
        pub_date = _parse_date(published_at)
        if not pub_date:
            return 0.0  # Can't parse = old/unknown
    else:
        pub_date = published_at
    
    if not pub_date:
        return 0.0
    
    # Calculate days ago
    days_ago = (datetime.now() - pub_date).days
    
    # If beyond lookback window, return 0
    if days_ago > days_lookback:
        return 0.0
    
    # Get decay constant from settings or use default
    settings = get_active_scoring_settings()
    decay_constant = settings.get("recency_decay_constant", 30.0) if settings else 30.0
    
    # Exponential decay: e^(-days_ago / decay_constant)
    recency_score = math.exp(-days_ago / decay_constant)
    
    return max(0.0, min(1.0, recency_score))


def _parse_date(date_str: str) -> datetime | None:
    """Parse various date formats."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def calculate_final_score(
    base_relevance: float,
    theme_match: float,
    recency_score: float,
    source_quality: float = 0.7,
    activity_level: float = 0.0,
) -> float:
    """
    Calculate final weighted score for an intelligence signal (using database settings or defaults).
    
    Args:
        base_relevance: Country/region/sector match score (0.0 to 1.0)
        theme_match: Theme keyword/semantic match score (0.0 to 1.0)
        recency_score: Recency score from calculate_recency_score (0.0 to 1.0)
        source_quality: Source quality score (0.0 to 1.0), default 0.7
        activity_level: Activity level score (0.0 to 1.0), default 0.0 (only for snapshots)
    
    Returns:
        Final weighted score (0.0 to 1.0)
    """
    # Get weights from database settings or use defaults
    settings = get_active_scoring_settings()
    if settings:
        weights = {
            "base_relevance": settings.get("weight_base_relevance", 0.3),
            "theme_match": settings.get("weight_theme_match", 0.25),
            "recency": settings.get("weight_recency", 0.2),
            "source_quality": settings.get("weight_source_quality", 0.15),
            "activity_level": settings.get("weight_activity_level", 0.1),
        }
    else:
        weights = {
            "base_relevance": 0.3,
            "theme_match": 0.25,
            "recency": 0.2,
            "source_quality": 0.15,
            "activity_level": 0.1,
        }
    
    # If no activity level (global items), redistribute weight to other factors
    if activity_level == 0.0:
        # Redistribute activity_level weight proportionally
        total_other_weights = sum([
            weights["base_relevance"],
            weights["theme_match"],
            weights["recency"],
            weights["source_quality"],
        ])
        scale_factor = 1.0 / total_other_weights
        adjusted_weights = {
            "base_relevance": weights["base_relevance"] * scale_factor,
            "theme_match": weights["theme_match"] * scale_factor,
            "recency": weights["recency"] * scale_factor,
            "source_quality": weights["source_quality"] * scale_factor,
        }
    else:
        adjusted_weights = weights
    
    final_score = (
        base_relevance * adjusted_weights.get("base_relevance", weights["base_relevance"]) +
        theme_match * adjusted_weights.get("theme_match", weights["theme_match"]) +
        recency_score * adjusted_weights.get("recency", weights["recency"]) +
        source_quality * adjusted_weights.get("source_quality", weights["source_quality"]) +
        activity_level * weights["activity_level"]
    )
    
    return max(0.0, min(1.0, final_score))
