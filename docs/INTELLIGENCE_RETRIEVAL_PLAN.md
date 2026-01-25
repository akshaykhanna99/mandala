# Intelligence Retrieval Plan

## Current State Analysis

### Data Sources Available
1. **Global Items** (`global_items` table)
   - RSS feed articles with title, summary, topic
   - Countries, country_ids arrays
   - Published dates, source URLs
   - Topics: Geopolitics, Economics, Security, etc.

2. **Country Snapshots** (`country_snapshots` table)
   - Aggregated country-level intelligence
   - Events (EventCluster objects with title, summary, why, confidence)
   - Activity levels (Low/Medium/High/Critical)
   - Stats (signals count, disputes, confidence)
   - Updated timestamps

3. **Market Items** (`market_items` table)
   - Market data (prices, changes)
   - Could provide context but less relevant for geopolitical risk

### Current Implementation Issues
1. **Performance**: Loads ALL data into memory, then filters
2. **Search Quality**: Simple keyword substring matching
3. **No Database-Level Filtering**: All filtering done in Python
4. **No Caching**: Re-queries database on every scan
5. **Signal Prioritization**: Basic scoring, could be more sophisticated
6. **Signal Freshness**: Date filtering but no decay/weighting
7. **Source Quality**: Not weighted (all sources treated equally)
8. **No Semantic Search**: Can't find conceptually similar signals

---

## Proposed Architecture

### Phase 1: Database Optimization (Immediate)
**Goal**: Filter at database level, reduce memory usage

#### 1.1 Add Database Indexes
```sql
-- For global_items
CREATE INDEX idx_global_items_countries ON global_items USING GIN(countries);
CREATE INDEX idx_global_items_published_at ON global_items(published_at);
CREATE INDEX idx_global_items_topic ON global_items(topic);

-- For country_snapshots
CREATE INDEX idx_snapshots_name ON country_snapshots(name);
CREATE INDEX idx_snapshots_activity_level ON country_snapshots(activity_level);
CREATE INDEX idx_snapshots_updated_at ON country_snapshots(updated_at);
```

#### 1.2 Create Filtered Query Functions
```python
def load_global_items_filtered(
    countries: List[str] | None = None,
    topics: List[str] | None = None,
    days_lookback: int = 90,
    limit: int = 100
) -> List[GlobalItem]:
    """Query with filters at DB level."""
    # Use SQLAlchemy filters instead of loading all
```

#### 1.3 Add Full-Text Search (PostgreSQL)
```sql
-- Add full-text search column
ALTER TABLE global_items ADD COLUMN search_vector tsvector;
CREATE INDEX idx_global_items_search ON global_items USING GIN(search_vector);

-- Update trigger to maintain search_vector
CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE ON global_items
FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(
    search_vector, 'pg_catalog.english', title, summary, topic
);
```

### Phase 2: Enhanced Scoring (Short-term)
**Goal**: Better signal relevance scoring

#### 2.1 Multi-Factor Scoring
```python
@dataclass
class SignalScore:
    base_relevance: float      # Country/region/sector match
    theme_match: float         # Theme keyword/semantic match
    recency_score: float       # How recent (with decay)
    source_quality: float      # Source reputation/quality
    activity_level: float      # Country activity level (for snapshots)
    signal_strength: float      # Event confidence, multiple signals
    final_score: float          # Weighted combination
```

#### 2.2 Recency Decay Function
```python
def calculate_recency_score(published_at: datetime, days_lookback: int) -> float:
    """Exponential decay: newer signals weighted higher."""
    days_ago = (datetime.now() - published_at).days
    if days_ago > days_lookback:
        return 0.0
    # Exponential decay: 1.0 for today, ~0.5 for 30 days, ~0.1 for 90 days
    return math.exp(-days_ago / 30.0)
```

#### 2.3 Source Quality Weighting
```python
SOURCE_QUALITY_SCORES = {
    "Reuters": 1.0,
    "BBC": 1.0,
    "Financial Times": 0.95,
    "The Guardian": 0.9,
    "Al Jazeera": 0.85,
    # ... etc
}
```

#### 2.4 Activity Level Weighting (Snapshots)
```python
ACTIVITY_LEVEL_SCORES = {
    "Critical": 1.0,
    "High": 0.8,
    "Medium": 0.5,
    "Low": 0.2,
}
```

### Phase 3: Semantic Search (Medium-term)
**Goal**: Find conceptually similar signals, not just keyword matches

#### 3.1 Embedding Generation
- Option A: Use OpenAI/Anthropic embeddings API
- Option B: Use local embedding model (sentence-transformers)
- Option C: Use Ollama embeddings (if available)

#### 3.2 Vector Storage
```sql
-- Add embedding column
ALTER TABLE global_items ADD COLUMN embedding vector(384);  -- or 1536 for OpenAI
CREATE INDEX idx_global_items_embedding ON global_items USING ivfflat(embedding);
```

#### 3.3 Semantic Matching
```python
def find_semantic_matches(
    query_embedding: List[float],
    asset_profile: AssetProfile,
    themes: List[ThemeRelevance],
    limit: int = 20
) -> List[IntelligenceSignal]:
    """Use cosine similarity to find conceptually similar signals."""
    # Query: "Turkey financial sector sanctions risk"
    # Finds: Articles about Turkish banks, currency issues, trade restrictions
    # Even if they don't contain exact keywords
```

