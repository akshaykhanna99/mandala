"""Deterministic fallback generator for geopolitical risk scans."""
import hashlib
from datetime import datetime
from typing import List
from .schemas.geo_risk import (
    GeoRiskScanInputs,
    GeoRiskScanResult,
    GeoRiskOutput,
    Scenario,
    GeoRiskScanMeta,
    ValidationResult,
)


def generate_fallback(inputs: GeoRiskScanInputs) -> GeoRiskScanResult:
    """
    Generate a deterministic fallback result when LLM fails.
    
    Uses a seed based on region strings + as_of date to produce
    consistent outputs for the same inputs.
    """
    # Create deterministic seed from inputs
    seed_str = f"{inputs.as_of}_{'_'.join([h.region for h in inputs.portfolio.holdings])}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    
    # Base probabilities (will be normalized)
    base_low = 0.4 + (seed % 20) / 100
    base_moderate = 0.35 + ((seed * 2) % 15) / 100
    base_severe = 0.15 + ((seed * 3) % 10) / 100
    
    # Adjust based on decision context (inferred from risk tolerance)
    low = base_low
    moderate = base_moderate
    severe = base_severe
    
    if inputs.risk_tolerance == "low":
        # More conservative for low risk tolerance
        severe += 0.08
        low -= 0.04
        moderate -= 0.04
    elif inputs.risk_tolerance == "high":
        # Less conservative for high risk tolerance
        severe -= 0.05
        low += 0.03
        moderate += 0.02
    
    # Normalize to sum to 1.0
    total = low + moderate + severe
    low = low / total
    moderate = moderate / total
    severe = severe / total
    
    # Round and ensure exact sum of 1.0
    low = round(low, 2)
    moderate = round(moderate, 2)
    severe = round(1.0 - low - moderate, 2)
    
    # Determine confidence based on seed
    confidence_seed = seed % 3
    confidence_map = {0: "low", 1: "medium", 2: "high"}
    confidence = confidence_map[confidence_seed]
    
    # Generate generic drivers (NO claims about real events)
    all_drivers = [
        "Sanctions risk",
        "Trade disruption potential",
        "Political instability indicators",
        "Energy supply volatility",
        "Currency volatility",
        "Regulatory changes",
        "Regional conflict spillover risk",
        "Infrastructure vulnerability",
    ]
    driver_indices = [
        (seed % 8),
        ((seed * 2) % 8),
        ((seed * 3) % 8),
        ((seed * 5) % 8),
    ]
    drivers = [all_drivers[i] for i in driver_indices if i < len(all_drivers)][:4]
    
    # Generate suitability impact (non-directive, compliance-safe)
    if inputs.risk_tolerance == "low" and severe > 0.25:
        suitability_impact = (
            "Elevated downside uncertainty may warrant additional consideration "
            "given the client's stated risk tolerance. The probability distribution "
            "suggests meaningful tail risk that could impact portfolio stability. "
            "Ongoing monitoring and periodic reassessment may be appropriate."
        )
    elif inputs.risk_tolerance == "medium" and severe > 0.2:
        suitability_impact = (
            "The scenario analysis indicates moderate-to-elevated risk factors that "
            "may require ongoing monitoring. Current probabilities suggest a balanced "
            "assessment of potential outcomes. Consideration of risk mitigation "
            "strategies may be warranted."
        )
    else:
        suitability_impact = (
            "The scenario analysis indicates a range of potential outcomes. "
            "Current probabilities suggest a balanced risk profile. Regular review "
            "of geopolitical developments may support ongoing suitability assessments."
        )
    
    limitations = [
        "Analysis based on available data as of specified date",
        "Probabilistic scenarios are not predictions of future events",
        "Actual outcomes may differ from modeled scenarios",
        "Does not account for all possible risk factors",
    ]
    
    # Generate scan_id and timestamp
    scan_id = f"fallback_{seed}_{int(datetime.now().timestamp())}"
    created_at = datetime.now().isoformat()
    
    return GeoRiskScanResult(
        scan_id=scan_id,
        created_at=created_at,
        inputs=inputs,
        geo_risk=GeoRiskOutput(
            scenarios=[
                Scenario(name="low", p=low),
                Scenario(name="moderate", p=moderate),
                Scenario(name="severe", p=severe),
            ],
            confidence=confidence,
            drivers=drivers,
            suitability_impact=suitability_impact,
            limitations=limitations,
            disclaimer="Internal decision-support only. Not financial advice.",
            citations=[],
        ),
        meta=GeoRiskScanMeta(
            model="fallback",
            used_fallback=True,
            validation=ValidationResult(passed=True, errors=[]),
        ),
    )
