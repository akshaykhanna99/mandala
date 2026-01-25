"use client";

import { useState } from "react";

type DecisionType = "Increase exposure" | "Decrease exposure" | "Hold / No change";
type RiskTolerance = "Low" | "Medium" | "High";

type GeoRiskResponse = {
  geo_risk: {
    as_of: string;
    horizon_days: number;
    scenarios: Array<{ name: string; p: number }>;
    confidence: "low" | "medium" | "high";
    drivers: string[];
    suitability_impact: string;
    disclaimer: string;
  };
};

// Deterministic mock generator (seeded by region)
function generateMockRiskResponse(
  decisionType: DecisionType,
  asset: string,
  region: string,
  horizonDays: number,
  riskTolerance: RiskTolerance,
  asOfDate: string,
): GeoRiskResponse {
  // Simple hash from region string for deterministic but varied outputs
  const seed = region.toLowerCase().split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  
  // Base probabilities (will be normalized)
  const baseLow = 0.4 + (seed % 20) / 100;
  const baseModerate = 0.35 + ((seed * 2) % 15) / 100;
  const baseSevere = 0.15 + ((seed * 3) % 10) / 100;
  
  // Adjust based on decision type
  let low = baseLow;
  let moderate = baseModerate;
  let severe = baseSevere;
  
  if (decisionType === "Increase exposure") {
    // More conservative (higher severe probability)
    severe += 0.1;
    low -= 0.05;
    moderate -= 0.05;
  } else if (decisionType === "Decrease exposure") {
    // Less conservative
    severe -= 0.05;
    low += 0.03;
    moderate += 0.02;
  }
  
  // Normalize to sum to 1.0
  const sum = low + moderate + severe;
  low = low / sum;
  moderate = moderate / sum;
  severe = severe / sum;
  
  // Round to 2 decimals and ensure exact sum of 1.0
  low = Math.round(low * 100) / 100;
  moderate = Math.round(moderate * 100) / 100;
  // Calculate severe as remainder to ensure exact 1.0 sum
  severe = Math.round((1.0 - low - moderate) * 100) / 100;
  
  // Determine confidence
  let confidence: "low" | "medium" | "high" = "medium";
  if (decisionType === "Increase exposure") {
    confidence = "low";
  } else if (region && region.trim().length > 0) {
    confidence = seed % 3 === 0 ? "high" : "medium";
  } else {
    confidence = "low";
  }
  
  // Generate drivers (deterministic based on seed)
  const allDrivers = [
    "Sanctions risk",
    "Trade disruption",
    "Political instability",
    "Energy supply volatility",
    "Currency volatility",
    "Regulatory changes",
    "Regional conflict spillover",
    "Infrastructure vulnerability",
  ];
  const driverIndices = [
    (seed % 8),
    ((seed * 2) % 8),
    ((seed * 3) % 8),
  ].map(i => (i === 0 ? 1 : i)); // Avoid duplicates
  const drivers = [...new Set(driverIndices.map(i => allDrivers[i]))].slice(0, 4);
  
  // Generate suitability impact (compliance-friendly, non-directive)
  let suitabilityImpact = "";
  if (riskTolerance === "Low" && severe > 0.25) {
    suitabilityImpact = `Elevated downside uncertainty may warrant additional consideration given the client's stated risk tolerance. The probability distribution suggests meaningful tail risk that could impact portfolio stability.`;
  } else if (riskTolerance === "Medium" && severe > 0.2) {
    suitabilityImpact = `The scenario analysis indicates moderate-to-elevated risk factors that may require ongoing monitoring. Current probabilities suggest a balanced assessment of potential outcomes.`;
  } else if (riskTolerance === "High") {
    suitabilityImpact = `The risk profile appears aligned with higher risk tolerance parameters, though periodic review of geopolitical developments is recommended.`;
  } else {
    suitabilityImpact = `The current risk assessment suggests manageable uncertainty levels, though ongoing monitoring of regional developments remains prudent.`;
  }
  
  return {
    geo_risk: {
      as_of: asOfDate,
      horizon_days: horizonDays,
      scenarios: [
        { name: "low", p: low },
        { name: "moderate", p: moderate },
        { name: "severe", p: severe },
      ],
      confidence,
      drivers,
      suitability_impact: suitabilityImpact,
      disclaimer: "Decision-support only; not financial advice.",
    },
  };
}

