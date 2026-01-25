/** API functions for GP scan management. */

import type { DetailedPipelineResult } from "@/types/geoRisk";

export interface GPScan {
  id: number;
  asset_id: number;
  risk_tolerance: string;
  days_lookback: number;
  scan_date: string;
  negative_probability: number;
  neutral_probability: number;
  positive_probability: number;
  overall_direction: string;
  overall_magnitude: number;
  confidence: number;
  signal_count: number;
  top_themes: string[];
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: number;
  name: string;
  ticker?: string;
  isin?: string;
  country?: string;
  region: string;
  sub_region?: string;
  asset_type: string;
  asset_class: string;
  sector: string;
  is_emerging_market: boolean;
  is_developed_market: boolean;
  is_global_fund: boolean;
  exposures: string[];
  created_at: string;
  updated_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function saveGPScan(
  pipelineResult: DetailedPipelineResult & { name?: string; ticker?: string; isin?: string },
  riskTolerance: string,
  daysLookback: number,
  assetId?: number
): Promise<GPScan> {
  const response = await fetch(`${API_BASE}/gp-scans`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      asset_id: assetId,
      risk_tolerance: riskTolerance,
      days_lookback: daysLookback,
      pipeline_result: pipelineResult,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to save GP scan: ${response.statusText}`);
  }
  
  return response.json();
}

export async function listGPScans(assetId?: number, limit: number = 50): Promise<GPScan[]> {
  const params = new URLSearchParams();
  if (assetId) params.append("asset_id", assetId.toString());
  params.append("limit", limit.toString());
  
  const response = await fetch(`${API_BASE}/gp-scans?${params}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch GP scans: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getGPScan(scanId: number): Promise<GPScan> {
  const response = await fetch(`${API_BASE}/gp-scans/${scanId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch GP scan: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getGPScanFull(scanId: number): Promise<DetailedPipelineResult> {
  const response = await fetch(`${API_BASE}/gp-scans/${scanId}/full`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch GP scan full result: ${response.statusText}`);
  }
  
  return response.json();
}

export async function listAssets(limit: number = 100): Promise<Asset[]> {
  const response = await fetch(`${API_BASE}/gp-scans/assets?limit=${limit}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch assets: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getAsset(assetId: number): Promise<Asset> {
  const response = await fetch(`${API_BASE}/gp-scans/assets/${assetId}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch asset: ${response.statusText}`);
  }
  
  return response.json();
}
