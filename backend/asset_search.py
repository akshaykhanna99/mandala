"""Asset search using web search + Claude Haiku for information extraction."""
import os
from typing import Optional
from dataclasses import dataclass
import httpx


@dataclass
class AssetInfo:
    """Extracted asset information."""
    name: str
    ticker: Optional[str]
    isin: Optional[str]
    country: Optional[str]
    region: Optional[str]
    sub_region: Optional[str]
    sector: Optional[str]
    asset_class: Optional[str]
    description: Optional[str]
    confidence: float  # 0.0-1.0


def search_asset(query: str) -> Optional[AssetInfo]:
    """
    Search for an asset using web search and extract information with Claude Haiku.

    Args:
        query: User's search query (e.g., "TSMC", "Taiwan Semiconductor", "Saudi Aramco")

    Returns:
        AssetInfo with extracted details, or None if not found
    """
    # Step 1: Web search for the asset
    web_results = _web_search_asset(query)

    if not web_results:
        return None

    # Step 2: Use Claude Haiku to extract asset information
    asset_info = _extract_asset_info_with_claude(query, web_results)

    return asset_info


def _web_search_asset(query: str) -> Optional[str]:
    """Perform web search for asset information."""
    # Check which web search API is available
    web_search_api = os.getenv("WEB_SEARCH_API", "tavily").lower()

    if web_search_api == "tavily":
        return _search_tavily_asset(query)
    elif web_search_api == "serper":
        return _search_serper_asset(query)
    else:
        return None


def _search_tavily_asset(query: str) -> Optional[str]:
    """Search using Tavily API."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return None

    try:
        # Enhance query for better results
        enhanced_query = f"{query} company stock ticker country sector"

        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": enhanced_query,
                "search_depth": "basic",
                "include_answer": True,
                "include_raw_content": False,
                "max_results": 5,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Combine answer + top results
        context = ""
        if data.get("answer"):
            context += f"Summary: {data['answer']}\n\n"

        context += "Top Results:\n"
        for item in data.get("results", [])[:3]:
            context += f"- {item.get('title', '')}\n"
            context += f"  {item.get('content', '')[:300]}...\n\n"

        return context
    except Exception as e:
        print(f"Tavily search error: {e}")
        return None


def _search_serper_asset(query: str) -> Optional[str]:
    """Search using Serper API (Google search)."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return None

    try:
        # Enhance query for better results
        enhanced_query = f"{query} company stock ticker country sector"

        response = httpx.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key},
            json={
                "q": enhanced_query,
                "num": 5,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Combine knowledge graph + top results
        context = ""

        # Knowledge graph (if available)
        if data.get("knowledgeGraph"):
            kg = data["knowledgeGraph"]
            context += f"Knowledge Graph:\n"
            context += f"Title: {kg.get('title', '')}\n"
            context += f"Description: {kg.get('description', '')}\n"
            if kg.get("attributes"):
                for key, value in list(kg["attributes"].items())[:5]:
                    context += f"{key}: {value}\n"
            context += "\n"

        # Top results
        context += "Top Results:\n"
        for item in data.get("organic", [])[:3]:
            context += f"- {item.get('title', '')}\n"
            context += f"  {item.get('snippet', '')}\n\n"

        return context
    except Exception as e:
        print(f"Serper search error: {e}")
        return None


def _extract_asset_info_with_claude(query: str, web_context: str) -> Optional[AssetInfo]:
    """Use Claude Haiku to extract structured asset information from web search results."""
    api_key = os.getenv("CLAUDE_API")
    if not api_key:
        # Fallback without Claude
        return AssetInfo(
            name=query,
            ticker=None,
            isin=None,
            country=None,
            region=None,
            sub_region=None,
            sector=None,
            asset_class=None,
            description=None,
            confidence=0.3,
        )

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        prompt = f"""You are a financial data extraction assistant. Extract structured information about the asset from the web search results.

USER QUERY: {query}

WEB SEARCH RESULTS:
{web_context}

Extract the following information in JSON format:
{{
  "name": "Full official company/asset name",
  "ticker": "Stock ticker symbol (e.g., TSMC, 2222.SR, or null if not found)",
  "isin": "ISIN code (or null if not found)",
  "country": "Primary country of operation",
  "region": "Geographic region (e.g., Asia, Middle East, Europe, North America, etc.)",
  "sub_region": "Sub-region (e.g., East Asia, Gulf States, etc., or null)",
  "sector": "Industry sector (e.g., Technology, Energy, Financials, etc.)",
  "asset_class": "Asset class (Equities, Fixed Income, Commodities, Alternatives, or null)",
  "description": "Brief 1-sentence description",
  "confidence": 0.0-1.0 (confidence in the extraction)
}}

Requirements:
- Use professional financial terminology
- Be precise and factual
- Set confidence low (0.3-0.5) if information is unclear
- Return ONLY valid JSON, no other text
"""

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            temperature=0.1,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse JSON response
        import json
        response_text = message.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        data = json.loads(response_text)

        return AssetInfo(
            name=data.get("name", query),
            ticker=data.get("ticker"),
            isin=data.get("isin"),
            country=data.get("country"),
            region=data.get("region"),
            sub_region=data.get("sub_region"),
            sector=data.get("sector"),
            asset_class=data.get("asset_class"),
            description=data.get("description"),
            confidence=float(data.get("confidence", 0.5)),
        )

    except Exception as e:
        print(f"Claude extraction error: {e}")
        # Fallback without Claude
        return AssetInfo(
            name=query,
            ticker=None,
            isin=None,
            country=None,
            region=None,
            sub_region=None,
            sector=None,
            asset_class=None,
            description=None,
            confidence=0.3,
        )
