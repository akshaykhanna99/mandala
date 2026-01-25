# Mandala backend

This service fetches GDELT + NATO + IAEA updates on demand and stores data in PostgreSQL (Neon).

## Setup

1. Create a `.env` file with your Neon database URL:
   ```env
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

2. Install dependencies and run migrations:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   ```

3. Start the server:
   ```bash
   uvicorn backend.app:app --reload --port 8000
   ```

## Endpoints

- `POST /refresh` fetches sources and updates the database
- `GET /countries` returns the latest snapshots from database
- `GET /countries/{country}` returns a single country snapshot
- `GET /global` returns global items
- `GET /markets` returns market data
- `GET /air-traffic` returns air traffic data
- `GET /notams` returns NOTAMs
- `POST /agent/query` queries the AI agent

## Notes

- All data is stored in PostgreSQL (Neon database)
- Database tables are created automatically on first startup
- CORS is enabled for `http://localhost:3000`
