/** API helper for Asset Search */

export interface AssetSearchRequest {
  query: string;
}

export interface AssetSearchResponse {
  name: string;
  ticker?: string;
  isin?: string;
  country?: string;
  region?: string;
  sub_region?: string;
  sector?: string;
  asset_class?: string;
  description?: string;
  confidence: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://localhost:8000";

export async function searchAsset(query: string): Promise<AssetSearchResponse> {
  try {
    const response = await fetch(`${API_BASE}/asset-search/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Asset search failed: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    return data as AssetSearchResponse;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to search for asset");
  }
}
