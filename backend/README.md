# Mandala backend (manual refresh)

This service fetches GDELT + NATO + IAEA updates on demand and writes country snapshots to a local JSON file.

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

## Endpoints

- `POST /refresh` fetches sources and updates the snapshot store
- `GET /countries` returns the latest snapshots
- `GET /countries/{country}` returns a single country snapshot

## Notes

- `backend/data/snapshots.json` is created on first refresh.
- CORS is enabled for `http://localhost:3000`.
