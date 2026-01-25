"""Theme-based web search for real-time intelligence retrieval.

This module performs targeted web searches for each identified geopolitical theme,
providing real-time, relevant intelligence signals.
"""
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import httpx
from dataclasses import dataclass

from typing import TYPE_CHECKING

from .geo_risk_characterization import AssetProfile
from .geo_risk_theme_mapper import ThemeRelevance, get_geopolitical_themes
from .intelligence_scoring import (
    calculate_recency_score,
    get_source_quality_score,
    calculate_final_score,
)

if TYPE_CHECKING:
    from .geo_risk_intelligence import IntelligenceSignal


@dataclass
class WebSearchResult:
    """Result from a web search."""
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    source: Optional[str] = None


def search_theme_web(
    profile: AssetProfile,
    theme: ThemeRelevance,
    days_lookback: int = 90,
) -> List[WebSearchResult]:
    """
    Search the web for a specific theme related to the asset.
    
    Args:
        profile: Asset profile
        theme: Theme to search for
        days_lookback: How many days back to search
    
    Returns:
        List of web search results
    """
    # Build targeted search query
    query = _build_search_query(profile, theme, days_lookback)
    
    # Use web search API (Tavily recommended, or Serper for Google search)
    # Note: Ollama LLM is used separately for analysis, not for web search
    search_api = os.getenv("WEB_SEARCH_API", "tavily")  # tavily or serper
    
    if search_api == "tavily":
        return _search_tavily(query, days_lookback)
    elif search_api == "serper":
        return _search_serper(query, days_lookback)
    else:
        # Default to Tavily
        return _search_tavily(query, days_lookback)


def _build_search_query(profile: AssetProfile, theme: ThemeRelevance, days_lookback: int = 90) -> str:
    """Build a targeted search query for the theme and asset.
    
    Uses LLM to create natural, well-phrased search queries.
    """
    # Get theme keywords
    themes = get_geopolitical_themes()
    theme_info = themes.get(theme.theme, {})
    theme_keywords = theme_info.get("keywords", [])
    
    # Format theme name for readability
    theme_name = theme.theme.replace("_", " ").title()
    
    # Build context for LLM
    context_parts = []
    if profile.country:
        context_parts.append(f"Country: {profile.country}")
    if profile.region:
        context_parts.append(f"Region: {profile.region}")
    if profile.sector and profile.sector not in ["Diversified", "Cash"]:
        context_parts.append(f"Sector: {profile.sector}")
    if profile.asset_class:
        context_parts.append(f"Asset Class: {profile.asset_class}")
    
    context = ", ".join(context_parts)
    
    # Use LLM to create a natural search query
    try:
        query = _refine_query_with_llm(theme_name, context, theme_keywords, days_lookback)
        if query:
            return query
    except Exception as e:
        print(f"LLM query refinement failed: {e}, using fallback")
    
    # Fallback: Build query manually if LLM fails
    parts = []
    if profile.country:
        parts.append(profile.country)
    elif profile.region:
        parts.append(profile.region)
    
    # Add theme in natural language
    if theme_name:
        parts.append(theme_name.lower())
    
    # Add financial context
    if profile.asset_class == "Equities":
        parts.append("financial markets")
    elif profile.asset_class:
        parts.append("investment")
    
    query = " ".join(parts)
    
    # Add time constraint
    if days_lookback <= 7:
        query += " recent news"
    elif days_lookback <= 30:
        query += " 2025"
    
    return query


