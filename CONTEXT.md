You are working inside my existing Mandala repo.

Goal:
Implement an INTERNAL-ONLY “Geopolitical Health Scan” that supports:
- Research & Analysis (Stage 3)
- Suitability reporting (Stage 4)
This is NOT client-facing and must NOT make recommendations.

Tech context (confirmed):
- Frontend: Next.js 16.1.1 App Router, React 19, TypeScript, Tailwind v4
- Backend: FastAPI (Python), Postgres (Neon), SQLAlchemy 2.0, Alembic
- LLM: Ollama llama3.1:8b via /agent/query endpoint
- Existing: RiskScoreDemo component w/ mock generator; Manager page has GP Health Scan button not wired.

Constraints:
- Minimal changes, no heavy dependencies.
- Keep language non-directive (“may warrant consideration”), never “you should buy/sell”.
- Outputs must be probabilistic and auditable (timestamp + inputs + output stored).
- Must work even if LLM fails (deterministic fallback).

Deliverables:
A) A regulatory docs folder scaffold
B) A strict JSON schema for scan output
C) Backend endpoint POST /geo-risk/scan producing that schema
D) Validation + retry + deterministic fallback
E) Audit trail storage (MVP: in-memory) + optional GET /geo-risk/scans
F) Frontend wiring of “GP Health Scan” button to backend + render UI + raw JSON

========================================
STEP 0 — REPO SCAN + IMPLEMENTATION MAP
========================================
1) Scan the repo and identify:
- exact backend folder path and FastAPI app entrypoint
- how /agent/query is implemented and where prompts live
- where the Manager/Client dashboard page is (route path)
- location of RiskScoreDemo component
- any existing API utility function patterns on frontend

2) Before coding, output a short plan listing:
- files to be added/changed
- assumptions

Then implement steps 1–6.

========================================
STEP 1 — REGULATORY DOCS SCAFFOLD
========================================
Create:
- /docs/regulatory/README.md
  - Explain: this folder holds excerpts + internal “requirements cheat sheet”
  - Note: Use FCA Handbook excerpts; internal decision-support only
- /docs/regulatory/FCA_EXCERPTS.md
  - Add placeholder headings for:
    - COBS 9 (Suitability)
    - Consumer Duty (good outcomes / foreseeable harm)
    - SYSC (systems & controls)
    - DISP (complaints / evidence)
  - Add a comment: “Paste excerpts here”
- /docs/regulatory/REQUIREMENTS.md
  - Create a first-pass “Do / Don’t” list even if excerpts are empty:
    DO:
      - probabilistic language, confidence, limitations, timestamped record
      - non-directive “may warrant consideration”
    DON’T:
      - recommendations, predictions, guarantees, client-facing tone
  - Mention: “Generated/updated once excerpts are pasted”

No need to fetch from the internet. Just scaffolding.

========================================
STEP 2 — DEFINE THE CANONICAL OUTPUT SCHEMA
========================================
Define a single schema used across FE/BE:

GeoRiskScanResult JSON shape:
{
  "scan_id": "uuid-or-short-id",
  "created_at": "ISO8601",
  "inputs": {
    "client_id": "string",
    "as_of": "YYYY-MM-DD",
    "horizon_days": 365,
    "risk_tolerance": "low|medium|high",
    "portfolio": {
      "total_value": number,
      "holdings": [
        {"name": "string", "value": number, "region": "string", "sector": "string"}
      ]
    }
  },
  "geo_risk": {
    "scenarios": [
      {"name": "low", "p": 0.xx},
      {"name": "moderate", "p": 0.xx},
      {"name": "severe", "p": 0.xx}
    ],
    "confidence": "low|medium|high",
    "drivers": ["...", "...", "..."],
    "suitability_impact": "2–4 sentences, internal, non-directive",
    "limitations": ["...", "..."],
    "disclaimer": "Internal decision-support only. Not financial advice.",
    "citations": [
      {"doc_id": "FCA_EXCERPTS", "snippet_id": "chunk_01", "section": "COBS 9"}
    ]
  },
  "meta": {
    "model": "llama3.1:8b",
    "used_fallback": boolean,
    "validation": {"passed": boolean, "errors": ["..."]}
  }
}

Rules:
- probabilities sum to 1.00 ± 0.01
- always include limitations + disclaimer
- citations can be empty in MVP

