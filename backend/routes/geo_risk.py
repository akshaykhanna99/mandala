"""FastAPI routes for geopolitical risk scanning."""
import json
import os
import re
from datetime import datetime
from typing import List
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..schemas.geo_risk import (
    GeoRiskScanRequest,
    GeoRiskScanResult,
    GeoRiskScanInputs,
    GeoRiskOutput,
    Scenario,
    GeoRiskScanMeta,
    ValidationResult,
    DetailedPipelineResult,
    ThemeDetail,
    IntelligenceSignalDetail,
    ThemeImpactDetail,
    AggregateImpactDetail,
    ActionProbabilitiesDetail,
    WebSearchDetail,
)
from ..geo_risk_fallback import generate_fallback
from ..geo_risk_validate import validate_result
from ..prompts.geo_risk_scan_prompt import build_prompt
from ..regulatory_retriever import retrieve_regulatory_snippets, get_snippet_texts
from ..geo_risk_store import get_store
from ..geo_risk_pipeline import run_pipeline_simple, run_pipeline, run_pipeline_streaming
from ..geo_risk_intelligence_cache import invalidate_cache

router = APIRouter(prefix="/geo-risk", tags=["geo-risk"])


def _call_ollama(prompt: str, model: str = None) -> str:
    """Call Ollama API directly."""
    if model is None:
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    base_url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    
    try:
        # Use /api/chat endpoint (same as agent.py)
        response = httpx.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {"num_predict": 800},  # Enough for JSON response
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        # Extract content from message response
        message = data.get("message", {})
        return message.get("content", "").strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama call failed: {str(e)}")


def _extract_json_from_response(text: str) -> dict:
    """Extract JSON from LLM response (may have markdown or extra text)."""
    # Try to find JSON object
    # Look for { ... } pattern
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Try parsing entire response as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from code blocks
    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass
    
    raise ValueError("Could not extract valid JSON from response")


