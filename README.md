# Mandala

A Geopolitical Risk Intelligence Platform that provides real-time analysis of geopolitical risks for financial assets. Features AI-powered intelligence retrieval, automated risk scoring, and comprehensive portfolio health dashboards.

## 🎥 Demo Video

[Watch the Demo Video](https://your-video-link-here) - See Mandala in action with a complete walkthrough of the GP Health Scan pipeline.

*Replace `https://your-video-link-here` with your actual video URL (YouTube, Vimeo, Loom, etc.)*

## Features

- **GP Health Scan**: Automated 5-step pipeline analyzing geopolitical risks for any asset in under 60 seconds
- **Real-Time Intelligence**: Web search integration with multi-source intelligence aggregation
- **AI-Powered Analysis**: Claude AI for semantic filtering and theme impact summaries
- **Portfolio Management**: View client portfolios with GP health scores and trend analysis
- **PDF Report Generation**: One-click professional PDF reports with asset and impact summaries
- **Tunable Scoring System**: Fully configurable intelligence scoring parameters
- **Audit Trail**: Complete database storage of all scans with relational asset linking

## Development Setup

### Prerequisites

- Node.js (for frontend)
- **Python 3.11 or 3.12** (for backend) - ⚠️ Python 3.13 has compatibility issues with some dependencies
- PostgreSQL database (free options: [Neon](https://neon.tech), [Supabase](https://supabase.com), or [Render](https://render.com))

### Database Setup

1. **Create a PostgreSQL database** (choose one):
   - **Neon** (recommended): Sign up at [neon.tech](https://neon.tech), create a project, copy the connection string
   - **Supabase**: Sign up at [supabase.com](https://supabase.com), create a project, get connection string from Settings → Database
   - **Render**: Create a PostgreSQL database service, copy the internal database URL

2. **Set up environment variables:**
   ```bash
   cd backend
   cp .env.example .env  # If you have an example file
   # Or create .env manually
   ```

   Add your database URL to `backend/.env`:
   ```env
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

### Quick Start

**Terminal 1 - Backend:**
```bash
# Setup virtual environment
cd backend
python3.12 -m venv .venv  # or python3.11
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations (from backend directory)
alembic upgrade head

# Start the server (from project root, not backend directory)
cd ..  # Go to project root
uvicorn backend.app:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
npm install
npm run dev
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)

## Application Pages

- **Desk** (`/desk`): Main dashboard with map view, market feeds, and signals
- **Manager** (`/manager`): Client portfolio management (view-only) with GP Health Dashboard
- **Demo** (`/demo`): Interactive GP Health Scan demonstration

## Key Capabilities

### GP Health Scan Pipeline

1. **Asset Characterization**: Analyzes asset properties (country, region, sector, exposures)
2. **Theme Identification**: Matches asset against 20+ geopolitical themes
3. **Intelligence Retrieval**: Real-time web search with multi-factor scoring
4. **Impact Assessment**: AI-generated theme impact summaries
5. **Probability Calculation**: Negative/Neutral/Positive risk probabilities

### Database Schema

- **Assets**: Store asset information (name, ticker, country, sector, etc.)
- **GP Scans**: Store complete scan results with full audit trail
- **Themes**: Customizable geopolitical themes with tunable weights
- **Scoring Settings**: Global scoring system parameters

## Documentation

- **DEMO_INSTRUCTIONS.md**: Complete walkthrough for demonstrating the platform
- **docs/regulatory/**: Regulatory documentation (FCA excerpts, requirements)

## Notes

- The backend uses PostgreSQL for data storage (Neon/Supabase/Render)
- Database tables are created via Alembic migrations (`alembic upgrade head`)
- Both servers must be running for the app to work
- Required API keys in `backend/.env`:
  - `DATABASE_URL`: PostgreSQL connection string
  - `ANTHROPIC_API_KEY`: For Claude AI semantic filtering (optional)
  - `TAVILY_API_KEY`: For web search intelligence (optional)
  - `OLLAMA_BASE_URL`: For LLM analysis (defaults to localhost)
