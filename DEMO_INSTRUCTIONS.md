# Mandala Demo Instructions

## Overview

Mandala is a Geopolitical Risk Intelligence Platform that provides real-time analysis of geopolitical risks for financial assets. This document provides step-by-step instructions for demonstrating the platform's capabilities.

## Quick Start

1. **Start the Application**:
   ```bash
   # Terminal 1 - Backend
   cd backend
   source .venv/bin/activate
   cd ..
   uvicorn backend.app:app --reload --port 8000

   # Terminal 2 - Frontend
   npm run dev
   ```

2. **Access the Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Navigation

The application has three main pages accessible via the top navigation bar:

- **Desk**: Main dashboard with map view, market feeds, and signals
- **Manager**: Client portfolio management (view-only mode)
- **Demo**: Interactive GP Health Scan demonstration

## Demo Page Walkthrough

### Step 1: Access the Demo Page

1. Click on **"Demo"** in the top navigation bar
2. You'll see the "Geopolitics Risk Calculator" page

### Step 2: Search for an Asset

1. In the **"Asset Search"** section, type a company name or ticker
2. Available demo assets include:
   - **Apple Inc.** (AAPL) - US Technology
   - **Samsung Electronics** (005930) - South Korea Technology
   - **Gold (Spot)** (XAUUSD) - Commodity
3. Select an asset from the dropdown

### Step 3: Run GP Health Scan

1. Click the **"GP Health Scan"** button (located inline with the asset dropdown)
2. The scan will run through 5 automated steps:

   **Step 1: Asset Characterization** (2-3 seconds)
   - Analyzes asset properties: country, region, sector, exposures
   - Displays characterization summary

   **Step 2: Theme Identification** (3-5 seconds)
   - Matches asset against 20+ geopolitical themes
   - Shows top relevant themes as pill-shaped tags with relevance percentages

   **Step 3: Intelligence Retrieval** (15-30 seconds)
   - Performs real-time web searches for each relevant theme
   - Retrieves 20-50 intelligence signals from news sources
   - Scores each signal on relevance, recency, source quality, and activity level
   - Uses AI semantic filtering to keep only high-signal intelligence
   - Displays expandable list of all signals

   **Step 4: Impact Assessment** (10-15 seconds)
   - Analyzes how intelligence signals impact the asset
   - Generates AI summaries for each theme's impact
   - Calculates overall direction and magnitude
   - Displays probability bar showing Negative/Neutral/Positive scores

   **Step 5: Results Display** (instant)
   - Shows final Geopolitical Health Score
   - Displays confidence level
   - Lists key theme impacts with full AI summaries

### Step 4: Review Results

1. **Geopolitical Health Score**: Color-coded bar showing:
   - **Negative** (Red): Probability of negative impact
   - **Neutral** (Yellow): Probability of neutral impact
   - **Positive** (Green): Probability of positive impact

2. **Theme Impacts**: Expand each theme to see:
   - Impact direction (negative/neutral/positive)
   - Impact magnitude
   - Full AI-generated summary explaining the assessment

3. **Intelligence Signals**: Expand to see all retrieved signals with:
   - Source and title
   - Relevance score
   - Publication date
   - Country and theme match

### Step 5: Save or Generate Report

1. **Save Results**: Click "Save Results" to store the scan in the database
   - Creates asset record if it doesn't exist
   - Links scan to asset with full audit trail

2. **Generate Report**: Click "Generate Report" to download a PDF
   - 1-page A4 PDF with Mandala branding
   - Includes asset summary and impact summary
   - Professional format for sharing

## Manager Page Walkthrough

### Viewing Client Portfolios

1. Click on **"Manager"** in the navigation bar
2. Select a client from the dropdown:
   - ACME Corporation
   - Global Growth Fund
   - Conservative Trust
   - Sovereign Wealth Fund Alpha
   - Pension Fund Beta

### Portfolio Dashboard

Each client portfolio shows:

1. **Portfolio Metrics**:
   - Total Portfolio Value
   - Total PnL (with time horizon toggle: YTD, 1Y, All)
   - % PnL

2. **Current Holdings Table**:
   - 6 real assets per client (Apple, Samsung, Nestlé, Saudi Aramco, Tencent, Gold)
   - Each asset has a GP Health Score displayed as a color-coded bar
   - Columns: Name, Country, Class, Sector, Region, Value, % Portfolio, PnL, GP Score
   - All columns are left-aligned
   - GP Score legend shows: Negative (Red), Neutral (Yellow), Positive (Green)

