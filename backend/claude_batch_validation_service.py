"""
Claude-powered batch validation service for intelligence signals.

This module implements Phase 2 enhancements:
- Cross-reference signals to detect contradictions
- Identify corroborating signals (multi-source validation)
- Enhanced confidence scoring based on evidence quality
- Boost high-confidence signals, downgrade contradicted ones
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
class SignalValidation:
    """Validation result for a signal."""
    signal_index: int  # Index in original signal list
    validation_confidence: float  # 0.0-1.0 (how confident in this signal)
    is_corroborated: bool  # True if confirmed by multiple sources
    is_contradicted: bool  # True if contradicted by other signals
    corroborating_indices: List[int]  # Indices of signals that support this one
    contradicting_indices: List[int]  # Indices of signals that contradict this one
    evidence_quality: str  # "high", "medium", "low"
    validation_reasoning: str  # Claude's explanation


@dataclass
class BatchValidationResult:
    """Result of batch validation."""
    validations: List[SignalValidation]  # One per signal
    overall_coherence: float  # 0.0-1.0 (how well signals agree)
    contradiction_count: int  # Number of contradictions found
    corroboration_count: int  # Number of corroborations found
    analysis_summary: str  # Claude's overall assessment


# In-memory cache for batch validation
_batch_cache: Dict[str, Tuple[BatchValidationResult, datetime]] = {}
_cache_ttl_minutes = 60


class ClaudeBatchValidationService:
    """Service for Claude-powered batch signal validation."""

    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """
        Initialize batch validation service.

        Args:
            api_key: Claude API key (defaults to CLAUDE_API env var)
            use_cache: Whether to use response caching (default: True)
        """
        self.api_key = api_key or os.getenv("CLAUDE_API")
        if not self.api_key:
            raise ValueError("CLAUDE_API key not found in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.use_cache = use_cache

    def validate_signal_batch(
        self,
        signals: List[Dict],
        asset_country: Optional[str] = None,
        asset_sector: Optional[str] = None,
        use_sonnet: bool = True,  # Use Sonnet for better reasoning
    ) -> BatchValidationResult:
        """
        Validate a batch of signals for contradictions and corroborations.

        This is the core Phase 2 enhancement: cross-referencing signals to
        improve quality through validation.

        Args:
            signals: List of signal dicts with 'title', 'summary', 'source'
            asset_country: Country context for validation
            asset_sector: Sector context for validation
            use_sonnet: Use Claude Sonnet for better reasoning (default: True)

        Returns:
            BatchValidationResult with validation for each signal
        """
        # Check cache first
        if self.use_cache:
            cache_key = self._generate_cache_key(signals, asset_country, asset_sector)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

        # Limit to top 50 signals for API token limits
        signals_subset = signals[:50]

        # Build signal summary for Claude
        signal_summaries = []
        for idx, sig in enumerate(signals_subset):
            signal_summaries.append(
                f"[{idx}] Source: {sig.get('source', 'unknown')}\n"
                f"    Title: {sig.get('title', '')}\n"
                f"    Summary: {sig.get('summary', '')[:200]}..."
            )

        signals_text = "\n\n".join(signal_summaries)

        # Build context
        context_parts = []
        if asset_country:
            context_parts.append(f"Country: {asset_country}")
        if asset_sector:
            context_parts.append(f"Sector: {asset_sector}")
        context = "\n".join(context_parts) if context_parts else "General global intelligence"

        # Build prompt
        prompt = f"""You are an expert intelligence analyst validating geopolitical risk signals.

ASSET CONTEXT:
{context}

INTELLIGENCE SIGNALS ({len(signals_subset)} signals):
{signals_text}

TASK:
Analyze these intelligence signals for:
1. **Contradictions**: Which signals contradict each other? (e.g., one says "sanctions lifted", another says "sanctions tightened")
2. **Corroborations**: Which signals support/confirm each other? (e.g., multiple sources reporting same event)
3. **Evidence Quality**: Rate each signal's evidence quality (high/medium/low) based on specificity and credibility
4. **Confidence Assessment**: How confident are you in each signal's accuracy?