Put this schema in:
- /backend/schemas/geo_risk.py (Pydantic models)
AND mirror it in FE types:
- /src/types/geoRisk.ts

========================================
STEP 3 — BACKEND: FALLBACK + VALIDATION + PROMPT
========================================
3.1 Create deterministic fallback generator:
- /backend/geo_risk_fallback.py
  - function generate_fallback(inputs) -> GeoRiskScanResult
  - deterministic seed based on region strings + as_of date
  - return plausible drivers but generic (NO claims about real events)
  - produce probabilities that sum exactly to 1

3.2 Create validator:
- /backend/geo_risk_validate.py
  - validate_result(result) -> (passed: bool, errors: list[str])
  - checks required fields and probability sum

3.3 Create prompt template:
- /backend/prompts/geo_risk_scan_prompt.py
  - function build_prompt(inputs, regulatory_snippets: list[str]) -> str
  - Must enforce:
    - output JSON only
    - never give recommendations
    - probabilities + confidence + limitations
    - “as-of” reasoning framing
  - Include “STRICT MODE” variant for retry

3.4 Regulatory snippet retrieval (MVP-lite):
- /backend/regulatory_retriever.py
  - For MVP: read /docs/regulatory/FCA_EXCERPTS.md
  - Chunk by headings and paragraphs into small chunks with IDs
  - Use simple keyword scoring (count of query terms) to return top 3 chunks
  - If file empty: return []
  - Return both text and citation objects

========================================
STEP 4 — BACKEND: ENDPOINT + AUDIT STORAGE
========================================
4.1 Add endpoint:
- POST /geo-risk/scan
  - file: /backend/routes/geo_risk.py (or consistent with repo routing)
  - request body matches inputs schema (client_id, as_of, horizon_days, risk_tolerance, portfolio)
  - behavior:
    a) retrieve regulatory snippets (top 3)
    b) call existing Ollama agent endpoint or direct Ollama wrapper used elsewhere
    c) parse JSON
    d) validate; if fail -> retry once with STRICT prompt
    e) if still fail -> fallback
    f) attach meta.validation info + used_fallback flag
    g) store scan in audit store
    h) return result

4.2 Implement audit store (MVP: in-memory):
- /backend/geo_risk_store.py
  - list/dict keyed by scan_id
  - store last N scans (e.g., 100)

4.3 Optional endpoint:
- GET /geo-risk/scans?client_id=...
  - return scans for that client_id (sorted newest first)

Do NOT require DB migrations for MVP. In-memory is fine.

========================================
STEP 5 — FRONTEND: WIRE THE GP HEALTH SCAN BUTTON
========================================
5.1 Identify the Manager/Client dashboard page and the “GP Health Scan” button.
Wire it to call backend POST /geo-risk/scan.

- Create frontend API helper:
  - /src/lib/api/geoRisk.ts
    - function runGeoRiskScan(payload): fetch POST /geo-risk/scan
    - handle errors

5.2 Types:
- Use /src/types/geoRisk.ts
- Ensure FE matches backend schema fields.

5.3 UI rendering:
On the client dashboard:
- Add a “How to demo” block:
  - Internal decision support only
  - Probabilities, not recommendations
  - Designed for suitability + audit trail
- On click:
  - show loading state
  - show result card with:
    - Scenario probabilities
    - Confidence
    - Drivers list
    - Suitability impact paragraph
    - Limitations
    - Disclaimer
  - show “Raw JSON” in a code block
  - show metadata: created_at, model, used_fallback, citations count

5.4 Optional: “View scan history”
If GET /geo-risk/scans is implemented, show a small list of prior scans (date + overall risk posture inferred from severe probability).

========================================
STEP 6 — QA / SAFETY CHECKS
========================================
- Ensure no text uses “recommend”, “should”, “must buy/sell”
- Ensure probabilities always sum to 1 (validator)
- Ensure disclaimers appear
- Ensure the page renders even if backend fails (surface error + allow retry)
- Confirm route works in Next.js App Router without breaking build

========================================
FINAL OUTPUT REQUIRED
========================================
After implementation, print:
1) List of files added/changed
2) How to run locally (frontend + backend commands based on repo scripts)
3) The exact URL/route for the demo page / where the GP Health Scan button is
4) Example request payload for POST /geo-risk/scan

Now proceed.
