"""
Simple test for Claude Intelligence Service.
Tests only the Claude service without importing the full pipeline.
"""
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Test imports
try:
    from claude_intelligence_service import ClaudeIntelligenceService
    print("✓ Claude service imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    exit(1)


def test_single_signal():
    """Test semantic analysis on single signals."""
    print("\n" + "=" * 80)
    print("CLAUDE SEMANTIC FILTERING - SIMPLE TEST")
    print("=" * 80)
    print()

    # Initialize service
    try:
        service = ClaudeIntelligenceService()
        print("✓ Claude service initialized")
        print(f"  API Key: {service.api_key[:20]}...")
        print()
    except Exception as e:
        print(f"✗ Service initialization failed: {e}")
        return

    # Test cases
    test_cases = [
        {
            "title": "Russia announces new oil export restrictions to Europe",
            "summary": "Russian government announced restrictions on oil exports targeting European markets amid ongoing trade tensions.",
            "asset_country": "Russia",
            "asset_sector": "Energy",
            "themes": ["sanctions", "energy_security", "regional_conflict"],
            "expected": "HIGH RELEVANCE (directly impacts Russian energy)",
        },
        {
            "title": "Japan announces new tech innovation fund for startups",
            "summary": "Japanese government launches $1B fund for technology startups in Tokyo metropolitan area.",
            "asset_country": "Russia",
            "asset_sector": "Energy",
            "themes": ["sanctions", "energy_security", "regional_conflict"],
            "expected": "LOW RELEVANCE (unrelated to Russian energy)",
        },
        {
            "title": "OPEC+ considers production cut amid price volatility",
            "summary": "OPEC+ alliance discussing potential oil production cuts to stabilize global energy markets.",
            "asset_country": "Russia",
            "asset_sector": "Energy",
            "themes": ["energy_security", "trade_disruption"],
            "expected": "MEDIUM RELEVANCE (indirect impact on Russian energy)",
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}")
        print("-" * 80)
        print(f"Title: {test_case['title']}")
        print(f"Asset: {test_case['asset_country']} / {test_case['asset_sector']}")
        print(f"Expected: {test_case['expected']}")
        print()

        try:
            result = service.analyze_signal_relevance(
                signal_title=test_case["title"],
                signal_summary=test_case["summary"],
                asset_country=test_case["asset_country"],
                asset_sector=test_case["asset_sector"],
                themes=test_case["themes"],
                relevance_threshold=0.6,
                use_haiku=True,  # Fast & cheap
            )

            print(f"✓ Analysis completed")
            print(f"  Relevance: {result.relevance_score:.2f} / 1.0")
            print(f"  Confidence: {result.confidence_score:.2f} / 1.0")
            print(f"  Is Relevant: {result.is_relevant} (threshold: 0.6)")
            print(f"  Matched Themes: {', '.join(result.matched_themes) if result.matched_themes else 'None'}")
            print(f"  Reasoning: {result.reasoning}")
            print()

            results.append({
                "case": i,
                "relevance": result.relevance_score,
                "is_relevant": result.is_relevant,
                "expected": test_case["expected"],
            })

        except Exception as e:
            print(f"✗ Analysis failed: {e}")
            print()

        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    for r in results:
        status = "✓" if r["relevance"] > 0 else "✗"
        print(f"{status} Case {r['case']}: Relevance {r['relevance']:.2f} | Passes: {r['is_relevant']} | {r['expected']}")

    print()
    print("Expected behavior:")
    print("  Case 1: Should score HIGH (0.7-1.0) - directly relevant")
    print("  Case 2: Should score LOW (0.0-0.4) - not relevant")
    print("  Case 3: Should score MEDIUM (0.5-0.7) - indirectly relevant")
    print()


def test_cache():
    """Test caching performance."""
    print("=" * 80)
    print("CACHE PERFORMANCE TEST")
    print("=" * 80)
    print()

    service = ClaudeIntelligenceService(use_cache=True)

    test_signal = {
        "title": "Russia oil export restrictions announced",
        "summary": "New restrictions on oil exports to European markets.",
    }

    import time

    # First call
    print("First call (API)...")
    start = time.time()
    result1 = service.analyze_signal_relevance(
        signal_title=test_signal["title"],
        signal_summary=test_signal["summary"],
        asset_country="Russia",
        asset_sector="Energy",
        themes=["sanctions", "energy_security"],
    )
    time1 = time.time() - start
    print(f"✓ Completed in {time1:.3f}s | Relevance: {result1.relevance_score:.2f}")
    print()

    # Second call (should be cached)
    print("Second call (cached)...")
    start = time.time()
    result2 = service.analyze_signal_relevance(
        signal_title=test_signal["title"],
        signal_summary=test_signal["summary"],
        asset_country="Russia",
        asset_sector="Energy",
        themes=["sanctions", "energy_security"],
    )
    time2 = time.time() - start
    print(f"✓ Completed in {time2:.3f}s | Relevance: {result2.relevance_score:.2f}")
    print()

    if time2 > 0:
        speedup = time1 / time2
        print(f"Cache speedup: {speedup:.1f}x faster")
    else:
        print("Cache speedup: Instant (< 1ms)")

    print()

    # Cache stats
    stats = ClaudeIntelligenceService.get_cache_stats()
    print(f"Cache stats: {stats['valid_entries']} valid entries (TTL: {stats['ttl_minutes']} min)")
    print()


if __name__ == "__main__":
    # Run tests
    test_single_signal()
    test_cache()

    print("=" * 80)
    print("✓ PHASE 1 SEMANTIC FILTERING TEST COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Test with real asset via API: POST /geo-risk/scan-detailed")
    print("  2. Compare signal quality before/after semantic filtering")
    print("  3. Monitor Claude API costs (Haiku is very cheap: ~$0.25 per 1M tokens)")
    print()
