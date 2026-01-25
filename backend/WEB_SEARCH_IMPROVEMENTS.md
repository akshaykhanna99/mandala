# Web Search Improvements - Reducing Clutter & Improving Quality

## Problem

The front end was cluttered with web search results due to:
1. **Too many results**: 10 results per theme × 5 themes = **50 web results**
2. **Low quality filtering**: All web results assumed relevant (0.7 base score)
3. **Duplicate content**: Similar articles from different sources
4. **Generic queries**: Ollama queries sometimes too broad
5. **Unreliable sources**: Blogs, forums, social media mixed with news

---

## Solutions Implemented

### 1. **Reduced Result Volume** (50 → 15 signals)

**Before**:
- 10 results per theme
- 5 themes searched
- **Total: Up to 50 web results**

**After**:
- **5 results per theme** (configurable via `WEB_SEARCH_MAX_RESULTS`)
- **3 themes searched** (configurable via `MAX_WEB_SEARCH_THEMES`)
- **Total: Up to 15 web results (70% reduction)**

### 2. **Quality Filtering**

Added multiple quality checks before accepting web results:

```python
# Minimum content length
- Skip if title < 20 characters
- Skip if snippet < 50 characters

# Source credibility check
- Only trusted news domains
- Exclude: blogs, forums, social media, press releases

# Deduplication
- Remove articles with similar titles (70% word overlap)
- Keeps only unique content
```

**Trusted News Domains** (whitelist):
- Major agencies: Reuters, AP, BBC
- Financial: Bloomberg, FT, WSJ, CNBC
- International: Al Jazeera, France24, DW, The Guardian
- Government/Institutional: UN, World Bank, IMF

**Blocked Sources** (blacklist):
- Social media: Reddit, Twitter, Facebook, YouTube
- Blogs: Medium, Substack, WordPress, Blogspot
- User-generated: Forums, comment sections
- Marketing: Press releases, prweb.com

### 3. **Improved Query Specificity**

Enhanced Ollama prompts for better query generation:

**Before**:
```
Prompt: "Generate a search query for [theme] and [country]"
Output: "Russia news" (too generic)
```

**After**:
```
Prompt includes:
- Specific rules (3-6 words, include year, no generic terms)
- Good/bad examples
- Explicit instruction to include specific keywords

Output: "Russia energy exports sanctions 2025" (much better)
```

**Rules added**:
- Include specific location (country/region)
- Include specific theme keywords
- Include year (2025/2026) for recent news
- NO generic words like "news", "latest", "recent"
- NO question format

### 4. **Conservative Scoring for Web Results**

**Before**:
- Base relevance: 0.7 (assumed high quality)
- No validation required

**After**:
- Base relevance: 0.5 (conservative until validated)
- Boost +0.1 for trusted news sources
- Will benefit from Phase 1 semantic filtering
- Will benefit from Phase 2 batch validation

### 5. **Summary Length Reduction**

**Before**: 500 characters per snippet
**After**: 300 characters per snippet (40% reduction)

This reduces visual clutter in the front-end while preserving key information.

---

## Configuration

### Environment Variables (`.env`)

```bash
# Web Search Configuration
WEB_SEARCH_API=tavily  # or "serper"
TAVILY_API_KEY=tvly-xxx  # Your Tavily API key
WEB_SEARCH_MAX_RESULTS=5  # 3-5 recommended (default: 5)
MAX_WEB_SEARCH_THEMES=3  # 2-3 recommended (default: 3)
USE_LLM_FOR_QUERIES=true  # Use Ollama for better queries
```

### Tuning for Your Needs

**More Results** (if you want more web intelligence):
```bash
WEB_SEARCH_MAX_RESULTS=7
MAX_WEB_SEARCH_THEMES=4
```

**Fewer Results** (if still too cluttered):
```bash
WEB_SEARCH_MAX_RESULTS=3
MAX_WEB_SEARCH_THEMES=2
```

**Disable Web Search Entirely**:
```bash
MAX_WEB_SEARCH_THEMES=0
```

---

## Expected Impact

### Before vs After

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Max Web Results** | 50 | 15 | **-70%** |
| **Results per Theme** | 10 | 5 | **-50%** |
| **Themes Searched** | 5 | 3 | **-40%** |
| **Duplicate Content** | Common | Removed | **Deduplicated** |
| **Low-Quality Sources** | Included | Filtered | **Higher quality** |
| **Generic Queries** | Common | Rare | **More specific** |
| **Base Relevance** | 0.7 (high) | 0.5 (conservative) | **More realistic** |

### Quality Improvements

1. **Fewer, Better Results**: 15 high-quality signals vs 50 mixed-quality signals
2. **Less Clutter**: Deduplicated and filtered results
3. **Better Queries**: More specific Ollama-generated queries
4. **Trusted Sources Only**: No blogs, forums, or social media
5. **Validated**: Web results now benefit from Phase 1+2 enhancements

---

## How It Works

### Pipeline Flow

