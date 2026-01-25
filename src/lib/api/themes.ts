/** API functions for theme management. */

export interface Theme {
  id: number;
  name: string;
  display_name: string;
  keywords: string[];
  relevant_countries: string[];
  relevant_regions: string[];
  relevant_sectors: string[];
  country_match_weight: number;
  region_match_weight: number;
  sector_match_weight: number;
  exposure_bonus_weight: number;
  emerging_market_bonus: number;
  min_relevance_threshold: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ThemeCreate {
  name: string;
  display_name: string;
  keywords: string[];
  relevant_countries?: string[];
  relevant_regions?: string[];
  relevant_sectors: string[];
  country_match_weight?: number;
  region_match_weight?: number;
  sector_match_weight?: number;
  exposure_bonus_weight?: number;
  emerging_market_bonus?: number;
  min_relevance_threshold?: number;
  is_active?: boolean;
}

export interface ThemeUpdate {
  display_name?: string;
  keywords?: string[];
  relevant_countries?: string[];
  relevant_regions?: string[];
  relevant_sectors?: string[];
  country_match_weight?: number;
  region_match_weight?: number;
  sector_match_weight?: number;
  exposure_bonus_weight?: number;
  emerging_market_bonus?: number;
  min_relevance_threshold?: number;
  is_active?: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function listThemes(activeOnly: boolean = false): Promise<Theme[]> {
  const response = await fetch(`${API_BASE}/themes?active_only=${activeOnly}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch themes: ${response.statusText}`);
  }
  return response.json();
}

export async function getTheme(themeName: string): Promise<Theme> {
  const response = await fetch(`${API_BASE}/themes/${themeName}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch theme: ${response.statusText}`);
  }
  return response.json();
}

export async function createTheme(theme: ThemeCreate): Promise<Theme> {
  const response = await fetch(`${API_BASE}/themes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(theme),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to create theme: ${response.statusText}`);
  }
  return response.json();
}

export async function updateTheme(themeName: string, theme: ThemeUpdate): Promise<Theme> {
  const response = await fetch(`${API_BASE}/themes/${themeName}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(theme),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to update theme: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteTheme(themeName: string): Promise<void> {
  const response = await fetch(`${API_BASE}/themes/${themeName}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to delete theme: ${response.statusText}`);
  }
}
