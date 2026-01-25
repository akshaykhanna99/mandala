/** TypeScript types for Geopolitical Health Scan - mirrors backend schema */

export type RiskTolerance = "low" | "medium" | "high";
export type Confidence = "low" | "medium" | "high";
export type ScenarioName = "low" | "moderate" | "severe";

export type AssetClass = 
  | "Equities"
  | "Fixed Income"
  | "Alternatives"
  | "Cash"
  | "Commodities"
  | "Real Estate"
  | "Private Equity";

export interface Holding {
  id: string;
  name: string;
  ticker?: string;
  isin?: string;
  country?: string;
  class: AssetClass;
  sector: string;
  region: string;
  sub_region?: string;
  quantity?: number; // Shares/units held
  value: number; // Current market value
  cost_basis?: number; // Original investment amount
  allocation_pct: number; // % of portfolio
  allocation_class_pct?: number; // % of asset class
  pnl_to_date: number; // Profit/Loss to date
  pnl_pct: number; // Return % since entry
  ytd_return?: number; // Year-to-date return %
  last_price?: number; // Current market price per unit
  last_valuation_date?: string; // YYYY-MM-DD
  entry_date?: string; // YYYY-MM-DD
  currency: string;
  beta?: number; // Market correlation (for equities)
  duration?: number; // Interest rate sensitivity (for bonds)
  credit_rating?: string; // Credit quality (for bonds)
  gp_score?: {
    sell: number; // Probability (0-1)
    hold: number; // Probability (0-1)
    buy: number; // Probability (0-1)
  };
}

export interface Portfolio {
  total_value: number;
  holdings: Holding[];
}

export interface GeoRiskScanInputs {
  client_id: string;
  as_of: string; // YYYY-MM-DD
  horizon_days: number;
  risk_tolerance: RiskTolerance;
  portfolio: Portfolio;
}

export interface Scenario {
  name: ScenarioName;
  p: number; // 0-1
}

export interface Citation {
  doc_id: string;
  snippet_id: string;
  section: string;
}

export interface GeoRiskOutput {
  scenarios: Scenario[];
  confidence: Confidence;
  drivers: string[];
  suitability_impact: string;
  limitations: string[];
  disclaimer: string;
  citations: Citation[];
}

export interface ValidationResult {
  passed: boolean;
  errors: string[];
}

export interface GeoRiskScanMeta {
  model: string;
  used_fallback: boolean;
  validation: ValidationResult;
}

export interface GeoRiskScanResult {
  scan_id: string;
  created_at: string; // ISO8601
  inputs: GeoRiskScanInputs;
  geo_risk: GeoRiskOutput;
  meta: GeoRiskScanMeta;
}

export interface GeoRiskScanRequest {
  client_id: string;
  as_of: string; // YYYY-MM-DD
  horizon_days: number;
  risk_tolerance: RiskTolerance;
  portfolio: Portfolio;
}

// Detailed pipeline result types
export interface ThemeDetail {
  theme: string;
  relevance_score: number;
  reasoning: string;
  keywords_matched: string[];
}

export interface IntelligenceSignalDetail {
  source: string;
  title: string;
  summary: string;
  topic: string;
  relevance_score: number;
  theme_match: string | null;
  published_at: string;
  url?: string | null;
  country?: string | null;
  activity_level?: string | null;
  base_relevance: number;
  theme_match_score: number;
  recency_score: number;
  source_quality: number;
  activity_level_score: number;
}

export interface ThemeImpactDetail {
  theme: string;
  impact_direction: string;
  impact_magnitude: number;
  confidence: number;
  reasoning: string;
  signal_count: number;
  summary?: string;
}

export interface AggregateImpactDetail {
  overall_direction: string;
  overall_magnitude: number;
  confidence: number;
  theme_impacts: ThemeImpactDetail[];
  total_signals: number;
}

export interface ActionProbabilitiesDetail {
  sell: number;
  hold: number;
  buy: number;
}

export interface WebSearchDetail {
  theme: string;
  query: string;
  results_count: number;
  signals_count: number;
  error?: string | null;
}

export interface DetailedPipelineResult {
  characterization_summary: string;
  asset_country: string | null;
  asset_region: string;
  asset_sub_region: string | null;
  asset_type: string;
  asset_class: string;
  asset_sector: string;
  is_emerging_market: boolean;
  is_developed_market: boolean;
  is_global_fund: boolean;
  exposures: string[];
  themes: ThemeDetail[];
  top_themes: string[];
  signals: IntelligenceSignalDetail[];
  signal_count: number;
  web_searches: WebSearchDetail[];
  impact: AggregateImpactDetail;
  probabilities: ActionProbabilitiesDetail;
  probability_summary: string;
  risk_tolerance: string;
  days_lookback: number;
}