type RiskScoreDemoProps = {
  onClose: () => void;
};

export default function RiskScoreDemo({ onClose }: RiskScoreDemoProps) {
  const [decisionType, setDecisionType] = useState<DecisionType>("Increase exposure");
  const [asset, setAsset] = useState("EM equities - Turkey");
  const [region, setRegion] = useState("Turkey");
  const [horizonDays, setHorizonDays] = useState(365);
  const [riskTolerance, setRiskTolerance] = useState<RiskTolerance>("Medium");
  const [asOfDate, setAsOfDate] = useState(
    new Date().toISOString().split("T")[0],
  );
  const [result, setResult] = useState<GeoRiskResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setIsLoading(true);
    setError(null);
    
    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 500));
    
    try {
      const response = generateMockRiskResponse(
        decisionType,
        asset,
        region,
        horizonDays,
        riskTolerance,
        asOfDate,
      );
      
      // Validate probabilities sum to 1.0
      const sum = response.geo_risk.scenarios.reduce((acc, s) => acc + s.p, 0);
      if (Math.abs(sum - 1.0) > 0.01) {
        throw new Error(`Probabilities sum to ${sum.toFixed(2)}, expected 1.00`);
      }
      
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate risk assessment");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadExample = () => {
    setDecisionType("Increase exposure");
    setAsset("EM equities - Turkey");
    setRegion("Turkey");
    setHorizonDays(365);
    setRiskTolerance("Medium");
    setAsOfDate(new Date().toISOString().split("T")[0]);
    setResult(null);
    setError(null);
  };

  return (
    <div className="pointer-events-auto absolute right-8 top-24 z-20 h-[calc(100vh-120px)] w-[600px] overflow-hidden rounded-[28px] border border-white/10 bg-black/40 shadow-[0_24px_80px_rgba(10,10,10,0.35)] backdrop-blur">
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="border-b border-white/10 px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">
                Geopolitical Risk Score
              </p>
              <p className="mt-1 text-sm text-white/80">Saturn Track 1 Demo</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full border border-white/15 text-white/70 transition hover:text-white"
              aria-label="Close risk score demo"
              title="Close risk score demo"
            >
              <svg
                viewBox="0 0 24 24"
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M6 6l12 12" />
                <path d="M18 6l-12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {/* How to demo */}
          <div className="mb-6 rounded-2xl border border-white/10 bg-black/30 p-4">
            <p className="mb-2 text-[10px] uppercase tracking-[0.2em] text-white/50">
              How to demo
            </p>
            <ul className="space-y-1.5 text-xs text-white/60">
              <li>• This is not a recommendation — outputs probabilities and rationale.</li>
              <li>• Designed to plug into suitability reports and ongoing reviews.</li>
              <li>• Auditable drivers + confidence.</li>
            </ul>
          </div>

          {/* Form */}
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-[10px] uppercase tracking-[0.2em] text-white/60">
                Decision Type
              </label>
              <select
                value={decisionType}
                onChange={(e) => setDecisionType(e.target.value as DecisionType)}
                className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2 text-sm text-white/80 focus:border-white/20 focus:outline-none"
              >
                <option>Increase exposure</option>
                <option>Decrease exposure</option>
                <option>Hold / No change</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-[10px] uppercase tracking-[0.2em] text-white/60">
                Asset / Exposure
              </label>
              <input
                type="text"
                value={asset}
                onChange={(e) => setAsset(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2 text-sm text-white/80 placeholder:text-white/40 focus:border-white/20 focus:outline-none"
                placeholder="EM equities - Turkey"
              />
            </div>

            <div>
              <label className="mb-2 block text-[10px] uppercase tracking-[0.2em] text-white/60">
                Region
              </label>
              <input
                type="text"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2 text-sm text-white/80 placeholder:text-white/40 focus:border-white/20 focus:outline-none"
                placeholder="Turkey"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-2 block text-[10px] uppercase tracking-[0.2em] text-white/60">
                  Horizon (days)
                </label>
                <input
                  type="number"
                  value={horizonDays}
                  onChange={(e) => setHorizonDays(Number(e.target.value))}
                  min="1"
                  className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2 text-sm text-white/80 focus:border-white/20 focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-2 block text-[10px] uppercase tracking-[0.2em] text-white/60">
                  Risk Tolerance
                </label>
                <select
                  value={riskTolerance}
                  onChange={(e) => setRiskTolerance(e.target.value as RiskTolerance)}
                  className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2 text-sm text-white/80 focus:border-white/20 focus:outline-none"
                >
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                </select>
              </div>
            </div>

            <div>
              <label className="mb-2 block text-[10px] uppercase tracking-[0.2em] text-white/60">
                As-of date
              </label>
              <input
                type="date"
                value={asOfDate}
                onChange={(e) => setAsOfDate(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-2 text-sm text-white/80 focus:border-white/20 focus:outline-none"
              />
            </div>
          </div>

          {/* Buttons */}
          <div className="mt-6 flex gap-3">
            <button
              onClick={handleGenerate}
              disabled={isLoading}
              className="flex-1 rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isLoading ? "Generating..." : "Generate Risk Output"}
            </button>
            <button
              onClick={handleLoadExample}
              disabled={isLoading}
              className="rounded-xl border border-white/10 bg-black/30 px-4 py-2.5 text-sm font-medium text-white/70 transition hover:bg-black/40 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Load Example
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <p className="text-xs text-red-400">Error: {error}</p>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="mt-6 space-y-4">
              {/* Scenario Probabilities */}
              <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                <h3 className="mb-3 text-[10px] uppercase tracking-[0.2em] text-white/60">
                  Scenario Probabilities
                </h3>
                <div className="space-y-3">
                  {result.geo_risk.scenarios.map((scenario) => (
                    <div key={scenario.name} className="flex items-center gap-3">
                      <div className="w-24 text-xs font-medium capitalize text-white/80">
                        {scenario.name}:
                      </div>
                      <div className="flex-1">
                        <div className="h-1.5 overflow-hidden rounded-full bg-black/50">
                          <div
                            className="h-full bg-white/30 transition-all"
                            style={{ width: `${scenario.p * 100}%` }}
                          />
                        </div>
                      </div>
                      <div className="w-12 text-right text-xs font-semibold text-white">
                        {(scenario.p * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Confidence & Drivers */}
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <h3 className="mb-2 text-[10px] uppercase tracking-[0.2em] text-white/60">
                    Confidence
                  </h3>
                  <span className="inline-block rounded-full bg-white/10 px-3 py-1 text-xs font-medium capitalize text-white/80">
                    {result.geo_risk.confidence}
                  </span>
                </div>

                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <h3 className="mb-2 text-[10px] uppercase tracking-[0.2em] text-white/60">
                    Key Drivers
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {result.geo_risk.drivers.slice(0, 2).map((driver, idx) => (
                      <span
                        key={idx}
                        className="rounded-lg border border-white/10 bg-black/40 px-2 py-1 text-[10px] text-white/70"
                      >
                        {driver}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* More Drivers */}
              {result.geo_risk.drivers.length > 2 && (
                <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                  <div className="flex flex-wrap gap-1.5">
                    {result.geo_risk.drivers.slice(2).map((driver, idx) => (
                      <span
                        key={idx}
                        className="rounded-lg border border-white/10 bg-black/40 px-2 py-1 text-[10px] text-white/70"
                      >
                        {driver}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Suitability Impact */}
              <div className="rounded-2xl border border-white/10 bg-black/30 p-4">
                <h3 className="mb-2 text-[10px] uppercase tracking-[0.2em] text-white/60">
                  Suitability Impact
                </h3>
                <p className="text-xs leading-relaxed text-white/70">
                  {result.geo_risk.suitability_impact}
                </p>
              </div>

              {/* Disclaimer */}
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
                <p className="text-[10px] text-amber-400">
                  <strong>Disclaimer:</strong> {result.geo_risk.disclaimer}
                </p>
              </div>

              {/* Raw JSON */}
              <details className="rounded-2xl border border-white/10 bg-black/50 p-4">
                <summary className="cursor-pointer text-[10px] uppercase tracking-[0.2em] text-white/60">
                  Raw JSON Response
                </summary>
                <pre className="mt-3 overflow-x-auto text-[10px] text-white/50">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
