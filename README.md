# Mandala

A geopolitics intelligence dashboard with a Next.js frontend and FastAPI backend.

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

### Notes

- The backend uses PostgreSQL for data storage
- Database tables are automatically created on first startup
- Both servers must be running for the app to work
- Optional: Create `backend/.env` for API keys (see `backend/README.md` for details)
