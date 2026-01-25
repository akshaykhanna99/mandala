"""Probability calculation - converts impact assessments to Sell/Hold/Buy probabilities."""
from dataclasses import dataclass
from typing import Literal
from .geo_risk_impact import AggregateImpact, ThemeImpact
from .geo_risk_characterization import AssetProfile


@dataclass
class ActionProbabilities:
    """Probability scores for Sell/Hold/Buy actions."""
    sell: float  # 0.0 to 1.0
    hold: float  # 0.0 to 1.0
    buy: float  # 0.0 to 1.0
    
    def normalize(self):
        """Ensure probabilities sum to 1.0."""
        total = self.sell + self.hold + self.buy
        if total > 0:
            self.sell = self.sell / total
            self.hold = self.hold / total
            self.buy = self.buy / total
        else:
            # Default to neutral if no signals
            self.sell = 0.2
            self.hold = 0.6
            self.buy = 0.2


def calculate_probabilities(
    profile: AssetProfile,
    impact: AggregateImpact,
    risk_tolerance: Literal["Low", "Medium", "High"] = "Medium",
) -> ActionProbabilities:
    """
    Calculate Sell/Hold/Buy probabilities from impact assessment.
    
    Args:
        profile: Asset profile
        impact: Aggregate impact assessment
        risk_tolerance: Client risk tolerance (affects sensitivity to negative signals)
    
    Returns:
        ActionProbabilities with normalized probabilities
    """
    probs = ActionProbabilities(sell=0.0, hold=0.0, buy=0.0)
    
    # Base probabilities from overall impact direction
    if impact.overall_direction == "negative":
        # Negative impact increases sell probability
        probs.sell = 0.4 + (impact.overall_magnitude * 0.4)
        probs.hold = 0.4 - (impact.overall_magnitude * 0.2)
        probs.buy = 0.2 - (impact.overall_magnitude * 0.2)
        
    elif impact.overall_direction == "positive":
        # Positive impact increases buy probability
        probs.sell = 0.2 - (impact.overall_magnitude * 0.1)
        probs.hold = 0.4 - (impact.overall_magnitude * 0.2)
        probs.buy = 0.4 + (impact.overall_magnitude * 0.3)
        
    else:  # neutral
        # Neutral defaults to hold
        probs.sell = 0.2
        probs.hold = 0.6
        probs.buy = 0.2
    
    # Adjust based on theme-specific impacts
    for theme_impact in impact.theme_impacts:
        if theme_impact.impact_direction == "negative":
            weight = theme_impact.impact_magnitude * theme_impact.confidence * 0.3
            probs.sell += weight
            probs.hold -= weight * 0.5
            probs.buy -= weight * 0.5
            
        elif theme_impact.impact_direction == "positive":
            weight = theme_impact.impact_magnitude * theme_impact.confidence * 0.3
            probs.buy += weight
            probs.hold -= weight * 0.5
            probs.sell -= weight * 0.5
    
    # Adjust for risk tolerance
    if risk_tolerance == "Low":
        # Low risk tolerance = more sensitive to negative signals
        if impact.overall_direction == "negative":
            probs.sell *= 1.3
            probs.hold *= 0.9
            probs.buy *= 0.7
    elif risk_tolerance == "High":
        # High risk tolerance = less sensitive to negative signals
        if impact.overall_direction == "negative":
            probs.sell *= 0.8
            probs.hold *= 1.1
            probs.buy *= 1.0
    
    # Ensure non-negative
    probs.sell = max(0.0, probs.sell)
    probs.hold = max(0.0, probs.hold)
    probs.buy = max(0.0, probs.buy)
    
    # Normalize to sum to 1.0
    probs.normalize()
    
    return probs


def get_probability_summary(probs: ActionProbabilities) -> str:
    """Generate human-readable summary of probabilities."""
    sell_pct = int(probs.sell * 100)
    hold_pct = int(probs.hold * 100)
    buy_pct = int(probs.buy * 100)
    
    if probs.sell > 0.5:
        return f"Strong Sell signal ({sell_pct}% probability)"
    elif probs.buy > 0.5:
        return f"Strong Buy signal ({buy_pct}% probability)"
    elif probs.hold > 0.5:
        return f"Hold recommendation ({hold_pct}% probability)"
    else:
        return f"Mixed: Sell {sell_pct}% | Hold {hold_pct}% | Buy {buy_pct}%"