### Phase 4: Signal Aggregation (Medium-term)
**Goal**: Combine multiple signals for same theme/country

#### 4.1 Signal Clustering
```python
@dataclass
class SignalCluster:
    theme: str
    country: str | None
    signals: List[IntelligenceSignal]
    aggregated_score: float
    signal_count: int
    earliest_signal: datetime
    latest_signal: datetime
    trend: str  # "increasing", "decreasing", "stable"
```

#### 4.2 Trend Detection
- Multiple signals on same theme = stronger signal
- Recent increase in signals = emerging risk
- Decreasing signals = risk subsiding

### Phase 5: Caching & Performance (Short-term)
**Goal**: Reduce database load, improve response times

#### 5.1 Query Result Caching
```python
from functools import lru_cache
from datetime import timedelta

@lru_cache(maxsize=100)
def get_cached_intelligence(
    country: str | None,
    region: str,
    sector: str,
    cache_key: str  # Hash of inputs
) -> List[IntelligenceSignal]:
    """Cache results for 5-15 minutes."""
    # Invalidate cache when new data is refreshed
```

#### 5.2 Incremental Updates
- Don't reload all data on every scan
- Track last scan time, only query new/updated items
- Use database `updated_at` timestamps

### Phase 6: Advanced Features (Long-term)
**Goal**: More sophisticated intelligence analysis

#### 6.1 Signal Relationships
- Track which signals reference each other
- Build signal graph (signal A leads to signal B)
- Identify cascading risks

#### 6.2 Temporal Patterns
- Detect recurring patterns (e.g., "sanctions announced every 6 months")
- Seasonal patterns (e.g., "elections in Q2")
- Historical precedent matching

#### 6.3 Cross-Asset Intelligence
- If scanning multiple holdings, identify shared risks
- Portfolio-level risk aggregation
- Diversification analysis

---

## Implementation Priority

### Must Have (Phase 1)
1. ✅ Database-level filtering (reduce memory usage)
2. ✅ Add indexes for common queries
3. ✅ Recency decay scoring

### Should Have (Phase 2)
4. ✅ Multi-factor scoring (source quality, activity level)
5. ✅ Signal aggregation/clustering
6. ✅ Basic caching

### Nice to Have (Phase 3)
7. ⚠️ Semantic search with embeddings
8. ⚠️ Temporal pattern detection
9. ⚠️ Signal relationship graph

---

## Proposed Query Strategy

### For Global Items:
```python
# Step 1: Filter by country (if specific country)
if profile.country:
    query = query.filter(GlobalItemTable.countries.contains([profile.country]))

# Step 2: Filter by date range
cutoff_date = datetime.now() - timedelta(days=days_lookback)
query = query.filter(GlobalItemTable.published_at >= cutoff_date)

# Step 3: Full-text search for themes
if themes:
    theme_keywords = " | ".join(get_all_theme_keywords(themes))
    query = query.filter(
        GlobalItemTable.search_vector.match(theme_keywords)
    )

# Step 4: Limit and order
query = query.order_by(GlobalItemTable.published_at.desc()).limit(100)

# Step 5: Score in Python (lighter processing)
```

### For Country Snapshots:
```python
# Step 1: Direct country match (if available)
if profile.country:
    query = query.filter(CountrySnapshotTable.name.ilike(f"%{profile.country}%"))

# Step 2: Filter by activity level (high priority)
query = query.filter(
    CountrySnapshotTable.activity_level.in_(["High", "Critical"])
)

# Step 3: Order by activity level, then updated_at
query = query.order_by(
    CountrySnapshotTable.activity_level.desc(),
    CountrySnapshotTable.updated_at.desc()
).limit(50)
```

---

## Scoring Formula (Proposed)

```python
final_score = (
    base_relevance * 0.3 +      # Country/region/sector match
    theme_match * 0.25 +        # Theme keyword/semantic match
    recency_score * 0.2 +       # How recent (decay function)
    source_quality * 0.15 +     # Source reputation
    activity_level * 0.1        # Country activity (snapshots only)
)
```

---

## Testing Strategy

1. **Unit Tests**: Scoring functions, date parsing, filtering logic
2. **Integration Tests**: Database queries with test data
3. **Performance Tests**: Query time, memory usage, cache hit rates
4. **Quality Tests**: Verify top signals are actually relevant

---

## Migration Path

1. **Week 1**: Add database indexes, implement filtered queries
2. **Week 2**: Enhance scoring with recency decay, source quality
3. **Week 3**: Add caching, signal aggregation
4. **Week 4+**: Semantic search (if needed), advanced features

---

## Questions to Resolve

1. **Embedding Model**: Which to use? (OpenAI, local, Ollama?)
2. **Cache Duration**: How long to cache? (5 min? 15 min?)
3. **Signal Limit**: How many signals per scan? (20? 50? 100?)
4. **Historical Data**: How far back to search? (90 days? 180 days?)
5. **Source Quality**: How to determine quality scores? (Manual? ML-based?)