GUIDELINES:
- Corroboration: Multiple independent sources reporting similar information = HIGH confidence boost
- Contradiction: Conflicting information = LOW confidence, flag for review
- Evidence quality:
  - HIGH: Specific details (dates, names, numbers), credible sources, verifiable claims
  - MEDIUM: General information, single source, vague details
  - LOW: Speculative, unverified, or highly general claims
- Overall coherence: How well do signals tell a coherent story?

RESPOND IN JSON FORMAT ONLY:
{{
    "validations": [
        {{
            "signal_index": 0,
            "validation_confidence": 0.0-1.0,
            "is_corroborated": true/false,
            "is_contradicted": true/false,
            "corroborating_indices": [1, 3],
            "contradicting_indices": [],
            "evidence_quality": "high/medium/low",
            "validation_reasoning": "Explanation here"
        }},
        ...
    ],
    "overall_coherence": 0.0-1.0,
    "contradiction_count": 0,
    "corroboration_count": 0,
    "analysis_summary": "Overall assessment of signal quality and coherence"
}}

IMPORTANT:
- Provide validation for ALL {len(signals_subset)} signals
- Be strict: only mark as corroborated if truly confirmed by another source
- Flag contradictions clearly to prevent conflicting intelligence"""

        # Call Claude API
        # Note: Using Opus 4 or latest Sonnet. Fallback to Haiku if use_sonnet=False
        model = "claude-opus-4-20250514" if use_sonnet else "claude-3-haiku-20240307"

        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=4000,  # Larger for batch analysis
                temperature=0.1,  # Low temperature for consistency
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            response_text = message.content[0].text.strip()

            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            response_data = json.loads(response_text)

            # Parse validations
            validations = []
            for v in response_data.get("validations", []):
                validations.append(SignalValidation(
                    signal_index=int(v.get("signal_index", 0)),
                    validation_confidence=float(v.get("validation_confidence", 0.5)),
                    is_corroborated=bool(v.get("is_corroborated", False)),
                    is_contradicted=bool(v.get("is_contradicted", False)),
                    corroborating_indices=v.get("corroborating_indices", []),
                    contradicting_indices=v.get("contradicting_indices", []),
                    evidence_quality=v.get("evidence_quality", "medium"),
                    validation_reasoning=v.get("validation_reasoning", "")
                ))

            # Create result
            result = BatchValidationResult(
                validations=validations,
                overall_coherence=float(response_data.get("overall_coherence", 0.7)),
                contradiction_count=int(response_data.get("contradiction_count", 0)),
                corroboration_count=int(response_data.get("corroboration_count", 0)),
                analysis_summary=response_data.get("analysis_summary", "")
            )

            # Cache result
            if self.use_cache:
                self._add_to_cache(cache_key, result)

            return result

        except Exception as e:
            # Fallback: return neutral validations on error
            print(f"Batch validation error: {e}")
            fallback_validations = [
                SignalValidation(
                    signal_index=idx,
                    validation_confidence=0.7,  # Neutral
                    is_corroborated=False,
                    is_contradicted=False,
                    corroborating_indices=[],
                    contradicting_indices=[],
                    evidence_quality="medium",
                    validation_reasoning=f"Validation error: {str(e)}"
                )
                for idx in range(len(signals_subset))
            ]

            return BatchValidationResult(
                validations=fallback_validations,
                overall_coherence=0.7,
                contradiction_count=0,
                corroboration_count=0,
                analysis_summary=f"Validation failed: {str(e)}"
            )

    def apply_validation_to_signals(
        self,
        signals: List[Dict],
        validation_result: BatchValidationResult
    ) -> List[Dict]:
        """
        Apply validation results to signals, adjusting confidence and relevance.

        Args:
            signals: Original signals
            validation_result: Batch validation results

        Returns:
            Updated signals with validation applied
        """
        # Create validation lookup
        validation_map = {v.signal_index: v for v in validation_result.validations}

        updated_signals = []
        for idx, signal in enumerate(signals):
            validation = validation_map.get(idx)
            if not validation:
                # No validation available, keep signal as-is
                updated_signals.append(signal)
                continue

            # Calculate confidence boost/penalty
            confidence_multiplier = 1.0

            # Boost for corroboration
            if validation.is_corroborated:
                confidence_multiplier *= 1.3  # +30% for corroboration

            # Penalty for contradiction
            if validation.is_contradicted:
                confidence_multiplier *= 0.5  # -50% for contradiction

            # Adjust for evidence quality
            if validation.evidence_quality == "high":
                confidence_multiplier *= 1.2
            elif validation.evidence_quality == "low":
                confidence_multiplier *= 0.7

            # Apply validation confidence
            confidence_multiplier *= validation.validation_confidence

            # Update signal
            signal_copy = signal.copy()
            signal_copy["validation_confidence"] = validation.validation_confidence
            signal_copy["is_corroborated"] = validation.is_corroborated
            signal_copy["is_contradicted"] = validation.is_contradicted
            signal_copy["corroboration_count"] = len(validation.corroborating_indices)
            signal_copy["evidence_quality"] = validation.evidence_quality
            signal_copy["validation_reasoning"] = validation.validation_reasoning
            signal_copy["confidence_multiplier"] = confidence_multiplier

            # Adjust relevance score if present
            if "relevance_score" in signal_copy:
                original_score = signal_copy["relevance_score"]
                signal_copy["relevance_score"] = min(1.0, original_score * confidence_multiplier)
                signal_copy["original_relevance_score"] = original_score

            updated_signals.append(signal_copy)

        return updated_signals

    def _generate_cache_key(
        self,
        signals: List[Dict],
        country: Optional[str],
        sector: Optional[str]
    ) -> str:
        """Generate MD5 hash for cache key."""
        # Use signal titles + summaries for cache key
        signal_texts = [f"{s.get('title', '')}|{s.get('summary', '')}" for s in signals[:50]]
        content = f"{'|'.join(signal_texts)}|{country}|{sector}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[BatchValidationResult]:
        """Retrieve from cache if not expired."""
        if cache_key in _batch_cache:
            result, cached_at = _batch_cache[cache_key]
            if datetime.now() - cached_at < timedelta(minutes=_cache_ttl_minutes):
                return result
            else:
                # Expired, remove
                del _batch_cache[cache_key]
        return None

    def _add_to_cache(self, cache_key: str, result: BatchValidationResult):
        """Add result to cache."""
        _batch_cache[cache_key] = (result, datetime.now())

    @staticmethod
    def clear_cache():
        """Clear the entire cache."""
        _batch_cache.clear()

    @staticmethod
    def get_cache_stats() -> Dict:
        """Get cache statistics."""
        now = datetime.now()
        valid_entries = sum(
            1 for _, (_, cached_at) in _batch_cache.items()
            if now - cached_at < timedelta(minutes=_cache_ttl_minutes)
        )
        return {
            "total_entries": len(_batch_cache),
            "valid_entries": valid_entries,
            "ttl_minutes": _cache_ttl_minutes
        }


# Example usage
if __name__ == "__main__":
    # Test the service
    service = ClaudeBatchValidationService()

    test_signals = [
        {
            "source": "Reuters",
            "title": "Russia announces new oil export restrictions",
            "summary": "Russian government announced new restrictions on oil exports to European markets."
        },
        {
            "source": "BBC",
            "title": "EU countries face Russian oil supply cuts",
            "summary": "European Union countries report reduced oil supplies from Russia following new export policies."
        },
        {
            "source": "Al Jazeera",
            "title": "Russia increases oil exports to Asia",
            "summary": "Data shows Russia ramping up oil exports to Asian markets amid European tensions."
        },
    ]

    print("Testing batch validation...")
    result = service.validate_signal_batch(
        signals=test_signals,
        asset_country="Russia",
        asset_sector="Energy"
    )

    print(f"\nValidation Results:")
    print(f"Overall Coherence: {result.overall_coherence:.2f}")
    print(f"Contradictions: {result.contradiction_count}")
    print(f"Corroborations: {result.corroboration_count}")
    print(f"Summary: {result.analysis_summary}")
    print()

    for v in result.validations:
        print(f"Signal [{v.signal_index}]:")
        print(f"  Confidence: {v.validation_confidence:.2f}")
        print(f"  Corroborated: {v.is_corroborated}")
        print(f"  Contradicted: {v.is_contradicted}")
        print(f"  Evidence Quality: {v.evidence_quality}")
        print(f"  Reasoning: {v.validation_reasoning[:100]}...")
        print()
