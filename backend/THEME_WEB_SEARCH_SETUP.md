# Theme-Based Web Search Setup

## Overview

The intelligence retrieval system now performs **targeted web searches for each identified geopolitical theme**. This provides real-time, relevant intelligence signals beyond what's in the RSS feed database.

## How It Works

1. **Theme Identification**: System identifies relevant themes (e.g., "sanctions", "political_instability", "currency_volatility")
2. **Targeted Web Search**: For each top theme (top 3-5 by relevance), performs a targeted web search
3. **Query Construction**: Builds queries like "Turkey sanctions financial markets 2025"
4. **Signal Conversion**: Converts web results to intelligence signals with scoring
5. **Deduplication**: Removes duplicate URLs, keeping highest-scored signals

## Supported Search APIs

### 1. Tavily API (Recommended - Research-Focused)
- **Best for**: Research, academic sources, comprehensive coverage
- **Free tier**: 1,000 searches/month
- **Setup**: 
  1. Sign up at https://tavily.com
  2. Get API key
  3. Add to `.env`: `TAVILY_API_KEY=your_key_here`
  4. Set: `WEB_SEARCH_API=tavily`

### 2. Serper API (Google Search)
- **Best for**: General web search, news articles
- **Free tier**: 2,500 searches/month
- **Setup**:
  1. Sign up at https://serper.dev
  2. Get API key
  3. Add to `.env`: `SERPER_API_KEY=your_key_here`
  4. Set: `WEB_SEARCH_API=serper`

### 3. Perplexity API
- **Best for**: Research with citations
- **Free tier**: Limited
- **Setup**:
  1. Sign up at https://www.perplexity.ai
  2. Get API key
  3. Add to `.env`: `PERPLEXITY_API_KEY=your_key_here`
  4. Set: `WEB_SEARCH_API=perplexity`

## Configuration

Add to `backend/.env`:

```bash
# Web Search API (choose one: tavily, serper, perplexity)
WEB_SEARCH_API=tavily

# API Keys (add the one you're using)
TAVILY_API_KEY=your_tavily_key_here
# OR
SERPER_API_KEY=your_serper_key_here
# OR
PERPLEXITY_API_KEY=your_perplexity_key_here
```

## Fallback Behavior

- If no API key is configured, web search is skipped (system uses database only)
- If web search fails, system continues with database results
- Database queries always run first, web search supplements results

## Query Examples

For a Turkish Equity Fund with "sanctions" theme:
- Query: `Turkey sanctions financial markets recent news`

For a Chinese Tech ETF with "trade_disruption" theme:
- Query: `China trade war technology export ban 2025`

## Benefits

✅ **Real-time intelligence**: Always current, not limited to RSS feed updates
✅ **Targeted searches**: Each theme gets a specific, relevant query
✅ **Better coverage**: Finds signals that RSS feeds might miss
✅ **Investment-focused**: Queries include financial/market context
✅ **Deduplication**: Avoids duplicate signals from multiple sources

## Cost Considerations

- **Tavily**: ~$0.001 per search (1,000 free/month)
- **Serper**: ~$0.0004 per search (2,500 free/month)
- **Perplexity**: Varies by plan

For a typical scan with 3-5 themes, expect 3-5 API calls per scan.
