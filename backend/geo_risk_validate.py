"""Validator for geopolitical risk scan results."""
from typing import List
from .schemas.geo_risk import GeoRiskScanResult, ValidationResult


def validate_result(result: GeoRiskScanResult) -> ValidationResult:
    """
    Validate a scan result.
    
    Checks:
    - Required fields present
    - Probabilities sum to 1.00 ± 0.01
    - Scenarios are exactly 3 (low, moderate, severe)
    - All probabilities are between 0 and 1
    """
    errors: List[str] = []
    
    # Check scenarios
    if len(result.geo_risk.scenarios) != 3:
        errors.append(f"Expected exactly 3 scenarios, got {len(result.geo_risk.scenarios)}")
    
    # Check scenario names
    scenario_names = {s.name for s in result.geo_risk.scenarios}
    expected_names = {"low", "moderate", "severe"}
    if scenario_names != expected_names:
        errors.append(f"Expected scenario names {expected_names}, got {scenario_names}")
    
    # Check probabilities sum
    total_p = sum(s.p for s in result.geo_risk.scenarios)
    if abs(total_p - 1.0) > 0.01:
        errors.append(f"Probabilities sum to {total_p:.4f}, expected 1.00 ± 0.01")
    
    # Check individual probabilities
    for scenario in result.geo_risk.scenarios:
        if scenario.p < 0.0 or scenario.p > 1.0:
            errors.append(f"Scenario {scenario.name} has invalid probability {scenario.p}")
    
    # Check required fields
    if not result.geo_risk.drivers:
        errors.append("Drivers list is empty")
    
    if not result.geo_risk.suitability_impact or len(result.geo_risk.suitability_impact) < 50:
        errors.append("Suitability impact must be at least 50 characters")
    
    if not result.geo_risk.limitations:
        errors.append("Limitations list is empty")
    
    if not result.geo_risk.disclaimer:
        errors.append("Disclaimer is missing")
    
    # Check confidence
    if result.geo_risk.confidence not in ["low", "medium", "high"]:
        errors.append(f"Invalid confidence value: {result.geo_risk.confidence}")
    
    passed = len(errors) == 0
    return ValidationResult(passed=passed, errors=errors)
