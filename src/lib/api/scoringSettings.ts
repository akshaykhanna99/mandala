/** API functions for scoring settings management. */

export interface ScoringSettings {
  id: number;
  name: string;
  description?: string;
  weight_base_relevance: number;
  weight_theme_match: number;
  weight_recency: number;
  weight_source_quality: number;
  weight_activity_level: number;
  recency_decay_constant: number;
  score_country_exact_match: number;
  score_country_partial_match: number;
  score_region_match: number;
  score_sector_match: number;
  activity_level_scores: Record<string, number>;
  source_quality_scores: Record<string, number>;
  semantic_threshold: number;
  relevance_threshold_low: number;
  relevance_threshold_high: number;
  theme_relevance_threshold_web: number;
  days_lookback_default: number;
  max_signals_default: number;
  max_events_per_snapshot: number;
  use_semantic_filtering: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScoringSettingsUpdate {
  description?: string;
  weight_base_relevance?: number;
  weight_theme_match?: number;
  weight_recency?: number;
  weight_source_quality?: number;
  weight_activity_level?: number;
  recency_decay_constant?: number;
  score_country_exact_match?: number;
  score_country_partial_match?: number;
  score_region_match?: number;
  score_sector_match?: number;
  activity_level_scores?: Record<string, number>;
  source_quality_scores?: Record<string, number>;
  semantic_threshold?: number;
  relevance_threshold_low?: number;
  relevance_threshold_high?: number;
  theme_relevance_threshold_web?: number;
  days_lookback_default?: number;
  max_signals_default?: number;
  max_events_per_snapshot?: number;
  use_semantic_filtering?: boolean;
  is_active?: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function getActiveScoringSettings(): Promise<ScoringSettings> {
  const response = await fetch(`${API_BASE}/scoring-settings/active/default`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch scoring settings: ${response.statusText}`);
  }
  return response.json();
}

export async function getScoringSettings(name: string): Promise<ScoringSettings> {
  const response = await fetch(`${API_BASE}/scoring-settings/${name}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch scoring settings: ${response.statusText}`);
  }
  return response.json();
}

export async function listScoringSettings(activeOnly: boolean = false): Promise<ScoringSettings[]> {
  const response = await fetch(`${API_BASE}/scoring-settings?active_only=${activeOnly}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch scoring settings: ${response.statusText}`);
  }
  return response.json();
}

export async function updateScoringSettings(
  name: string,
  settings: ScoringSettingsUpdate
): Promise<ScoringSettings> {
  const response = await fetch(`${API_BASE}/scoring-settings/${name}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to update scoring settings: ${response.statusText}`);
  }
  return response.json();
}