def _parse_llm_response(response_text: str, inputs: GeoRiskScanInputs, model: str) -> GeoRiskScanResult:
    """Parse LLM response into GeoRiskScanResult."""
    try:
        data = _extract_json_from_response(response_text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM JSON: {str(e)}")
    
    # Validate and construct result
    try:
        geo_risk_output = GeoRiskOutput(
            scenarios=[
                Scenario(name=s["name"], p=float(s["p"]))
                for s in data.get("scenarios", [])
            ],
            confidence=data.get("confidence", "medium"),
            drivers=data.get("drivers", []),
            suitability_impact=data.get("suitability_impact", ""),
            limitations=data.get("limitations", []),
            disclaimer=data.get("disclaimer", "Internal decision-support only. Not financial advice."),
            citations=[],  # MVP: empty citations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to construct output: {str(e)}")
    
    # Generate scan_id and timestamp
    scan_id = f"scan_{int(datetime.now().timestamp())}_{inputs.client_id[:8]}"
    created_at = datetime.now().isoformat()
    
    result = GeoRiskScanResult(
        scan_id=scan_id,
        created_at=created_at,
        inputs=inputs,
        geo_risk=geo_risk_output,
        meta=GeoRiskScanMeta(
            model=model,
            used_fallback=False,
            validation=ValidationResult(passed=False, errors=[]),  # Will validate next
        ),
    )
    
    # Validate
    validation = validate_result(result)
    result.meta.validation = validation
    
    return result


@router.post("/scan")
def scan_geo_risk(request: GeoRiskScanRequest) -> GeoRiskScanResult:
    """
    Run a geopolitical risk scan.
    
    Uses the new pipeline-based approach for per-holding analysis.
    Returns a probabilistic risk assessment with scenarios, confidence, drivers,
    and suitability impact in compliance-safe language.
    """
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    
    # Convert request to inputs
    inputs = GeoRiskScanInputs(
        client_id=request.client_id,
        as_of=request.as_of,
        horizon_days=request.horizon_days,
        risk_tolerance=request.risk_tolerance,
        portfolio=request.portfolio,
    )
    
    # For now, process the first holding (frontend sends single holding per request)
    if not request.portfolio.holdings:
        raise HTTPException(status_code=400, detail="Portfolio must contain at least one holding")
    
    holding = request.portfolio.holdings[0]
    
    # Use new pipeline to calculate probabilities
    try:
        # Convert risk_tolerance to proper case
        risk_tolerance_map = {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
        }
        risk_tolerance = risk_tolerance_map.get(request.risk_tolerance.lower(), "Medium")
        
        # Run pipeline
        probabilities = run_pipeline_simple(holding, risk_tolerance)
        
        # Convert probabilities to scenarios format
        # Map: Sell -> severe, Hold -> moderate, Buy -> low
        scenarios = [
            Scenario(name="severe", p=probabilities.sell),
            Scenario(name="moderate", p=probabilities.hold),
            Scenario(name="low", p=probabilities.buy),
        ]
        
        # Determine confidence based on signal strength
        # For now, use medium confidence (can be enhanced with actual signal count)
        confidence = "medium"
        
        # Generate drivers (can be enhanced with actual theme data)
        drivers = [
            "Geopolitical risk assessment based on asset characteristics",
            "Intelligence signal analysis from global feeds",
            "Theme-based impact evaluation",
        ]
        
        # Generate suitability impact (compliance-safe)
        suitability_impact = (
            f"Geopolitical risk analysis indicates {int(probabilities.sell * 100)}% probability of severe risk, "
            f"{int(probabilities.hold * 100)}% moderate risk, and {int(probabilities.buy * 100)}% low risk scenarios. "
            "This assessment is based on current intelligence signals and asset characteristics. "
            "Consider this information alongside other suitability factors when making investment decisions."
        )
        
        geo_risk_output = GeoRiskOutput(
            scenarios=scenarios,
            confidence=confidence,
            drivers=drivers,
            suitability_impact=suitability_impact,
            limitations=[
                "Analysis based on available intelligence signals",
                "Does not account for all geopolitical factors",
                "Probabilities are estimates, not certainties",
            ],
            disclaimer="Internal decision-support only. Not financial advice.",
            citations=[],
        )
        
        # Generate scan_id and timestamp
        scan_id = f"scan_{int(datetime.now().timestamp())}_{request.client_id[:8]}"
        created_at = datetime.now().isoformat()
        
        result = GeoRiskScanResult(
            scan_id=scan_id,
            created_at=created_at,
            inputs=inputs,
            geo_risk=geo_risk_output,
            meta=GeoRiskScanMeta(
                model=model,
                used_fallback=False,
                validation=ValidationResult(passed=True, errors=[]),
            ),
        )
        
    except Exception as e:
        # Pipeline failed, fall back to LLM-based approach
        # Retrieve regulatory snippets
        query_terms = ["suitability", "risk", "documentation", "assessment"]
        snippets = retrieve_regulatory_snippets(query_terms, max_results=3)
        snippet_texts = get_snippet_texts(snippets)
        
        # Build prompt
        prompt = build_prompt(inputs, snippet_texts, strict_mode=False)
        
        used_fallback = False
        
        try:
            response_text = _call_ollama(prompt, model)
            result = _parse_llm_response(response_text, inputs, model)
            
            # If validation failed, try once more with strict mode
            if not result.meta.validation.passed:
                prompt_strict = build_prompt(inputs, snippet_texts, strict_mode=True)
                response_text_strict = _call_ollama(prompt_strict, model)
                result = _parse_llm_response(response_text_strict, inputs, model)
                
                # If still failed, use fallback
                if not result.meta.validation.passed:
                    used_fallback = True
                    result = generate_fallback(inputs)
        except Exception:
            # LLM failed, use fallback
            used_fallback = True
            result = generate_fallback(inputs)
        
        result.meta.used_fallback = used_fallback
    
    # Store in audit trail
    store = get_store()
    store.store(result)
    
    return result


@router.post("/scan-detailed")
def scan_geo_risk_detailed(request: GeoRiskScanRequest) -> DetailedPipelineResult:
    """
    Run a detailed geopolitical risk scan with full pipeline breakdown.
    
    Returns all intermediate results from each pipeline step:
    - Asset characterization details
    - Identified themes with relevance scores
    - Intelligence signals with scoring breakdown
    - Impact assessment per theme
    - Final probability calculations
    """
    # Convert risk_tolerance to proper case
    risk_tolerance_map = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
    }
    risk_tolerance = risk_tolerance_map.get(request.risk_tolerance.lower(), "Medium")
    
    # Get the holding
    if not request.portfolio.holdings:
        raise HTTPException(status_code=400, detail="Portfolio must contain at least one holding")
    
    holding = request.portfolio.holdings[0]
    
    # Run full pipeline
    pipeline_result = run_pipeline(holding, risk_tolerance, days_lookback=90)
    
    # Extract exposures
    exposures = []
    if pipeline_result.profile.is_government_exposed:
        exposures.append("Government")
    if pipeline_result.profile.is_energy_exposed:
        exposures.append("Energy")
    if pipeline_result.profile.is_financial_exposed:
        exposures.append("Financial")
    if pipeline_result.profile.is_technology_exposed:
        exposures.append("Technology")
    if pipeline_result.profile.is_infrastructure_exposed:
        exposures.append("Infrastructure")
    
    # Convert themes
    theme_details = [
        ThemeDetail(
            theme=t.theme,
            relevance_score=t.relevance_score,
            reasoning=t.reasoning,
            keywords_matched=t.keywords_matched,
        )
        for t in pipeline_result.themes
    ]
    
    # Convert signals
    signal_details = [
        IntelligenceSignalDetail(
            source=s.source,
            title=s.title,
            summary=s.summary,
            topic=s.topic,
            relevance_score=s.relevance_score,
            theme_match=s.theme_match,
            published_at=s.published_at,
            url=s.url,
            country=s.country,
            activity_level=s.activity_level,
            base_relevance=s.base_relevance,
            theme_match_score=s.theme_match_score,
            recency_score=s.recency_score,
            source_quality=s.source_quality,
            activity_level_score=s.activity_level_score,
        )
        for s in pipeline_result.signals
    ]
    
    # Convert web searches
    web_search_details = [
        WebSearchDetail(
            theme=ws.get("theme", ""),
            query=ws.get("query", ""),
            results_count=ws.get("results_count", 0),
            signals_count=ws.get("signals_count", 0),
            error=ws.get("error"),
        )
        for ws in pipeline_result.web_searches
    ]
    
    # Convert impact
    theme_impact_details = [
        ThemeImpactDetail(
            theme=ti.theme,
            impact_direction=ti.impact_direction,
            impact_magnitude=ti.impact_magnitude,
            confidence=ti.confidence,
            reasoning=ti.reasoning,
            signal_count=ti.signal_count,
            summary=ti.summary,
        )
        for ti in pipeline_result.impact.theme_impacts
    ]
    
    aggregate_impact = AggregateImpactDetail(
        overall_direction=pipeline_result.impact.overall_direction,
        overall_magnitude=pipeline_result.impact.overall_magnitude,
        confidence=pipeline_result.impact.confidence,
        theme_impacts=theme_impact_details,
        total_signals=pipeline_result.impact.total_signals,
    )
    
    # Convert probabilities
    probabilities_detail = ActionProbabilitiesDetail(
        sell=pipeline_result.probabilities.sell,
        hold=pipeline_result.probabilities.hold,
        buy=pipeline_result.probabilities.buy,
    )
    
    return DetailedPipelineResult(
        characterization_summary=pipeline_result.characterization_summary,
        asset_country=pipeline_result.profile.country,
        asset_region=pipeline_result.profile.region,
        asset_sub_region=pipeline_result.profile.sub_region,
        asset_type=pipeline_result.profile.asset_type,
        asset_class=pipeline_result.profile.asset_class,
        asset_sector=pipeline_result.profile.sector,
        is_emerging_market=pipeline_result.profile.is_emerging_market,
        is_developed_market=pipeline_result.profile.is_developed_market,
        is_global_fund=pipeline_result.profile.is_global_fund,
        exposures=exposures,
        themes=theme_details,
        top_themes=pipeline_result.top_themes,
        signals=signal_details,
        signal_count=pipeline_result.signal_count,
        web_searches=web_search_details,
        impact=aggregate_impact,
        probabilities=probabilities_detail,
        probability_summary=pipeline_result.probability_summary,
        risk_tolerance=pipeline_result.risk_tolerance,
        days_lookback=pipeline_result.days_lookback,
    )


@router.post("/scan-detailed-stream")
def scan_geo_risk_detailed_stream(request: GeoRiskScanRequest):
    """
    Run a detailed geopolitical risk scan with real-time streaming updates.

    Returns Server-Sent Events (SSE) stream with progress updates for each pipeline step:
    - characterization: Asset analysis complete
    - theme_identification: Themes identified
    - intelligence_retrieval: Intelligence signals retrieved
    - impact_assessment: Impact assessed
    - probability_calculation: Final probabilities calculated

    Each event includes step_id, step_name, status, duration_ms, and step-specific data.
    """
    # Convert risk_tolerance to proper case
    risk_tolerance_map = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
    }
    risk_tolerance = risk_tolerance_map.get(request.risk_tolerance.lower(), "Medium")

    # Get the holding
    if not request.portfolio.holdings:
        raise HTTPException(status_code=400, detail="Portfolio must contain at least one holding")

    holding = request.portfolio.holdings[0]

    # Create SSE event generator
    def generate_sse_events():
        """Generate SSE-formatted events from pipeline updates."""
        try:
            for update in run_pipeline_streaming(holding, risk_tolerance, days_lookback=90):
                # Convert update to JSON
                event_data = {
                    "step_id": update.step_id,
                    "step_name": update.step_name,
                    "status": update.status,
                    "duration_ms": update.duration_ms,
                    "data": update.data,
                    "error": update.error,
                }

                # Format as SSE: data: {json}\n\n
                yield f"data: {json.dumps(event_data)}\n\n"

        except Exception as e:
            # Send error event
            error_event = {
                "step_id": "error",
                "step_name": "Pipeline Error",
                "status": "error",
                "duration_ms": 0,
                "data": None,
                "error": str(e),
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        generate_sse_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/scans")
def list_scans(client_id: str | None = None, limit: int = 10) -> List[GeoRiskScanResult]:
    """
    List scan results.
    
    If client_id is provided, returns scans for that client only.
    Otherwise returns all scans (newest first).
    """
    store = get_store()
    
    if client_id:
        return store.list_by_client(client_id, limit=limit)
    else:
        return store.list_all(limit=limit)


@router.get("/scans/{scan_id}")
def get_scan(scan_id: str) -> GeoRiskScanResult:
    """Get a specific scan by ID."""
    store = get_store()
    result = store.get(scan_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return result
