"""Main pipeline orchestrator - runs the complete GP risk analysis pipeline."""
from dataclasses import dataclass
from typing import Literal, List, Dict, Any, Generator
import time
from .schemas.geo_risk import Holding
from .geo_risk_characterization import characterize_asset, AssetProfile, get_characterization_summary
from .geo_risk_theme_mapper import identify_relevant_themes, get_top_themes, ThemeRelevance
from .geo_risk_intelligence import retrieve_intelligence, IntelligenceSignal, IntelligenceRetrievalResult
from .geo_risk_intelligence_cache import retrieve_intelligence_cached
from .geo_risk_impact import assess_impact, AggregateImpact
from .geo_risk_probability import calculate_probabilities, ActionProbabilities, get_probability_summary
from .scoring_settings_service import get_active_scoring_settings


@dataclass
class PipelineResult:
    """Complete pipeline result with all intermediate steps."""
    # Step 1: Characterization
    profile: AssetProfile
    characterization_summary: str
    
    # Step 2: Theme identification
    themes: List[ThemeRelevance]
    top_themes: List[str]
    
    # Step 3: Intelligence retrieval
    signals: List[IntelligenceSignal]
    signal_count: int
    web_searches: List[Dict[str, Any]]  # Web search metadata
    
    # Step 4: Impact assessment
    impact: AggregateImpact
    
    # Step 5: Probability calculation
    probabilities: ActionProbabilities
    probability_summary: str
    
    # Metadata
    risk_tolerance: str
    days_lookback: int


def run_pipeline(
    holding: Holding,
    risk_tolerance: Literal["Low", "Medium", "High"] = "Medium",
    days_lookback: int | None = None,
) -> PipelineResult:
    """
    Run the complete geopolitical risk analysis pipeline.
    
    Pipeline steps:
    1. Asset Characterization - Extract asset characteristics
    2. Theme Identification - Map to relevant geopolitical themes
    3. Intelligence Retrieval - Query data sources for relevant signals
    4. Impact Assessment - Analyze signal direction and magnitude
    5. Probability Calculation - Convert to Sell/Hold/Buy probabilities
    
    Args:
        holding: Investment holding to analyze
        risk_tolerance: Client risk tolerance (Low/Medium/High)
        days_lookback: How many days back to search for signals (uses settings default if None)
    
    Returns:
        PipelineResult with all intermediate results and final probabilities
    """
    # Get default days_lookback from settings if not provided
    if days_lookback is None:
        settings = get_active_scoring_settings()
        days_lookback = settings.get("days_lookback_default", 90) if settings else 90
    
    # Step 1: Asset Characterization
    profile = characterize_asset(holding)
    characterization_summary = get_characterization_summary(profile)
    
    # Step 2: Theme Identification
    themes = identify_relevant_themes(profile)
    top_themes = get_top_themes(profile, max_themes=5)
    
    # Step 3: Intelligence Retrieval (with caching)
    intel_result = retrieve_intelligence_cached(profile, themes, days_lookback=days_lookback)
    signals = intel_result.signals
    web_searches = intel_result.web_searches
    
    # Step 4: Impact Assessment
    impact = assess_impact(profile, themes, signals)
    
    # Step 5: Probability Calculation
    probabilities = calculate_probabilities(profile, impact, risk_tolerance)
    probability_summary = get_probability_summary(probabilities)
    
    return PipelineResult(
        profile=profile,
        characterization_summary=characterization_summary,
        themes=themes,
        top_themes=top_themes,
        signals=signals,
        signal_count=len(signals),
        web_searches=web_searches,
        impact=impact,
        probabilities=probabilities,
        probability_summary=probability_summary,
        risk_tolerance=risk_tolerance,
        days_lookback=days_lookback,
    )


def run_pipeline_simple(
    holding: Holding,
    risk_tolerance: Literal["Low", "Medium", "High"] = "Medium",
) -> ActionProbabilities:
    """
    Simplified pipeline that returns only the final probabilities.

    Use this when you only need the Sell/Hold/Buy scores.
    """
    result = run_pipeline(holding, risk_tolerance)
    return result.probabilities


@dataclass
class PipelineStepUpdate:
    """Progress update for a single pipeline step."""
    step_id: str
    step_name: str
    status: Literal["pending", "running", "completed", "error"]
    duration_ms: int
    data: Any = None  # Step-specific data
    error: str | None = None


