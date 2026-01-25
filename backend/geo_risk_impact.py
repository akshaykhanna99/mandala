"""Impact assessment - analyzes intelligence signals to determine asset impact."""
from dataclasses import dataclass
from typing import List, Dict, Optional
import os
from .geo_risk_intelligence import IntelligenceSignal
from .geo_risk_characterization import AssetProfile
from .geo_risk_theme_mapper import ThemeRelevance


@dataclass
class ThemeImpact:
    """Impact assessment for a single theme."""
    theme: str
    impact_direction: str  # "positive", "negative", "neutral"
    impact_magnitude: float  # 0.0 to 1.0 (how strong the impact)
    confidence: float  # 0.0 to 1.0 (how confident we are in this assessment)
    reasoning: str
    signal_count: int  # Number of signals supporting this assessment
    summary: str = ""  # Claude-generated verbal summary of decision making


@dataclass
class AggregateImpact:
    """Aggregated impact across all themes."""
    overall_direction: str  # "positive", "negative", "neutral"
    overall_magnitude: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    theme_impacts: List[ThemeImpact]
    total_signals: int


def _generate_theme_summary(
    theme: ThemeRelevance,
    signals: List[IntelligenceSignal],
    profile: AssetProfile,
    impact_direction: str,
    impact_magnitude: float,
    confidence: float,
) -> str:
    """
    Generate a Claude-powered verbal summary of the theme impact decision.

    Args:
        theme: The theme being assessed
        signals: Intelligence signals for this theme
        profile: Asset profile
        impact_direction: Assessed direction (positive/negative/neutral)
        impact_magnitude: Impact magnitude (0.0-1.0)
        confidence: Confidence score (0.0-1.0)

    Returns:
        Verbal summary explaining the decision making
    """
    # Check if Claude API is available
    api_key = os.getenv("CLAUDE_API")
    if not api_key:
        # Fallback to simple summary if no Claude API
        return f"Based on {len(signals)} signals, this theme shows {impact_direction} impact with {int(confidence * 100)}% confidence."

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        # Build signal context (limit to top 5 most relevant signals)
        signal_summaries = []
        for i, sig in enumerate(sorted(signals, key=lambda s: s.relevance_score, reverse=True)[:5]):
            signal_summaries.append(f"- {sig.title} ({sig.source})")

        signals_text = "\n".join(signal_summaries)

        # Build prompt for suitability reporting
        prompt = f"""You are a financial analyst preparing geopolitical risk analysis for investment suitability reporting. Provide a clear, professional summary explaining why this theme has a {impact_direction} impact.

ASSET CONTEXT:
- Name: {profile.name}
- Country: {profile.country or 'N/A'}
- Sector: {profile.sector}
- Region: {profile.region}

THEME: {theme.theme.replace('_', ' ').title()}
Theme Relevance: {theme.relevance_score:.2f}

TOP INTELLIGENCE SIGNALS ({len(signals)} total):
{signals_text}

ASSESSMENT:
- Direction: {impact_direction.upper()}
- Magnitude: {int(impact_magnitude * 100)}%
- Confidence: {int(confidence * 100)}%

Write a 2-3 sentence summary for suitability documentation:
1. What the intelligence signals indicate about this geopolitical theme
2. Why this creates a {impact_direction} impact on the asset
3. The investment implications based on this analysis

Requirements:
- Use professional, compliance-appropriate language
- Reference specific signals when relevant
- Be objective and evidence-based
- Suitable for client-facing investment documentation"""

        # Try Claude Sonnet 4.5 first (best for suitability reporting)
        models_to_try = [
            "claude-sonnet-4-5-20250929",  # Claude Sonnet 4.5 (latest, best quality)
            "claude-3-haiku-20240307",     # Fallback to Haiku
        ]

        last_error = None
        for model in models_to_try:
            try:
                message = client.messages.create(
                    model=model,
                    max_tokens=250,
                    temperature=0.3,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                summary = message.content[0].text.strip()
                return summary
            except Exception as model_error:
                last_error = model_error
                # If it's a 404 (model not found), try next model
                if "404" in str(model_error) or "not_found" in str(model_error):
                    print(f"Model {model} not available, trying fallback...")
                    continue
                else:
                    # For other errors, raise immediately
                    raise

        # If all models failed, raise the last error
        if last_error:
            raise last_error

    except Exception as e:
        print(f"Failed to generate Claude summary (all models): {e}")
        # Fallback to simple summary
        return f"Based on {len(signals)} intelligence signals, this theme shows {impact_direction} impact with {int(confidence * 100)}% confidence for {profile.name}."


def assess_impact(
    profile: AssetProfile,
    themes: List[ThemeRelevance],
    signals: List[IntelligenceSignal],
) -> AggregateImpact:
    """
    Assess the geopolitical impact on an asset based on themes and intelligence signals.
    
    Args:
        profile: Asset profile
        themes: Relevant themes with relevance scores
        signals: Intelligence signals retrieved
    
    Returns:
        AggregateImpact with overall assessment and per-theme breakdowns
    """
    theme_impacts: List[ThemeImpact] = []
    
    # Group signals by theme
    signals_by_theme: Dict[str, List[IntelligenceSignal]] = {}
    for signal in signals:
        if signal.theme_match:
            signals_by_theme.setdefault(signal.theme_match, []).append(signal)
    
    # Assess impact for each theme
    for theme in themes:
        theme_signals = signals_by_theme.get(theme.theme, [])
        
        if not theme_signals:
            # No signals for this theme - neutral impact with low confidence
            theme_impacts.append(
                ThemeImpact(
                    theme=theme.theme,
                    impact_direction="neutral",
                    impact_magnitude=0.0,
                    confidence=0.1,
                    reasoning="No recent signals found for this theme",
                    signal_count=0,
                )
            )
            continue
        
        # Analyze signals to determine impact
        impact = _assess_theme_impact(theme, theme_signals, profile)
        theme_impacts.append(impact)
    
    # Aggregate impacts
    return _aggregate_impacts(theme_impacts, len(signals))


def _assess_theme_impact(
    theme: ThemeRelevance,
    signals: List[IntelligenceSignal],
    profile: AssetProfile,
) -> ThemeImpact:
    """Assess impact for a single theme based on its signals."""
    
    # Determine impact direction based on theme type and signal content
    positive_keywords = [
        "growth", "improve", "stability", "recovery", "positive", "strength",
        "agreement", "cooperation", "progress", "expansion", "boost", "gain",
    ]
    negative_keywords = [
        "crisis", "conflict", "sanction", "instability", "decline", "risk",
        "tension", "dispute", "threat", "volatility", "uncertainty", "loss",
        "embargo", "restriction", "protest", "unrest", "war", "attack",
    ]
    
    # Count positive vs negative signals
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for signal in signals:
        text = f"{signal.title} {signal.summary}".lower()
        has_positive = any(kw in text for kw in positive_keywords)
        has_negative = any(kw in text for kw in negative_keywords)
        
        if has_negative and not has_positive:
            negative_count += 1
        elif has_positive and not has_negative:
            positive_count += 1
        else:
            neutral_count += 1
    
    # Determine direction
    total = len(signals)
    if negative_count > positive_count and negative_count > total * 0.4:
        direction = "negative"
        magnitude = min(1.0, (negative_count / total) * theme.relevance_score)
    elif positive_count > negative_count and positive_count > total * 0.4:
        direction = "positive"
        magnitude = min(1.0, (positive_count / total) * theme.relevance_score)
    else:
        direction = "neutral"
        magnitude = 0.3 * theme.relevance_score
    
    # Adjust for theme-specific logic
    if theme.theme == "sanctions":
        # Sanctions are almost always negative
        if negative_count > 0:
            direction = "negative"
            magnitude = min(1.0, magnitude + 0.2)
    elif theme.theme == "political_instability":
        # Instability is negative
        if negative_count > 0:
            direction = "negative"
            magnitude = min(1.0, magnitude + 0.15)
    elif theme.theme == "currency_volatility":
        # Volatility can be negative or neutral
        if negative_count > positive_count:
            direction = "negative"
            magnitude = min(1.0, magnitude + 0.1)
    elif theme.theme == "trade_disruption":
        # Trade disruption is negative
        if negative_count > 0:
            direction = "negative"
            magnitude = min(1.0, magnitude + 0.15)
    elif theme.theme == "energy_security":
        # Energy security issues are negative
        if negative_count > 0:
            direction = "negative"
            magnitude = min(1.0, magnitude + 0.1)
    
    # Confidence based on signal count and relevance
    confidence = min(1.0, (len(signals) / 10.0) * 0.5 + theme.relevance_score * 0.5)
    
    # Build reasoning
    reasoning_parts = []
    if direction == "negative":
        reasoning_parts.append(f"{negative_count} negative signals")
    elif direction == "positive":
        reasoning_parts.append(f"{positive_count} positive signals")
    else:
        reasoning_parts.append("Mixed or neutral signals")

    reasoning_parts.append(f"Theme relevance: {theme.relevance_score:.2f}")
    if profile.country:
        reasoning_parts.append(f"Country: {profile.country}")

    # Generate Claude-powered summary
    summary = _generate_theme_summary(
        theme=theme,
        signals=signals,
        profile=profile,
        impact_direction=direction,
        impact_magnitude=magnitude,
        confidence=confidence,
    )

    return ThemeImpact(
        theme=theme.theme,
        impact_direction=direction,
        impact_magnitude=magnitude,
        confidence=confidence,
        reasoning="; ".join(reasoning_parts),
        signal_count=len(signals),
        summary=summary,
    )


def _aggregate_impacts(
    theme_impacts: List[ThemeImpact],
    total_signals: int,
) -> AggregateImpact:
    """Aggregate individual theme impacts into overall assessment."""
    
    # Weighted average of impacts
    weighted_negative = 0.0
    weighted_positive = 0.0
    total_weight = 0.0
    total_confidence = 0.0
    
    for impact in theme_impacts:
        weight = impact.impact_magnitude * impact.confidence
        total_weight += weight
        total_confidence += impact.confidence
        
        if impact.impact_direction == "negative":
            weighted_negative += weight
        elif impact.impact_direction == "positive":
            weighted_positive += weight
    
    # Determine overall direction
    if weighted_negative > weighted_positive and weighted_negative > total_weight * 0.4:
        overall_direction = "negative"
        overall_magnitude = min(1.0, weighted_negative / total_weight if total_weight > 0 else 0.0)
    elif weighted_positive > weighted_negative and weighted_positive > total_weight * 0.4:
        overall_direction = "positive"
        overall_magnitude = min(1.0, weighted_positive / total_weight if total_weight > 0 else 0.0)
    else:
        overall_direction = "neutral"
        overall_magnitude = 0.3
    
    # Overall confidence
    avg_confidence = total_confidence / len(theme_impacts) if theme_impacts else 0.0
    signal_confidence = min(1.0, total_signals / 20.0)  # More signals = higher confidence
    overall_confidence = (avg_confidence * 0.7 + signal_confidence * 0.3)
    
    return AggregateImpact(
        overall_direction=overall_direction,
        overall_magnitude=overall_magnitude,
        confidence=overall_confidence,
        theme_impacts=theme_impacts,
        total_signals=total_signals,
    )