```
1. User scans asset
   ↓
2. Top 3 themes identified (reduced from 5)
   ↓
3. For each theme:
   a. Generate specific query with Ollama
      Example: "Russia energy exports sanctions 2025"

   b. Search Tavily/Serper (max 5 results, reduced from 10)

   c. Filter results:
      - Check title length (>20 chars)
      - Check snippet length (>50 chars)
      - Check source credibility (trusted domains only)
      - Remove low-quality sources (blogs, forums, etc.)

   d. Deduplicate:
      - Compare titles with existing results
      - Remove if 70%+ word overlap

   e. Score conservatively:
      - Base relevance: 0.5 (conservative)
      - +0.1 if trusted news source
      - Apply Phase 1 semantic filtering (if enabled)
      - Apply Phase 2 batch validation (if enabled)
   ↓
4. Return top 15 web results (vs 50 before)
```

---

## Testing

### Test the Improvements

1. **Check result count**:
   - Look at `web_searches` in API response
   - Should see 3 themes max (reduced from 5)
   - Should see ~5 results per theme (reduced from 10)

2. **Check query quality**:
   - Look at `query` field in `web_searches`
   - Should be specific (e.g., "Russia energy exports 2025")
   - NOT generic (e.g., "Russia news")

3. **Check source quality**:
   - All web results should be from trusted news sources
   - No blogs, forums, or social media

4. **Check for duplicates**:
   - Titles should be distinct
   - No near-identical articles

### Example API Response

```json
{
  "signals": [
    // Database signals (RSS + snapshots)
    ...

    // Web signals (now fewer, higher quality)
    {
      "source": "web_search",
      "title": "Russia tightens oil export quotas to Europe",
      "summary": "Russian government announced new restrictions...",
      "relevance_score": 0.65,
      "theme_match": "energy_security",
      "url": "https://reuters.com/...",
      "semantic_relevance": 0.75,  // Phase 1
      "is_corroborated": true,  // Phase 2
      "evidence_quality": "high"  // Phase 2
    }
  ],
  "web_searches": [
    {
      "theme": "energy_security",
      "query": "Russia energy exports sanctions 2025",
      "results_count": 5,  // Reduced from 10
      "signals_count": 4  // After filtering
    },
    {
      "theme": "sanctions",
      "query": "Russia financial sanctions Europe 2025",
      "results_count": 5,
      "signals_count": 5
    },
    {
      "theme": "trade_disruption",
      "query": "Russia trade restrictions 2025",
      "results_count": 5,
      "signals_count": 3
    }
  ]
}
```

Notice:
- Only 3 themes searched (not 5)
- ~5 results per theme (not 10)
- **Total: ~12-15 web signals** (not 50)

---

## Front-End Impact

### Reduced Clutter

**Before**:
- 50 web results mixed with 20 database results = **70 total signals**
- Hard to scan
- Many duplicates
- Lots of low-quality sources

**After**:
- 15 web results + 20 database results = **35 total signals**
- **50% reduction in total signals**
- Easier to scan
- No duplicates
- Only high-quality sources

### Better UX

1. **Faster load times**: Fewer API calls, smaller payloads
2. **Less scrolling**: Fewer results to display
3. **Higher signal-to-noise**: Only relevant, trusted sources
4. **Better context**: More specific queries = more relevant results

---

## Maintenance

### If Web Results Still Feel Cluttered

Further reduce in `.env`:
```bash
WEB_SEARCH_MAX_RESULTS=3  # Even fewer per theme
MAX_WEB_SEARCH_THEMES=2  # Even fewer themes
```

### If You Want More Web Results

Increase in `.env`:
```bash
WEB_SEARCH_MAX_RESULTS=7
MAX_WEB_SEARCH_THEMES=4
```

### Add/Remove Trusted Domains

Edit `_get_trusted_news_domains()` in [theme_web_search.py](theme_web_search.py):
```python
def _get_trusted_news_domains() -> List[str]:
    return [
        "reuters.com", "bbc.com", "bloomberg.com",
        # Add your preferred news sources here
        "yournewssource.com",
    ]
```

---

## Summary

**Problem**: Front-end cluttered with 50 web results, many low-quality
**Solution**: Reduced to 15 high-quality results with better filtering
**Impact**:
- **70% fewer web results** (50 → 15)
- **Higher quality** (only trusted sources)
- **Better queries** (Ollama-enhanced specificity)
- **No duplicates** (deduplication)
- **Validated** (Phase 1+2 enhancements)

**Configuration**: Easy to tune via environment variables
**Cost**: No additional cost (still using Ollama + Tavily)
**Benefit**: Much cleaner, more useful intelligence feed

---

## Files Modified

- ✅ [backend/theme_web_search.py](theme_web_search.py) - Added filtering, deduplication, better scoring
- ✅ [backend/geo_risk_intelligence.py](geo_risk_intelligence.py) - Reduced max themes from 5 to 3
- ✅ [backend/.env.example](.env.example) - Added configuration documentation
- ✅ [backend/WEB_SEARCH_IMPROVEMENTS.md](WEB_SEARCH_IMPROVEMENTS.md) - This file

**No breaking changes**: Everything is backward compatible, just better defaults.
