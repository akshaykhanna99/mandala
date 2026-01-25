"""
Claude-powered semantic intelligence analysis service.

This module provides semantic filtering and analysis of intelligence signals
using Claude API, significantly improving signal quality by replacing keyword
matching with natural language understanding.
"""

import os
import hashlib
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class SemanticAnalysisResult:
    """Result of Claude semantic analysis."""
    relevance_score: float  # 0.0-1.0
    confidence_score: float  # 0.0-1.0
    matched_themes: List[str]  # Themes that semantically match
    reasoning: str  # Claude's explanation
    is_relevant: bool  # True if relevance_score >= threshold


# In-memory cache for Claude responses
_claude_cache: Dict[str, Tuple[SemanticAnalysisResult, datetime]] = {}
_cache_ttl_minutes = 60


class ClaudeIntelligenceService:
    """Service for Claude-powered semantic intelligence analysis."""

    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """
        Initialize Claude service.

        Args:
            api_key: Claude API key (defaults to CLAUDE_API env var)
            use_cache: Whether to use response caching (default: True)
        """
        self.api_key = api_key or os.getenv("CLAUDE_API")
        if not self.api_key:
            raise ValueError("CLAUDE_API key not found in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.use_cache = use_cache

    def analyze_signal_relevance(
        self,
        signal_title: str,
        signal_summary: str,
        asset_country: Optional[str],
        asset_sector: Optional[str],
        themes: List[str],
        relevance_threshold: float = 0.6,
        use_haiku: bool = True
    ) -> SemanticAnalysisResult:
        """
        Analyze if a signal is semantically relevant to the asset profile.

        This replaces keyword matching with semantic understanding, filtering out
        noise and weak signals before they enter the scoring pipeline.

        Args:
            signal_title: Signal title
            signal_summary: Signal summary/description
            asset_country: Country of the asset
            asset_sector: Sector of the asset
            themes: List of relevant geopolitical themes
            relevance_threshold: Minimum relevance score to pass (0.0-1.0)
            use_haiku: Use Claude Haiku for speed/cost (default: True)

        Returns:
            SemanticAnalysisResult with relevance score, confidence, and reasoning
        """
        # Check cache first
        if self.use_cache:
            cache_key = self._generate_cache_key(
                signal_title, signal_summary, asset_country, asset_sector, themes
            )
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

        # Build context string
        context_parts = []
        if asset_country:
            context_parts.append(f"Country: {asset_country}")
        if asset_sector:
            context_parts.append(f"Sector: {asset_sector}")
        if themes:
            context_parts.append(f"Relevant themes: {', '.join(themes)}")

        context = "\n".join(context_parts) if context_parts else "General global intelligence"

        # Build prompt
        prompt = f"""You are an expert geopolitical risk analyst. Analyze if this intelligence signal is truly relevant to the given asset.

ASSET CONTEXT:
{context}

INTELLIGENCE SIGNAL:
Title: {signal_title}
Summary: {signal_summary}

TASK:
1. Determine if this signal is TRULY relevant to the asset's risk profile
2. Rate relevance from 0.0 (completely irrelevant) to 1.0 (highly relevant)
3. Rate your confidence from 0.0 (very uncertain) to 1.0 (very confident)
4. Identify which themes (if any) this signal matches semantically
5. Explain your reasoning concisely (1-2 sentences)

RELEVANCE GUIDELINES:
- 0.8-1.0: Direct, specific impact on the asset (e.g., sanctions on Russia for Russian assets)
- 0.6-0.8: Likely indirect impact (e.g., regional conflict affecting neighboring country)
- 0.4-0.6: Tangential relevance (e.g., global trend affecting sector broadly)
- 0.2-0.4: Weak connection (e.g., mentioned country but unrelated topic)
- 0.0-0.2: Irrelevant or generic news

RESPOND IN JSON FORMAT ONLY:
{{
    "relevance_score": 0.0-1.0,
    "confidence_score": 0.0-1.0,
    "matched_themes": ["theme1", "theme2"],
    "reasoning": "Your explanation here"
}}"""

        # Call Claude API
        model = "claude-3-haiku-20240307" if use_haiku else "claude-3-5-sonnet-20241022"

        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=300,
                temperature=0.1,  # Low temperature for consistent scoring
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            response_text = message.content[0].text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            response_data = json.loads(response_text)

            # Create result
            result = SemanticAnalysisResult(
                relevance_score=float(response_data.get("relevance_score", 0.0)),
                confidence_score=float(response_data.get("confidence_score", 0.0)),
                matched_themes=response_data.get("matched_themes", []),
                reasoning=response_data.get("reasoning", ""),
                is_relevant=float(response_data.get("relevance_score", 0.0)) >= relevance_threshold
            )

            # Cache result
            if self.use_cache:
                self._add_to_cache(cache_key, result)

            return result

        except Exception as e:
            # Fallback: return neutral score on error
            print(f"Claude API error: {e}")
            return SemanticAnalysisResult(
                relevance_score=0.5,  # Neutral score
                confidence_score=0.0,  # No confidence
                matched_themes=[],
                reasoning=f"API error: {str(e)}",
                is_relevant=False  # Don't pass through on error
            )

    def analyze_batch_signals(
        self,
        signals: List[Dict],
        asset_country: Optional[str],
        asset_sector: Optional[str],
        themes: List[str],
        relevance_threshold: float = 0.6,
    ) -> List[Tuple[int, SemanticAnalysisResult]]:
        """
        Analyze multiple signals in sequence.

        Note: This processes signals one-by-one. For production, consider
        implementing true batch processing with concurrent API calls.

        Args:
            signals: List of signal dicts with 'title' and 'summary'
            asset_country: Country of the asset
            asset_sector: Sector of the asset
            themes: List of relevant geopolitical themes
            relevance_threshold: Minimum relevance score to pass

        Returns:
            List of (index, SemanticAnalysisResult) tuples for relevant signals only
        """
        relevant_signals = []

        for idx, signal in enumerate(signals):
            result = self.analyze_signal_relevance(
                signal_title=signal.get("title", ""),
                signal_summary=signal.get("summary", ""),
                asset_country=asset_country,
                asset_sector=asset_sector,
                themes=themes,
                relevance_threshold=relevance_threshold,
            )

            # Only include if relevant
            if result.is_relevant:
                relevant_signals.append((idx, result))

        return relevant_signals

    def _generate_cache_key(
        self,
        title: str,
        summary: str,
        country: Optional[str],
        sector: Optional[str],
        themes: List[str]
    ) -> str:
        """Generate MD5 hash for cache key."""
        content = f"{title}|{summary}|{country}|{sector}|{'|'.join(sorted(themes))}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[SemanticAnalysisResult]:
        """Retrieve from cache if not expired."""
        if cache_key in _claude_cache:
            result, cached_at = _claude_cache[cache_key]
            if datetime.now() - cached_at < timedelta(minutes=_cache_ttl_minutes):
                return result
            else:
                # Expired, remove
                del _claude_cache[cache_key]
        return None

    def _add_to_cache(self, cache_key: str, result: SemanticAnalysisResult):
        """Add result to cache."""
        _claude_cache[cache_key] = (result, datetime.now())

    @staticmethod
    def clear_cache():
        """Clear the entire cache."""
        _claude_cache.clear()

    @staticmethod
    def get_cache_stats() -> Dict:
        """Get cache statistics."""
        now = datetime.now()
        valid_entries = sum(
            1 for _, (_, cached_at) in _claude_cache.items()
            if now - cached_at < timedelta(minutes=_cache_ttl_minutes)
        )
        return {
            "total_entries": len(_claude_cache),
            "valid_entries": valid_entries,
            "ttl_minutes": _cache_ttl_minutes
        }


def analyze_signal_relevance_simple(
    signal_title: str,
    signal_summary: str,
    asset_country: Optional[str] = None,
    asset_sector: Optional[str] = None,
    themes: List[str] = None,
    relevance_threshold: float = 0.6
) -> SemanticAnalysisResult:
    """
    Simple function wrapper for one-off signal analysis.

    Creates a new service instance and analyzes a single signal.
    For batch processing, create a service instance and reuse it.
    """
    service = ClaudeIntelligenceService()
    return service.analyze_signal_relevance(
        signal_title=signal_title,
        signal_summary=signal_summary,
        asset_country=asset_country,
        asset_sector=asset_sector,
        themes=themes or [],
        relevance_threshold=relevance_threshold
    )


# Example usage
if __name__ == "__main__":
    # Test the service
    service = ClaudeIntelligenceService()

    result = service.analyze_signal_relevance(
        signal_title="Russia announces new oil export restrictions",
        signal_summary="Russia's government announced new restrictions on oil exports to European countries, citing geopolitical tensions.",
        asset_country="Russia",
        asset_sector="Energy",
        themes=["sanctions", "energy_security", "trade_disruption"],
        relevance_threshold=0.6
    )

    print("Semantic Analysis Result:")
    print(f"  Relevance: {result.relevance_score:.2f}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    print(f"  Matched Themes: {', '.join(result.matched_themes)}")
    print(f"  Is Relevant: {result.is_relevant}")
    print(f"  Reasoning: {result.reasoning}")
