"""
Test script for Phase 1 semantic filtering enhancement.

This script demonstrates the improvement in signal quality by comparing
keyword-based filtering vs Claude-powered semantic filtering.
"""
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geo_risk_characterization import AssetProfile
from geo_risk_theme_mapper import ThemeRelevance
from geo_risk_intelligence import retrieve_intelligence
from claude_intelligence_service import ClaudeIntelligenceService

# Load environment
load_dotenv()


def create_test_asset_profile() -> AssetProfile:
    """Create a test asset profile for Russian energy sector."""
    return AssetProfile(
        id="test-001",
        name="Russian Energy ETF",
        ticker="RSX",
        isin="US1234567890",
        country="Russia",
        region="Europe",
        sub_region="Eastern Europe",
        asset_type="ETF",
        asset_class="Equity",
        sector="Energy",
        value=100000.0,
        allocation_pct=5.0,
        is_emerging_market=True,
        is_developed_market=False,
        is_global_fund=False,
        is_sector_specific=True,
        is_country_specific=True,
        is_government_exposed=False,
        is_energy_exposed=True,
        is_financial_exposed=False,
        is_technology_exposed=False,
        is_infrastructure_exposed=False,
    )


def create_test_themes() -> list[ThemeRelevance]:
    """Create test themes relevant to Russian energy."""
    return [
        ThemeRelevance(
            theme="sanctions",
            relevance_score=0.95,
            reasoning="Russia faces extensive sanctions",
            keywords_matched=["sanction", "embargo", "trade ban"],
        ),
        ThemeRelevance(
            theme="energy_security",
            relevance_score=0.9,
            reasoning="Russian energy sector critical to global supply",
            keywords_matched=["energy", "oil", "gas", "pipeline"],
        ),
        ThemeRelevance(
            theme="regional_conflict",
            relevance_score=0.85,
            reasoning="Ongoing regional tensions",
            keywords_matched=["conflict", "war", "military", "tension"],
        ),
    ]


def test_semantic_filtering():
    """Test semantic filtering with real asset profile."""
    print("=" * 80)
    print("PHASE 1 SEMANTIC FILTERING TEST")
    print("=" * 80)
    print()

    # Create test asset and themes
    profile = create_test_asset_profile()
    themes = create_test_themes()

    print(f"Test Asset: {profile.name}")
    print(f"Country: {profile.country}")
    print(f"Sector: {profile.sector}")
    print(f"Top Themes: {', '.join(t.theme for t in themes[:3])}")
    print()
    print("-" * 80)
    print()

    # Test 1: WITHOUT semantic filtering (baseline)
    print("TEST 1: Keyword-based filtering (BASELINE)")
    print("-" * 80)
    try:
        result_without = retrieve_intelligence(
            profile=profile,
            themes=themes,
            days_lookback=30,  # Shorter window for faster testing
            max_signals=10,
            use_semantic_filtering=False,  # Baseline
        )

        print(f"Signals retrieved: {len(result_without.signals)}")
        print()

        if result_without.signals:
            print("Top 5 signals (keyword-based):")
            for i, signal in enumerate(result_without.signals[:5], 1):
                print(f"\n{i}. [{signal.source}] {signal.title[:80]}")
                print(f"   Score: {signal.relevance_score:.3f} | Theme: {signal.theme_match or 'None'}")
                print(f"   Country: {signal.country or 'N/A'}")
        else:
            print("No signals found.")
    except Exception as e:
        print(f"Error: {e}")

    print()
    print("=" * 80)
    print()

    # Test 2: WITH semantic filtering (Phase 1 enhancement)
    print("TEST 2: Claude semantic filtering (PHASE 1)")
    print("-" * 80)
    try:
        result_with = retrieve_intelligence(
            profile=profile,
            themes=themes,
            days_lookback=30,
            max_signals=10,
            use_semantic_filtering=True,  # Phase 1
            semantic_threshold=0.6,  # Medium-high threshold
        )

        print(f"Signals retrieved: {len(result_with.signals)}")
        print()

        if result_with.signals:
            print("Top 5 signals (semantic filtering):")
            for i, signal in enumerate(result_with.signals[:5], 1):
                print(f"\n{i}. [{signal.source}] {signal.title[:80]}")
                print(f"   Score: {signal.relevance_score:.3f} | Theme: {signal.theme_match or 'None'}")
                print(f"   Country: {signal.country or 'N/A'}")

                if signal.semantic_relevance > 0:
                    print(f"   Claude Relevance: {signal.semantic_relevance:.2f} | Confidence: {signal.semantic_confidence:.2f}")
                    print(f"   Reasoning: {signal.semantic_reasoning[:100]}...")
        else:
            print("No signals found.")
    except Exception as e:
        print(f"Error: {e}")

    print()
    print("=" * 80)
    print()

    # Comparison
    print("COMPARISON")
    print("-" * 80)
    print(f"Without semantic filtering: {len(result_without.signals)} signals")
    print(f"With semantic filtering: {len(result_with.signals)} signals")

    if len(result_without.signals) > 0:
        reduction = (1 - len(result_with.signals) / len(result_without.signals)) * 100
        print(f"Noise reduction: {reduction:.1f}%")

    print()
    print("Expected Outcome:")
    print("- Semantic filtering should reduce signal count (filtering out noise)")
    print("- Remaining signals should be more relevant to Russian energy sector")
    print("- Each signal should have Claude's reasoning for transparency")
    print()


