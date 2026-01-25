"""Intelligence retrieval - queries existing data sources filtered by asset characteristics.

This module implements the intelligence retrieval pipeline with:
- Database-level filtering for performance
- Claude-powered semantic filtering (Phase 1 enhancement)
- Multi-factor scoring (relevance, recency, source quality, activity level)
- Theme-based signal matching
- Signal aggregation and prioritization

Pipeline:
1. Filter data sources at database level (by country, region, date)
2. [NEW] Semantic pre-filtering with Claude API (optional, high-quality filtering)
3. Score each signal using multi-factor scoring
4. Match signals to relevant themes
5. Aggregate and prioritize signals
6. Return top N most relevant signals
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from functools import lru_cache
import os
from typing import TYPE_CHECKING

from .geo_risk_characterization import AssetProfile
from .geo_risk_theme_mapper import ThemeRelevance, get_geopolitical_themes
from .data_store_filtered import load_global_items_filtered, load_snapshots_filtered
from .intelligence_scoring import (
    calculate_recency_score,
    get_source_quality_score,
    get_activity_level_score,
    calculate_final_score,
)
from .models import GlobalItem, CountrySnapshot
from .theme_web_search import (
    search_theme_web,
    convert_web_results_to_signals,
)
from .scoring_settings_service import get_active_scoring_settings

# Import Claude services (optional, graceful fallback if not available)
try:
    from .claude_intelligence_service import ClaudeIntelligenceService
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("Claude service not available - using keyword-based filtering only")

try:
    from .claude_batch_validation_service import ClaudeBatchValidationService
    BATCH_VALIDATION_AVAILABLE = True
except ImportError:
    BATCH_VALIDATION_AVAILABLE = False
    print("Batch validation service not available")


@dataclass
class IntelligenceSignal:
    """A single intelligence signal relevant to an asset."""
    source: str  # "global_item", "country_snapshot", or "web_search"
    title: str
    summary: str
    topic: str
    relevance_score: float  # 0.0 to 1.0 (final weighted score)
    theme_match: str | None  # Which theme this relates to
    published_at: str
    url: str | None = None
    country: str | None = None
    activity_level: str | None = None  # For country snapshots

    # Scoring breakdown (for debugging/transparency)
    base_relevance: float = 0.0
    theme_match_score: float = 0.0
    recency_score: float = 0.0
    source_quality: float = 0.0
    activity_level_score: float = 0.0

    # Claude semantic analysis (Phase 1 enhancement)
    semantic_relevance: float = 0.0  # Claude's relevance score (0.0-1.0)
    semantic_confidence: float = 0.0  # Claude's confidence score (0.0-1.0)
    semantic_reasoning: str = ""  # Claude's explanation

    # Batch validation (Phase 2 enhancement)
    validation_confidence: float = 1.0  # Validation confidence (0.0-1.0)
    is_corroborated: bool = False  # Confirmed by multiple sources
    is_contradicted: bool = False  # Contradicted by other signals
    corroboration_count: int = 0  # Number of corroborating signals
    evidence_quality: str = ""  # "high", "medium", "low"
    validation_reasoning: str = ""  # Validation explanation
    confidence_multiplier: float = 1.0  # Final confidence adjustment


@dataclass
class IntelligenceRetrievalResult:
    """Result from intelligence retrieval with metadata."""
    signals: List[IntelligenceSignal]
    web_searches: List[Dict[str, any]]  # List of {theme, query, results_count}


def retrieve_intelligence(
    profile: AssetProfile,
    themes: List[ThemeRelevance],
    days_lookback: Optional[int] = None,
    max_signals: Optional[int] = None,
    use_semantic_filtering: Optional[bool] = None,
    semantic_threshold: Optional[float] = None,
    use_batch_validation: Optional[bool] = None,
) -> IntelligenceRetrievalResult:
    """
    Retrieve relevant intelligence signals from global_items and country_snapshots.

    Uses database-level filtering and multi-factor scoring for optimal performance
    and relevance. Optionally uses Claude API for semantic pre-filtering and
    batch validation (Phase 2 enhancement).

    Args:
        profile: Asset profile with characteristics
        themes: List of relevant themes with relevance scores
        days_lookback: How many days back to search (default 90)
        max_signals: Maximum number of signals to return (default 20)
        use_semantic_filtering: Use Claude for semantic filtering (default True)
        semantic_threshold: Minimum semantic relevance to pass (default 0.6)
        use_batch_validation: Use Claude for batch validation (Phase 2, default True)

    Returns:
        List of intelligence signals sorted by relevance (highest first)
    """
    # Load settings from database or use defaults
    settings = get_active_scoring_settings()

    # Use settings values if parameters not provided
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
    
    signals: List[IntelligenceSignal] = []

    # Initialize Claude service if semantic filtering is enabled
    claude_service = None
    if use_semantic_filtering and CLAUDE_AVAILABLE:
        try:
            claude_service = ClaudeIntelligenceService()
            print(f"✓ Claude semantic filtering enabled (threshold: {semantic_threshold})")
        except Exception as e:
            print(f"⚠ Claude service initialization failed: {e}")
            print("Falling back to keyword-based filtering")
            claude_service = None

    # Build theme keywords for matching
    theme_keywords = _build_theme_keywords(themes)
    theme_names = [t.theme for t in themes]
    
    # Step 1: Query global items with database-level filtering
    global_items = _query_global_items(profile, days_lookback)

    # Step 2: Score and process global items with semantic filtering
    for item in global_items:
        signal = _process_global_item(item, profile, themes, theme_keywords, days_lookback)
        if signal:
            # Step 2a: Apply semantic filtering (if enabled)
            if claude_service:
                semantic_result = claude_service.analyze_signal_relevance(
                    signal_title=signal.title,
                    signal_summary=signal.summary,
                    asset_country=profile.country,
                    asset_sector=profile.sector,
                    themes=theme_names,
                    relevance_threshold=semantic_threshold,
                )

                # Update signal with Claude's analysis
                signal.semantic_relevance = semantic_result.relevance_score
                signal.semantic_confidence = semantic_result.confidence_score
                signal.semantic_reasoning = semantic_result.reasoning

                # Only keep if semantically relevant
                if not semantic_result.is_relevant:
                    continue  # Skip this signal

                # Boost theme matching if Claude identified themes
                if semantic_result.matched_themes and not signal.theme_match:
                    signal.theme_match = semantic_result.matched_themes[0]

            # Get threshold from settings
            settings = get_active_scoring_settings()
            threshold_low = settings.get("relevance_threshold_low", 0.05) if settings else 0.05
            threshold_high = settings.get("relevance_threshold_high", 0.1) if settings else 0.1
            threshold = threshold_low if len(signals) < 5 else threshold_high
            if signal.relevance_score > threshold:
                signals.append(signal)
    
    # Step 3: Query country snapshots with database-level filtering
    snapshots = _query_country_snapshots(profile, days_lookback)

    # Step 4: Score and process country snapshots with semantic filtering
    for snapshot in snapshots:
        snapshot_signals = _process_country_snapshot(
            snapshot, profile, themes, theme_keywords, days_lookback
        )

        # Get threshold from settings
        settings = get_active_scoring_settings()
        threshold_low = settings.get("relevance_threshold_low", 0.05) if settings else 0.05
        threshold_high = settings.get("relevance_threshold_high", 0.1) if settings else 0.1
        threshold = threshold_low if len(signals) < 5 else threshold_high

        for sig in snapshot_signals:
            # Step 4a: Apply semantic filtering (if enabled)
            if claude_service:
                semantic_result = claude_service.analyze_signal_relevance(
                    signal_title=sig.title,
                    signal_summary=sig.summary,
                    asset_country=profile.country,
                    asset_sector=profile.sector,
                    themes=theme_names,
                    relevance_threshold=semantic_threshold,
                )

                # Update signal with Claude's analysis
                sig.semantic_relevance = semantic_result.relevance_score
                sig.semantic_confidence = semantic_result.confidence_score
                sig.semantic_reasoning = semantic_result.reasoning

                # Only keep if semantically relevant
                if not semantic_result.is_relevant:
                    continue  # Skip this signal

                # Boost theme matching if Claude identified themes
                if semantic_result.matched_themes and not sig.theme_match:
                    sig.theme_match = semantic_result.matched_themes[0]

            if sig.relevance_score > threshold:
                signals.append(sig)
    
    # Step 5: Web search for each identified theme (top 2-3 themes to reduce clutter)
    # This provides real-time, targeted intelligence
    max_web_themes = int(os.getenv("MAX_WEB_SEARCH_THEMES", "3"))  # Reduced from 5 to 3
    top_themes = sorted(themes, key=lambda t: t.relevance_score, reverse=True)[:max_web_themes]
    web_searches = []
    
    # Get theme threshold from settings
    settings = get_active_scoring_settings()
    theme_threshold = settings.get("theme_relevance_threshold_web", 0.3) if settings else 0.3
    
    for theme in top_themes:
        if theme.relevance_score < theme_threshold:  # Skip low-relevance themes
            continue
        
        try:
            # Build query for tracking
            from .theme_web_search import _build_search_query
            query = _build_search_query(profile, theme, days_lookback)
            
            # Search web for this specific theme
            web_results = search_theme_web(profile, theme, days_lookback)
            
            # Convert to intelligence signals
            web_signals = convert_web_results_to_signals(
                web_results, profile, theme, days_lookback
            )
            
            # Track web search metadata
            web_searches.append({
                "theme": theme.theme,
                "query": query,
                "results_count": len(web_results),
                "signals_count": len(web_signals),
            })
            
            # Add to signals list
            signals.extend(web_signals)
        except Exception as e:
            # Don't fail if web search fails - continue with database results
            print(f"Web search failed for theme {theme.theme}: {e}")
            # Build query even on error for tracking
            try:
                from .theme_web_search import _build_search_query
                query = _build_search_query(profile, theme, days_lookback)
            except:
                query = f"{profile.country or profile.region} {theme.theme}"
            
            web_searches.append({
                "theme": theme.theme,
                "query": query,
                "results_count": 0,
                "signals_count": 0,
                "error": str(e),
            })
            continue
    
    # Step 6: Deduplicate signals by URL (keep highest scored)
    seen_urls = {}
    deduplicated = []
    for signal in signals:
        url = signal.url or ""
        if url and url in seen_urls:
            # Keep the one with higher relevance
            if signal.relevance_score > seen_urls[url].relevance_score:
                # Replace the existing one
                deduplicated.remove(seen_urls[url])
                deduplicated.append(signal)
                seen_urls[url] = signal
        else:
            deduplicated.append(signal)
            if url:
                seen_urls[url] = signal
    
    signals = deduplicated

    # Step 7: Sort by relevance (highest first)
    signals.sort(key=lambda x: x.relevance_score, reverse=True)

    # Step 7.5: Batch validation (Phase 2 enhancement)
    if use_batch_validation and BATCH_VALIDATION_AVAILABLE and len(signals) >= 3:
        try:
            validation_service = ClaudeBatchValidationService()
            print(f"✓ Batch validation enabled for {len(signals)} signals")

            # Convert signals to dict format for validation
            signals_for_validation = [
                {
                    "source": sig.source,
                    "title": sig.title,
                    "summary": sig.summary,
                    "relevance_score": sig.relevance_score,
                }
                for sig in signals
            ]

            # Run batch validation
            validation_result = validation_service.validate_signal_batch(
                signals=signals_for_validation,
                asset_country=profile.country,
                asset_sector=profile.sector,
            )

            print(f"  Coherence: {validation_result.overall_coherence:.2f}")
            print(f"  Contradictions: {validation_result.contradiction_count}")
            print(f"  Corroborations: {validation_result.corroboration_count}")

            # Apply validation results to signals
            validation_map = {v.signal_index: v for v in validation_result.validations}

            for idx, signal in enumerate(signals):
                validation = validation_map.get(idx)
                if not validation:
                    continue

                # Calculate confidence multiplier
                confidence_multiplier = 1.0

                # Boost for corroboration (+30%)
                if validation.is_corroborated:
                    confidence_multiplier *= 1.3

                # Penalty for contradiction (-50%)
                if validation.is_contradicted:
                    confidence_multiplier *= 0.5

                # Adjust for evidence quality
                if validation.evidence_quality == "high":
                    confidence_multiplier *= 1.2
                elif validation.evidence_quality == "low":
                    confidence_multiplier *= 0.7

                # Apply validation confidence
                confidence_multiplier *= validation.validation_confidence

                # Update signal fields
                signal.validation_confidence = validation.validation_confidence
                signal.is_corroborated = validation.is_corroborated
                signal.is_contradicted = validation.is_contradicted
                signal.corroboration_count = len(validation.corroborating_indices)
                signal.evidence_quality = validation.evidence_quality
                signal.validation_reasoning = validation.validation_reasoning
                signal.confidence_multiplier = confidence_multiplier

                # Adjust relevance score
                original_score = signal.relevance_score
                signal.relevance_score = min(1.0, original_score * confidence_multiplier)

            # Re-sort after validation adjustments
            signals.sort(key=lambda x: x.relevance_score, reverse=True)

        except Exception as e:
            print(f"⚠ Batch validation failed: {e}")
            print("Continuing without validation")

    # Step 8: Return top N signals with metadata
    return IntelligenceRetrievalResult(
        signals=signals[:max_signals],
        web_searches=web_searches,
    )


def _query_global_items(profile: AssetProfile, days_lookback: int) -> List[GlobalItem]:
    """Query global items with database-level filtering."""
    countries = []
    if profile.country:
        countries.append(profile.country)
    
    # Query with country filter first
    items = load_global_items_filtered(
        countries=countries if countries else None,
        days_lookback=days_lookback,
        limit=200,  # Get more than we need, will filter further
    )
    
    # If no country-specific results, try without country filter to get region-based items
    if not items and profile.region:
        items = load_global_items_filtered(
            countries=None,  # No country filter
            days_lookback=days_lookback,
            limit=200,
        )
    
    return items


def _query_country_snapshots(profile: AssetProfile, days_lookback: int) -> List[CountrySnapshot]:
    """Query country snapshots with database-level filtering."""
    country_name = profile.country
    
    # Prioritize high-activity snapshots
    activity_levels = ["Critical", "High", "Medium"]  # Exclude "Low" for better signal quality
    
    # Try country-specific query first
    snapshots = load_snapshots_filtered(
        country_name=country_name,
        activity_levels=activity_levels,
        days_lookback=days_lookback,
        limit=50,
    )
    
    # If no country-specific results, try without country filter to get region-based snapshots
    # This helps when country name doesn't match exactly
    if not snapshots:
        snapshots = load_snapshots_filtered(
            country_name=None,  # No country filter - get all recent snapshots
            activity_levels=activity_levels,
            days_lookback=days_lookback,
            limit=50,
        )
    
    return snapshots


def _process_global_item(
    item: GlobalItem,
    profile: AssetProfile,
    themes: List[ThemeRelevance],
    theme_keywords: Dict[str, List[str]],
    days_lookback: int,
) -> Optional[IntelligenceSignal]:
    """Process a global item and convert to IntelligenceSignal with scoring."""
    
    # Calculate base relevance (country/region/sector match)
    base_relevance = _calculate_base_relevance_global(item, profile)
    
    # Calculate theme match score
    theme_match_score, matched_theme = _calculate_theme_match(
        item.title + " " + item.summary + " " + item.topic,
        themes,
        theme_keywords,
    )
    
    # Calculate recency score
    recency_score = calculate_recency_score(item.published_at, days_lookback)
    
    # Get source quality
    source_name = item.source.get("name", "") if isinstance(item.source, dict) else str(item.source)
    source_quality = get_source_quality_score(source_name)
    
    # Calculate final weighted score
    final_score = calculate_final_score(
        base_relevance=base_relevance,
        theme_match=theme_match_score,
        recency_score=recency_score,
        source_quality=source_quality,
        activity_level=0.0,  # Global items don't have activity level
    )
    
    # Extract country
    country = _extract_country_from_item(item, profile)
    
    return IntelligenceSignal(
        source="global_item",
        title=item.title,
        summary=item.summary,
        topic=item.topic,
        relevance_score=final_score,
        theme_match=matched_theme,
        published_at=item.published_at,
        url=item.url,
        country=country,
        activity_level=None,
        base_relevance=base_relevance,
        theme_match_score=theme_match_score,
        recency_score=recency_score,
        source_quality=source_quality,
        activity_level_score=0.0,
        semantic_relevance=0.0,
        semantic_confidence=0.0,
        semantic_reasoning="",
        validation_confidence=1.0,
        is_corroborated=False,
        is_contradicted=False,
        corroboration_count=0,
        evidence_quality="",
        validation_reasoning="",
        confidence_multiplier=1.0,
    )


def _process_country_snapshot(
    snapshot: CountrySnapshot,
    profile: AssetProfile,
    themes: List[ThemeRelevance],
    theme_keywords: Dict[str, List[str]],
    days_lookback: int,
) -> List[IntelligenceSignal]:
    """Process a country snapshot and convert to IntelligenceSignal(s)."""
    signals: List[IntelligenceSignal] = []
    
    # Get max events from settings
    settings = get_active_scoring_settings()
    max_events = settings.get("max_events_per_snapshot", 3) if settings else 3
    top_events = _get_top_events(snapshot, profile, themes, theme_keywords, max_events=max_events)
    
    if not top_events and snapshot.events:
        # If no events matched themes, use first event
        top_events = [snapshot.events[0]]
    
    for event in top_events:
        # Calculate base relevance
        base_relevance = _calculate_base_relevance_snapshot(snapshot, profile)
        
        # Calculate theme match
        event_text = f"{event.title} {event.summary} {event.why} {event.topic}"
        theme_match_score, matched_theme = _calculate_theme_match(
            event_text,
            themes,
            theme_keywords,
        )
        
        # Calculate recency (use snapshot updated_at)
        recency_score = calculate_recency_score(snapshot.updated_at, days_lookback)
        
        # Source quality (use event confidence as proxy)
        # Events don't have direct source, use default
        source_quality = 0.8  # Default for aggregated country intelligence
        
        # Activity level score
        activity_level_score = get_activity_level_score(snapshot.activity_level)
        
        # Calculate final score
        final_score = calculate_final_score(
            base_relevance=base_relevance,
            theme_match=theme_match_score,
            recency_score=recency_score,
            source_quality=source_quality,
            activity_level=activity_level_score,
        )
        
        signal = IntelligenceSignal(
            source="country_snapshot",
            title=event.title,
            summary=event.summary,
            topic=event.topic,
            relevance_score=final_score,
            theme_match=matched_theme,
            published_at=snapshot.updated_at,
            url=None,
            country=snapshot.name,
            activity_level=snapshot.activity_level,
            base_relevance=base_relevance,
            theme_match_score=theme_match_score,
            recency_score=recency_score,
            source_quality=source_quality,
            activity_level_score=activity_level_score,
            semantic_relevance=0.0,
            semantic_confidence=0.0,
            semantic_reasoning="",
            validation_confidence=1.0,
            is_corroborated=False,
            is_contradicted=False,
            corroboration_count=0,
            evidence_quality="",
            validation_reasoning="",
            confidence_multiplier=1.0,
        )
        
        signals.append(signal)
    
    return signals


def _calculate_base_relevance_global(item: GlobalItem, profile: AssetProfile) -> float:
    """Calculate base relevance score for a global item (using database settings or defaults)."""
    score = 0.0
    
    # Get scores from settings
    settings = get_active_scoring_settings()
    country_exact = settings.get("score_country_exact_match", 0.5) if settings else 0.5
    country_partial = settings.get("score_country_partial_match", 0.3) if settings else 0.3
    region_match = settings.get("score_region_match", 0.2) if settings else 0.2
    sector_match = settings.get("score_sector_match", 0.2) if settings else 0.2
    
    # Country match (strong signal)
    if profile.country:
        if profile.country in item.countries:
            score += country_exact
        # Partial match (e.g., "United States" in "United States of America")
        elif any(profile.country.lower() in country.lower() for country in item.countries):
            score += country_partial
    
    # Region match
    if profile.region:
        region_keywords = {
            "Emerging Markets": ["emerging", "developing"],
            "Europe": ["europe", "european"],
            "Asia": ["asia", "asian"],
            "Americas": ["america", "american"],
            "Middle East": ["middle east", "mideast"],
        }
        region_lower = profile.region.lower()
        for country in item.countries:
            country_lower = country.lower()
            if region_lower in country_lower or any(
                kw in country_lower for kw in region_keywords.get(profile.region, [])
            ):
                score += region_match
                break
    
    # Sector/topic match
    if profile.sector:
        text = f"{item.topic} {item.title}".lower()
        sector_lower = profile.sector.lower()
        if sector_lower in text or text in sector_lower:
            score += sector_match
    
    return min(1.0, score)


def _calculate_base_relevance_snapshot(
    snapshot: CountrySnapshot,
    profile: AssetProfile,
) -> float:
    """Calculate base relevance score for a country snapshot (using database settings or defaults)."""
    score = 0.0
    
    # Get scores from settings
    settings = get_active_scoring_settings()
    country_exact = settings.get("score_country_exact_match", 0.5) if settings else 0.5
    country_partial = settings.get("score_country_partial_match", 0.3) if settings else 0.3
    region_match = settings.get("score_region_match", 0.2) if settings else 0.2
    
    # Direct country match (very strong) - use higher multiplier for snapshots
    if profile.country:
        if profile.country.lower() == snapshot.name.lower():
            score += country_exact * 1.4  # Boost for exact match in snapshots
        elif profile.country.lower() in snapshot.name.lower():
            score += country_partial * 1.4  # Boost for partial match in snapshots
    
    # Region match
    if profile.region:
        region_keywords = {
            "Emerging Markets": ["emerging", "developing"],
            "Europe": ["europe", "european"],
            "Asia": ["asia", "asian"],
            "Americas": ["america", "american"],
            "Middle East": ["middle east", "mideast"],
        }
        snapshot_lower = snapshot.name.lower()
        if any(kw in snapshot_lower for kw in region_keywords.get(profile.region, [])):
            score += region_match
    
    return min(1.0, score)


def _calculate_theme_match(
    text: str,
    themes: List[ThemeRelevance],
    theme_keywords: Dict[str, List[str]],
) -> tuple[float, Optional[str]]:
    """
    Calculate theme match score and return best matching theme.
    
    Returns:
        (score, theme_name) tuple
    """
    text_lower = text.lower()
    best_score = 0.0
    best_theme = None
    
    for theme in themes:
        if theme.relevance_score < 0.2:  # Skip low-relevance themes
            continue
        
        keywords = theme_keywords.get(theme.theme, [])
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        
        if matches > 0:
            # Score based on number of keyword matches and theme relevance
            match_score = min(1.0, (matches / len(keywords)) * theme.relevance_score)
            if match_score > best_score:
                best_score = match_score
                best_theme = theme.theme
    
    return best_score, best_theme


def _get_top_events(
    snapshot: CountrySnapshot,
    profile: AssetProfile,
    themes: List[ThemeRelevance],
    theme_keywords: Dict[str, List[str]],
    max_events: int = 3,
) -> List:
    """Get top N most relevant events from a snapshot."""
    if not snapshot.events:
        return []
    
    event_scores = []
    for event in snapshot.events:
        event_text = f"{event.title} {event.summary} {event.why} {event.topic}"
        score, _ = _calculate_theme_match(event_text, themes, theme_keywords)
        event_scores.append((score, event))
    
    # Sort by score (highest first)
    event_scores.sort(key=lambda x: x[0], reverse=True)
    
    # Return top N events
    return [event for _, event in event_scores[:max_events]]


def _build_theme_keywords(themes: List[ThemeRelevance]) -> Dict[str, List[str]]:
    """Build keyword dictionary for themes."""
    keywords: Dict[str, List[str]] = {}
    all_themes = get_geopolitical_themes()
    for theme in themes:
        if theme.theme in all_themes:
            keywords[theme.theme] = all_themes[theme.theme].get("keywords", [])
    return keywords


def _extract_country_from_item(item: GlobalItem, profile: AssetProfile) -> Optional[str]:
    """Extract the most relevant country from item."""
    if profile.country and profile.country in item.countries:
        return profile.country
    if item.countries:
        return item.countries[0]
    return None