def _refine_query_with_llm(theme_name: str, context: str, keywords: List[str], days_lookback: int) -> str | None:
    """Use LLM to create a natural, well-phrased search query."""
    import os
    import httpx
    
    # Check if we should use LLM (can be disabled for faster queries)
    use_llm = os.getenv("USE_LLM_FOR_QUERIES", "true").lower() == "true"
    if not use_llm:
        return None
    
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    
    # Build prompt
    time_context = "recent" if days_lookback <= 7 else "this year" if days_lookback <= 365 else ""
    
    prompt = f"""You are a search query generator for financial/geopolitical news. Return ONLY the search query text.

Theme: {theme_name}
Context: {context}
Keywords: {', '.join(keywords[:3]) if keywords else 'N/A'}
Time: {time_context}

Rules:
- 3-6 words only
- Include specific location (country/region)
- Include specific theme keywords
- Include "2025" or "2026" for recent news
- NO generic words like "news", "latest", "recent"
- Return ONLY the query, no labels or explanations

Good examples:
Russia energy exports sanctions 2025
China Taiwan military tensions 2026
Turkey currency crisis financial impact

Bad examples:
Russia news (too generic)
Latest developments in China (has "latest")
What is happening with Turkey (question format)

Your query:"""
    
    try:
        response = httpx.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {"num_predict": 50},  # Short response
            },
            timeout=5,  # Quick timeout for query generation
        )
        response.raise_for_status()
        data = response.json()
        raw_content = data.get("message", {}).get("content", "").strip()
        
        # Extract query from response - handle various formats
        query = raw_content
        
        # Remove common prefixes/instructions that LLM might include
        prefixes_to_remove = [
            "here's a concise and natural search query:",
            "here's a search query:",
            "query:",
            "search query:",
            "the query is:",
            "here is the query:",
        ]
        query_lower = query.lower()
        for prefix in prefixes_to_remove:
            if query_lower.startswith(prefix):
                query = query[len(prefix):].strip()
                break
        
        # Remove quotes
        query = query.strip('"').strip("'").strip()
        
        # Take first line if multiple lines (in case LLM adds explanation)
        query = query.split("\n")[0].strip()
        
        # Remove any trailing punctuation that might be part of explanation
        query = query.rstrip(".,;:!?")
        
        # Remove any remaining instruction-like text
        if ":" in query:
            # If there's a colon, take everything after it (in case LLM added label)
            parts = query.split(":", 1)
            if len(parts) > 1:
                query = parts[1].strip()
        
        # Final cleanup
        query = query.strip()
        
        # Validate it's reasonable (not empty, not too long, looks like a query)
        if query and len(query.split()) <= 10 and len(query) > 3:
            # Make sure it doesn't look like an instruction
            instruction_words = ["here", "query", "search", "create", "generate", "return"]
            first_word = query.split()[0].lower() if query.split() else ""
            if first_word not in instruction_words:
                return query
    except Exception as e:
        print(f"LLM query generation failed: {e}")
    
    return None


def _search_tavily(query: str, days_lookback: int) -> List[WebSearchResult]:
    """Search using Tavily API (research-focused, good free tier)."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []

    # Reduce results per theme to avoid clutter (10 → 5)
    max_results = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))

    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": False,
                "include_raw_content": False,
                "max_results": max_results,
                "include_domains": _get_trusted_news_domains(),  # Only credible sources
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            # Filter out low-quality results
            title = item.get("title", "")
            snippet = item.get("content", "")
            url = item.get("url", "")

            # Skip if title or snippet is too short (likely not useful)
            if len(title) < 20 or len(snippet) < 50:
                continue

            # Skip if URL contains suspicious patterns
            if _is_low_quality_source(url):
                continue

            results.append(
                WebSearchResult(
                    title=title,
                    url=url,
                    snippet=snippet[:300],  # Limit snippet length
                    published_date=item.get("published_date"),
                    source=_extract_source_from_url(url),
                )
            )

        # Deduplicate by title similarity
        results = _deduplicate_web_results(results)

        return results
    except Exception as e:
        print(f"Tavily search error: {e}")
        return []


def _search_serper(query: str, days_lookback: int) -> List[WebSearchResult]:
    """Search using Serper API (Google search)."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return []

    # Reduce results per theme to avoid clutter
    max_results = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))

    try:
        # Calculate date range
        if days_lookback <= 7:
            time_period = "week"
        elif days_lookback <= 30:
            time_period = "month"
        else:
            time_period = "year"

        response = httpx.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key},
            json={
                "q": query,
                "num": max_results,
                "tbs": f"qdr:{time_period}" if days_lookback <= 30 else None,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("organic", []):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            url = item.get("link", "")

            # Filter out low-quality results
            if len(title) < 20 or len(snippet) < 50:
                continue

            if _is_low_quality_source(url):
                continue

            results.append(
                WebSearchResult(
                    title=title,
                    url=url,
                    snippet=snippet[:300],  # Limit snippet length
                    source=_extract_source_from_url(url),
                )
            )

        # Deduplicate by title similarity
        results = _deduplicate_web_results(results)

        return results
    except Exception as e:
        print(f"Serper search error: {e}")
        return []




def _extract_source_from_url(url: str) -> Optional[str]:
    """Extract source name from URL."""
    if not url:
        return None

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        # Extract main domain name
        parts = domain.split(".")
        if len(parts) >= 2:
            return parts[-2].title()  # e.g., "bbc.co.uk" -> "Bbc"
        return domain
    except Exception:
        return None


def _get_trusted_news_domains() -> List[str]:
    """Get list of trusted news domains for filtering."""
    return [
        # Major news agencies
        "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk",
        # Financial news
        "bloomberg.com", "ft.com", "wsj.com", "cnbc.com", "marketwatch.com",
        # International news
        "aljazeera.com", "france24.com", "dw.com", "theguardian.com",
        # Regional credible sources
        "economist.com", "forbes.com", "axios.com", "politico.com",
        # Government/institutional
        "europa.eu", "un.org", "worldbank.org", "imf.org",
    ]


def _is_low_quality_source(url: str) -> bool:
    """Check if URL is from a low-quality source."""
    if not url:
        return True

    # Patterns that indicate low-quality sources
    low_quality_patterns = [
        "/forum/", "/blog/", "/comment/", "/user/",
        "reddit.com", "twitter.com", "facebook.com",
        "youtube.com", "tiktok.com", "instagram.com",
        "medium.com", "substack.com", "wordpress.com",
        "blogspot.com", "/press-release/", "prweb.com",
    ]

    url_lower = url.lower()
    return any(pattern in url_lower for pattern in low_quality_patterns)


def _deduplicate_web_results(results: List[WebSearchResult]) -> List[WebSearchResult]:
    """Deduplicate web results by title similarity."""
    if not results:
        return results

    deduplicated = []
    seen_titles = []

    for result in results:
        # Check if this title is too similar to any existing title
        is_duplicate = False
        for seen_title in seen_titles:
            if _titles_are_similar(result.title, seen_title):
                is_duplicate = True
                break

        if not is_duplicate:
            deduplicated.append(result)
            seen_titles.append(result.title)

    return deduplicated


def _titles_are_similar(title1: str, title2: str, threshold: float = 0.7) -> bool:
    """Check if two titles are similar using simple word overlap."""
    if not title1 or not title2:
        return False

    # Normalize titles
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())

    # Remove common words
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as"}
    words1 = words1 - stop_words
    words2 = words2 - stop_words

    if not words1 or not words2:
        return False

    # Calculate Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    if union == 0:
        return False

    similarity = intersection / union
    return similarity >= threshold