def test_single_signal_analysis():
    """Test semantic analysis on a single signal."""
    print("=" * 80)
    print("SINGLE SIGNAL SEMANTIC ANALYSIS TEST")
    print("=" * 80)
    print()

    service = ClaudeIntelligenceService()

    # Test signals (one relevant, one irrelevant)
    test_cases = [
        {
            "title": "Russia announces new oil export restrictions to Europe",
            "summary": "Russian government announced restrictions on oil exports targeting European markets amid ongoing trade tensions.",
            "expected": "RELEVANT (directly impacts Russian energy)",
        },
        {
            "title": "Japan announces new tech innovation fund",
            "summary": "Japanese government launches $1B fund for technology startups in Tokyo.",
            "expected": "IRRELEVANT (unrelated to Russian energy)",
        },
        {
            "title": "Global markets react to Fed rate decision",
            "summary": "Stock markets worldwide respond to Federal Reserve interest rate announcement.",
            "expected": "BORDERLINE (generic financial news, weak relevance)",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['title'][:60]}...")
        print(f"Expected: {test_case['expected']}")
        print()

        try:
            result = service.analyze_signal_relevance(
                signal_title=test_case["title"],
                signal_summary=test_case["summary"],
                asset_country="Russia",
                asset_sector="Energy",
                themes=["sanctions", "energy_security", "regional_conflict"],
                relevance_threshold=0.6,
            )

            print(f"✓ Relevance Score: {result.relevance_score:.2f}")
            print(f"✓ Confidence Score: {result.confidence_score:.2f}")
            print(f"✓ Is Relevant: {result.is_relevant} (threshold: 0.6)")
            print(f"✓ Matched Themes: {', '.join(result.matched_themes) or 'None'}")
            print(f"✓ Reasoning: {result.reasoning}")
            print()
        except Exception as e:
            print(f"✗ Error: {e}")
            print()

        print("-" * 80)
        print()


def test_cache_performance():
    """Test that caching is working properly."""
    print("=" * 80)
    print("CACHE PERFORMANCE TEST")
    print("=" * 80)
    print()

    from claude_intelligence_service import ClaudeIntelligenceService

    service = ClaudeIntelligenceService(use_cache=True)

    test_signal = {
        "title": "Russia oil export restrictions",
        "summary": "New restrictions announced on oil exports to Europe.",
    }

    print("First call (should hit API)...")
    import time
    start = time.time()
    result1 = service.analyze_signal_relevance(
        signal_title=test_signal["title"],
        signal_summary=test_signal["summary"],
        asset_country="Russia",
        asset_sector="Energy",
        themes=["sanctions", "energy_security"],
    )
    time1 = time.time() - start
    print(f"✓ Completed in {time1:.3f}s")
    print(f"  Relevance: {result1.relevance_score:.2f}")
    print()

    print("Second call (should hit cache)...")
    start = time.time()
    result2 = service.analyze_signal_relevance(
        signal_title=test_signal["title"],
        signal_summary=test_signal["summary"],
        asset_country="Russia",
        asset_sector="Energy",
        themes=["sanctions", "energy_security"],
    )
    time2 = time.time() - start
    print(f"✓ Completed in {time2:.3f}s")
    print(f"  Relevance: {result2.relevance_score:.2f}")
    print()

    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"Cache speedup: {speedup:.1f}x faster")
    print()

    # Cache stats
    stats = ClaudeIntelligenceService.get_cache_stats()
    print(f"Cache stats: {stats['valid_entries']} valid entries (TTL: {stats['ttl_minutes']} min)")
    print()


if __name__ == "__main__":
    # Run tests
    print("\n")

    # Test 1: Single signal analysis (fast)
    test_single_signal_analysis()

    # Test 2: Cache performance
    test_cache_performance()

    # Test 3: Full pipeline comparison (slower, requires database)
    print("\nWould you like to run the full pipeline test?")
    print("This requires database access and will take longer.")
    response = input("Run full test? (y/n): ").lower().strip()

    if response == 'y':
        test_semantic_filtering()
    else:
        print("\nSkipping full pipeline test.")
        print("\nTo test the full pipeline later, run:")
        print("  python test_semantic_filtering.py")

    print("\n✓ Phase 1 testing complete!")
    print()