3. **GP Health Dashboard**:
   - **Portfolio GP Health**: Weighted average across all assets
   - **Assets by Risk**: Count of assets in each category
   - **Top Risk Countries**: Countries with highest negative risk
   - **Top Risk Sectors**: Sectors with highest negative risk

4. **Ones to Watch**:
   - Table showing GP Score trends over time
   - Columns: Asset, Current Negative Risk %, 1M Ago, 3M Ago, 6M Ago, Verdict
   - Verdict badges:
     - **Escalating** (Red): Risk increasing over time
     - **Improving** (Green): Risk decreasing over time
     - **No Change** (Gray): Stable risk profile

**Note**: The Manager page is view-only. The GP Health Scan button is disabled.

## Settings Configuration

### Accessing Settings

1. Click the **Settings** button (gear icon) in the top right control bar
2. Settings modal opens with two tabs:
   - **Themes**: Manage geopolitical themes
   - **Scoring**: Configure scoring parameters

### Themes Tab

- View all available geopolitical themes
- Edit theme properties (keywords, countries, sectors, weights)
- Add new themes
- Toggle theme active/inactive status

### Scoring Tab

Configure the intelligence scoring system:

1. **Scoring Weights**: Adjust weights for different scoring factors
   - Base Relevance
   - Theme Match
   - Recency
   - Source Quality
   - Activity Level

2. **Source Quality Scores**: Edit source reliability scores
   - Click "Edit Sources" button
   - Modify existing source scores
   - Add new sources (e.g., new news outlets)
   - Delete sources (except "default")
   - Default sources include: Reuters, BBC, Financial Times, Bloomberg, etc.

3. **Thresholds**: Adjust relevance and semantic filtering thresholds

4. **Pipeline Parameters**: Configure default lookback periods and signal limits

## Key Features to Highlight

### 1. Real-Time Intelligence
- Web search integration (Tavily API)
- Real-time news and analysis retrieval
- Multi-source intelligence aggregation

### 2. AI-Powered Analysis
- Semantic filtering using Claude AI
- Theme impact summaries generated by AI
- Natural language understanding of intelligence signals

### 3. Multi-Factor Scoring
- Relevance scoring (country/region/sector match)
- Recency scoring (exponential decay)
- Source quality weighting
- Activity level assessment
- Theme match scoring

### 4. Comprehensive Audit Trail
- Full pipeline results saved to database
- Asset and scan relational linking
- Historical GP score tracking
- Trend analysis (1M, 3M, 6M)

### 5. Professional Reporting
- One-click PDF report generation
- A4 formatted reports
- Asset and impact summaries
- Theme impact details with AI summaries

## Demo Flow Recommendations

### Quick Demo (5 minutes)
1. Navigate to Demo page
2. Search for "Apple"
3. Run GP Health Scan
4. Show the pipeline progress
5. Highlight the final probability bar
6. Generate PDF report

### Full Demo (15 minutes)
1. Show Manager page with client portfolios
2. Highlight GP Health Dashboard KPIs
3. Show "Ones to Watch" trends
4. Navigate to Demo page
5. Run scan for different asset types (equity, commodity)
6. Show Settings → Scoring → Edit Sources
7. Generate and show PDF report

### Technical Deep Dive (30 minutes)
1. Walk through all 5 pipeline steps in detail
2. Show intelligence signals and scoring breakdown
3. Explain theme identification logic
4. Demonstrate Settings configuration
5. Show database structure (assets, scans)
6. Explain scoring algorithm and tunable parameters

## Troubleshooting

### Scan Taking Too Long
- Normal scan time: 30-60 seconds
- Intelligence retrieval is the longest step (15-30 seconds)
- Web search and AI processing require time

### No Results Appearing
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify database connection in backend/.env

### PDF Not Generating
- Ensure `reportlab` and `Pillow` are installed in backend
- Check backend logs for errors
- Verify logo path: `public/mandala_logo.png`

## Technical Notes

- **Database**: PostgreSQL (Neon/Supabase/Render)
- **Backend**: FastAPI with Python 3.12
- **Frontend**: Next.js 16 with React 19
- **AI**: Claude API for semantic filtering, Ollama for analysis
- **Web Search**: Tavily API for real-time intelligence
- **Caching**: In-memory caching for performance

## Support

For issues or questions:
- Check backend logs: Terminal running uvicorn
- Check frontend logs: Browser console (F12)
- Verify environment variables in `backend/.env`