def convert_web_results_to_signals(
    web_results: List[WebSearchResult],
    profile: AssetProfile,
    theme: ThemeRelevance,
    days_lookback: int,
) -> List:
    """Convert web search results to IntelligenceSignal objects.

    Returns List[IntelligenceSignal] - using List to avoid circular import.
    """
    # Import here to avoid circular dependency
    from .geo_risk_intelligence import IntelligenceSignal

    signals = []

    for result in web_results:
        # Parse published date
        published_at = result.published_date or datetime.now().isoformat()

        # Calculate scores with more conservative base relevance
        # Web results need validation - don't assume high relevance
        base_relevance = 0.5  # Reduced from 0.7 (conservative until validated)
        theme_match_score = theme.relevance_score
        recency_score = calculate_recency_score(published_at, days_lookback)
        source_quality = get_source_quality_score(result.source or "Unknown")

        # Boost source quality for web results from trusted sources
        if _is_trusted_news_source(result.url or ""):
            source_quality = min(1.0, source_quality + 0.1)

        # Calculate final score
        relevance_score = calculate_final_score(
            base_relevance=base_relevance,
            theme_match=theme_match_score,
            recency_score=recency_score,
            source_quality=source_quality,
            activity_level=0.0,  # Not applicable for web results
        )

        signal = IntelligenceSignal(
            source="web_search",
            title=result.title,
            summary=result.snippet[:300] if result.snippet else "",  # Reduced from 500
            topic=_infer_topic_from_text(result.title + " " + result.snippet),
            relevance_score=relevance_score,
            theme_match=theme.theme,
            published_at=published_at,
            url=result.url,
            country=profile.country,
            base_relevance=base_relevance,
            theme_match_score=theme_match_score,
            recency_score=recency_score,
            source_quality=source_quality,
            activity_level_score=0.0,
            # Phase 1 & 2 fields (will be populated if semantic filtering enabled)
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


def _is_trusted_news_source(url: str) -> bool:
    """Check if URL is from a trusted news source."""
    if not url:
        return False

    trusted_domains = _get_trusted_news_domains()
    url_lower = url.lower()

    return any(domain in url_lower for domain in trusted_domains)


def _infer_topic_from_text(text: str) -> str:
    """Infer topic from text (similar to sources.py)."""
    lowered = text.lower()
    
    topic_keywords = {
        "security": ["military", "defense", "missile", "strike", "border", "troops"],
        "energy": ["gas", "oil", "energy", "pipeline", "nuclear", "power"],
        "diplomacy": ["talks", "summit", "minister", "agreement", "sanction"],
        "economy": ["trade", "tariff", "economy", "inflation", "export", "import"],
        "humanitarian": ["aid", "refugee", "humanitarian", "evacuation", "crisis"],
    }
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in lowered for keyword in keywords):
            return topic
    
    return "general"
