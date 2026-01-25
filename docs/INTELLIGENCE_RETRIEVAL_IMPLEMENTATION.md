# Intelligence Retrieval Implementation Documentation

## Overview

The intelligence retrieval system has been enhanced with database-level filtering, multi-factor scoring, and caching to improve both performance and signal quality.

## Architecture

### Pipeline Flow

```
Asset Profile → Database Filtering → Multi-Factor Scoring → Theme Matching → Signal Aggregation → Top N Signals
```

### Components

1. **Database Optimization** (`alembic/versions/002_add_intelligence_indexes.py`)
   - GIN index on `global_items.countries` for array searches
   - Index on `global_items.published_at` for date filtering
   - Index on `country_snapshots.activity_level` for priority filtering
   - Index on `country_snapshots.updated_at_db` for date filtering

2. **Filtered Queries** (`data_store_filtered.py`)
   - `load_global_items_filtered()`: Database-level filtering by country, topic, date
   - `load_snapshots_filtered()`: Database-level filtering by country, activity level, date
   - Reduces memory usage by filtering at database level

3. **Scoring System** (`intelligence_scoring.py`)
   - `calculate_recency_score()`: Exponential decay (newer = higher score)
   - `get_source_quality_score()`: Source reputation weighting
   - `get_activity_level_score()`: Country activity level weighting
   - `calculate_final_score()`: Weighted combination of all factors

4. **Intelligence Retrieval** (`geo_risk_intelligence.py`)
   - `retrieve_intelligence()`: Main retrieval function
   - Uses filtered queries and multi-factor scoring
   - Theme-based signal matching
   - Returns top N signals sorted by relevance

5. **Caching Layer** (`geo_risk_intelligence_cache.py`)
   - In-memory cache with 10-minute TTL
   - Cache invalidation on data refresh
   - Reduces database load for repeated queries

## Scoring Formula

### Final Score Calculation

```
final_score = (
    base_relevance * 0.3 +      # Country/region/sector match
    theme_match * 0.25 +        # Theme keyword/semantic match
    recency_score * 0.2 +       # How recent (exponential decay)
    source_quality * 0.15 +     # Source reputation
    activity_level * 0.1        # Country activity (snapshots only)
)
```

### Recency Decay

Exponential decay function:
- **Today**: 1.0
- **7 days ago**: ~0.8
- **30 days ago**: ~0.5
- **90 days ago**: ~0.1

Formula: `e^(-days_ago / 30)`

### Source Quality Scores

**Tier 1 (0.9-1.0)**: Reuters, BBC, Financial Times, NYT, WSJ, Bloomberg, AP

**Tier 2 (0.8-0.9)**: Al Jazeera, CNN, The Economist, Foreign Policy

**Tier 3 (0.7)**: Default for unknown sources

### Activity Level Scores

- **Critical**: 1.0
- **High**: 0.8
- **Medium**: 0.5
- **Low**: 0.2

## Database Queries

### Global Items Query

```python
# Filtered by:
- Countries (array containment: countries && ARRAY['Turkey'])
- Topics (if specified)
- Date range (published_at within days_lookback)
- Ordered by: created_at DESC
- Limited to: 200 items (then filtered further)
```

### Country Snapshots Query

```python
# Filtered by:
- Country name (case-insensitive partial match)
- Activity levels (Critical, High, Medium - excludes Low)
- Date range (updated_at_db within days_lookback)
- Ordered by: activity_level priority, then updated_at_db DESC
- Limited to: 50 snapshots
```

## Usage

### Basic Usage

```python
from geo_risk_characterization import characterize_asset
from geo_risk_theme_mapper import identify_relevant_themes
from geo_risk_intelligence_cache import retrieve_intelligence_cached

# Step 1: Characterize asset
profile = characterize_asset(holding)

# Step 2: Identify themes
themes = identify_relevant_themes(profile)

# Step 3: Retrieve intelligence (with caching)
signals = retrieve_intelligence_cached(
    profile=profile,
    themes=themes,
    days_lookback=90,
    max_signals=20,
)
```

### Without Caching

```python
from geo_risk_intelligence import retrieve_intelligence

signals = retrieve_intelligence(
    profile=profile,
    themes=themes,
    days_lookback=90,
    max_signals=20,
)
```

## Performance Improvements

### Before
- Loaded ALL data into memory (~1000s of items)
- Filtered in Python (slow)
- No caching (re-queried every time)
- Simple keyword matching

### After
- Database-level filtering (only loads relevant data)
- Multi-factor scoring (better signal quality)
- 10-minute cache (reduces DB load)
- Indexed queries (faster searches)

### Expected Performance
- **Query time**: ~50-200ms (down from 500-1000ms)
- **Memory usage**: ~10-50MB (down from 100-500MB)
- **Cache hit rate**: ~70-80% for repeated queries

## Migration

### Step 1: Run Database Migration

```bash
cd backend
alembic upgrade head
```

This adds the necessary indexes for performance.

### Step 2: Verify Indexes

```sql
-- Check indexes were created
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename IN ('global_items', 'country_snapshots');
```

### Step 3: Test Performance

```python
# Test query performance
import time
from geo_risk_intelligence_cache import retrieve_intelligence_cached

start = time.time()
signals = retrieve_intelligence_cached(profile, themes)
elapsed = time.time() - start
print(f"Query time: {elapsed:.2f}s")
```

## Cache Management

### Cache Invalidation

Cache is automatically invalidated when:
- `/refresh` endpoint is called (new data loaded)

### Manual Cache Invalidation

```python
from geo_risk_intelligence_cache import invalidate_cache

invalidate_cache()
```

### Cache Statistics

```python
from geo_risk_intelligence_cache import get_cache_stats

stats = get_cache_stats()
print(f"Cache size: {stats['cache_size']}")
```

## Troubleshooting

### Slow Queries

1. **Check indexes**: Ensure migration ran successfully
2. **Check date parsing**: Some date formats may not parse correctly
3. **Reduce days_lookback**: Smaller lookback window = faster queries
4. **Check database size**: Large datasets may need additional optimization

### Low Signal Quality

1. **Check theme matching**: Ensure themes are correctly identified
2. **Check source quality**: Verify source names match quality scores
3. **Adjust scoring weights**: Modify weights in `calculate_final_score()`
4. **Check date filtering**: Ensure recent data is available

### Cache Issues

1. **Cache not working**: Check `use_cache=True` is set
2. **Stale data**: Cache TTL is 10 minutes, adjust if needed
3. **Memory issues**: Reduce cache size or disable caching

## Future Enhancements

### Phase 3: Semantic Search
- Add embedding generation for signals
- Vector similarity search
- Find conceptually similar signals

### Phase 4: Signal Aggregation
- Cluster related signals
- Detect trends (increasing/decreasing risk)
- Multi-signal confidence boosting

### Phase 5: Advanced Features
- Signal relationship graphs
- Temporal pattern detection
- Cross-asset intelligence

## API Reference

See individual module docstrings for detailed API documentation:
- `geo_risk_intelligence.py`: Main retrieval functions
- `intelligence_scoring.py`: Scoring functions
- `data_store_filtered.py`: Filtered query functions
- `geo_risk_intelligence_cache.py`: Caching layer