def run_pipeline_streaming(
    holding: Holding,
    risk_tolerance: Literal["Low", "Medium", "High"] = "Medium",
    days_lookback: int | None = None,
) -> Generator[PipelineStepUpdate, None, None]:
    """
    Run the pipeline with real-time progress streaming.

    Yields a PipelineStepUpdate after each step completes, allowing
    the frontend to show live progress updates.

    Args:
        holding: Investment holding to analyze
        risk_tolerance: Client risk tolerance (Low/Medium/High)
        days_lookback: How many days back to search for signals

    Yields:
        PipelineStepUpdate for each step (characterization, themes, intelligence, impact, probability)
    """
    # Get default days_lookback from settings if not provided
    if days_lookback is None:
        settings = get_active_scoring_settings()
        days_lookback = settings.get("days_lookback_default", 90) if settings else 90

    try:
        # Step 1: Asset Characterization
        step_start = time.time()
        profile = characterize_asset(holding)
        characterization_summary = get_characterization_summary(profile)
        step_duration = int((time.time() - step_start) * 1000)

        # Build exposures list
        exposures = []
        if profile.is_government_exposed:
            exposures.append("Government")
        if profile.is_energy_exposed:
            exposures.append("Energy")
        if profile.is_financial_exposed:
            exposures.append("Financial")
        if profile.is_technology_exposed:
            exposures.append("Technology")
        if profile.is_infrastructure_exposed:
            exposures.append("Infrastructure")

        yield PipelineStepUpdate(
            step_id="characterization",
            step_name="Asset Characterization",
            status="completed",
            duration_ms=step_duration,
            data={
                "asset_name": profile.name,
                "name": holding.name,  # Include for asset saving
                "ticker": holding.ticker,  # Include for asset saving
                "isin": holding.isin,  # Include for asset saving
                "asset_country": profile.country,
                "asset_region": profile.region,
                "asset_class": profile.asset_class,
                "asset_sector": profile.sector,
                "is_emerging_market": profile.is_emerging_market,
                "is_developed_market": profile.is_developed_market,
                "is_global_fund": profile.is_global_fund,
                "exposures": exposures,
                "characterization_summary": characterization_summary,
            }
        )

        # Step 2: Theme Identification
        step_start = time.time()
        themes = identify_relevant_themes(profile)
        top_themes = get_top_themes(profile, max_themes=5)
        step_duration = int((time.time() - step_start) * 1000)

        yield PipelineStepUpdate(
            step_id="theme_identification",
            step_name="Theme Identification",
            status="completed",
            duration_ms=step_duration,
            data={
                "themes": [
                    {
                        "theme": t.theme,
                        "relevance_score": t.relevance_score,
                        "reasoning": t.reasoning,
                        "keywords_matched": t.keywords_matched,
                    }
                    for t in themes
                ],
                "top_themes": top_themes,
            }
        )

        # Step 3: Intelligence Retrieval
        step_start = time.time()
        intel_result = retrieve_intelligence_cached(profile, themes, days_lookback=days_lookback)
        signals = intel_result.signals
        web_searches = intel_result.web_searches
        step_duration = int((time.time() - step_start) * 1000)

        yield PipelineStepUpdate(
            step_id="intelligence_retrieval",
            step_name="Intelligence Retrieval",
            status="completed",
            duration_ms=step_duration,
            data={
                "signals": [
                    {
                        "source": s.source,
                        "title": s.title,
                        "summary": s.summary,
                        "topic": s.topic,
                        "relevance_score": s.relevance_score,
                        "theme_match": s.theme_match,
                        "published_at": s.published_at,
                        "url": s.url,
                        "country": s.country,
                        "activity_level": s.activity_level,
                        "base_relevance": s.base_relevance,
                        "theme_match_score": s.theme_match_score,
                        "recency_score": s.recency_score,
                        "source_quality": s.source_quality,
                        "activity_level_score": s.activity_level_score,
                    }
                    for s in signals
                ],
                "signal_count": len(signals),
                "web_searches": web_searches,
            }
        )

        # Step 4: Impact Assessment (includes probability calculation)
        step_start = time.time()
        impact = assess_impact(profile, themes, signals)
        probabilities = calculate_probabilities(profile, impact, risk_tolerance)
        probability_summary = get_probability_summary(probabilities)
        step_duration = int((time.time() - step_start) * 1000)

        yield PipelineStepUpdate(
            step_id="impact_assessment",
            step_name="Impact Assessment",
            status="completed",
            duration_ms=step_duration,
            data={
                "impact": {
                    "overall_direction": impact.overall_direction,
                    "overall_magnitude": impact.overall_magnitude,
                    "confidence": impact.confidence,
                    "total_signals": impact.total_signals,
                    "theme_impacts": [
                        {
                            "theme": ti.theme,
                            "impact_direction": ti.impact_direction,
                            "impact_magnitude": ti.impact_magnitude,
                            "confidence": ti.confidence,
                            "reasoning": ti.reasoning,
                            "signal_count": ti.signal_count,
                            "summary": ti.summary,
                        }
                        for ti in impact.theme_impacts
                    ],
                },
                "probabilities": {
                    "negative": probabilities.sell,  # Map sell to negative
                    "neutral": probabilities.hold,   # Map hold to neutral
                    "positive": probabilities.buy,    # Map buy to positive
                },
                "probability_summary": probability_summary,
                "risk_tolerance": risk_tolerance,
                "days_lookback": days_lookback,
            }
        )

    except Exception as e:
        # Send error update
        yield PipelineStepUpdate(
            step_id="error",
            step_name="Pipeline Error",
            status="error",
            duration_ms=0,
            error=str(e)
        )
