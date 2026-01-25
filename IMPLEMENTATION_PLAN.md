# Geopolitical Health Scan - Implementation Plan

## Files to Add

### Backend
- `/backend/schemas/geo_risk.py` - Pydantic models for scan inputs/outputs
- `/backend/geo_risk_fallback.py` - Deterministic fallback generator
- `/backend/geo_risk_validate.py` - Result validator
- `/backend/prompts/geo_risk_scan_prompt.py` - LLM prompt builder
- `/backend/regulatory_retriever.py` - Extract chunks from FCA_EXCERPTS.md
- `/backend/geo_risk_store.py` - In-memory audit store
- `/backend/routes/geo_risk.py` - FastAPI route handlers
- Update `/backend/app.py` - Include new routes

### Frontend
- `/src/types/geoRisk.ts` - TypeScript types matching backend schema
- `/src/lib/api/geoRisk.ts` - API helper functions
- Update `/src/components/ClientDashboard.tsx` - Wire GP Health Scan button

### Documentation
- `/docs/regulatory/` - Already created (README, FCA_EXCERPTS, REQUIREMENTS)

## Assumptions

1. **Routing**: Create new `/backend/routes/geo_risk.py` following FastAPI patterns (can use APIRouter or direct app routes)
2. **Ollama Integration**: Use direct httpx calls to Ollama API (similar to agent.py), not via /agent/query endpoint
3. **Client Data**: Use selected client's portfolio data from ClientDashboard (mock data for now)
4. **PDF Extraction**: User will manually extract PDFs later; regulatory_retriever will work with empty/mock content initially
5. **Storage**: In-memory dict for MVP (no DB migrations needed)

## Implementation Order

1. ✅ Create regulatory docs scaffold (DONE)
2. Create schema files (backend + frontend)
3. Create fallback generator
4. Create validator
5. Create prompt template
6. Create regulatory retriever
7. Create audit store
8. Create backend routes
9. Wire frontend API
10. Wire UI button
11. Test end-to-end
