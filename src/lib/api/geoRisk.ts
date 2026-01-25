/** API helper for Geopolitical Health Scan */

import type {
  GeoRiskScanRequest,
  GeoRiskScanResult,
  DetailedPipelineResult,
} from "@/types/geoRisk";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://localhost:8000";

export async function runGeoRiskScan(
  payload: GeoRiskScanRequest,
): Promise<GeoRiskScanResult> {
  try {
    const response = await fetch(`${API_BASE}/geo-risk/scan`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Scan failed: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    return data as GeoRiskScanResult;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to run geopolitical risk scan");
  }
}

export async function getScanHistory(
  clientId?: string,
  limit: number = 10,
): Promise<GeoRiskScanResult[]> {
  try {
    const url = new URL(`${API_BASE}/geo-risk/scans`);
    if (clientId) {
      url.searchParams.set("client_id", clientId);
    }
    url.searchParams.set("limit", limit.toString());

    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`Failed to fetch scan history: ${response.status}`);
    }

    const data = await response.json();
    return data as GeoRiskScanResult[];
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to fetch scan history");
  }
}

export async function getScan(scanId: string): Promise<GeoRiskScanResult> {
  try {
    const response = await fetch(`${API_BASE}/geo-risk/scans/${scanId}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch scan: ${response.status}`);
    }

    const data = await response.json();
    return data as GeoRiskScanResult;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to fetch scan");
  }
}

export async function runGeoRiskScanDetailed(
  payload: GeoRiskScanRequest,
): Promise<DetailedPipelineResult> {
  try {
    const response = await fetch(`${API_BASE}/geo-risk/scan-detailed`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Detailed scan failed: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    return data as DetailedPipelineResult;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Failed to run detailed geopolitical risk scan");
  }
}

export interface PipelineStepUpdate {
  step_id: string;
  step_name: string;
  status: "pending" | "running" | "completed" | "error";
  duration_ms: number;
  data: any;
  error?: string;
}

export async function runGeoRiskScanDetailedStreaming(
  payload: GeoRiskScanRequest,
  onStepUpdate: (update: PipelineStepUpdate) => void,
  onComplete: (finalData: DetailedPipelineResult) => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/geo-risk/scan-detailed-stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Streaming scan failed: ${response.status} ${errorText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Failed to get response reader");
    }

    const decoder = new TextDecoder();
    let buffer = "";
    let allStepData: Record<string, any> = {};

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        break;
      }

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE events (ending with \n\n)
      const events = buffer.split("\n\n");
      buffer = events.pop() || ""; // Keep incomplete event in buffer

      for (const event of events) {
        if (!event.trim()) continue;

        // Parse SSE event (format: data: {json})
        const dataMatch = event.match(/^data: (.+)$/m);
        if (dataMatch) {
          try {
            const update: PipelineStepUpdate = JSON.parse(dataMatch[1]);

            // Store step data
            if (update.data) {
              allStepData[update.step_id] = update.data;
            }

            // Call update callback
            onStepUpdate(update);

            // If error, stop processing
            if (update.status === "error") {
              throw new Error(update.error || "Pipeline error");
            }

            // If final step (impact_assessment), assemble complete result
            if (update.step_id === "impact_assessment" && update.status === "completed") {
              // Assemble DetailedPipelineResult from all step data
              const characterizationData = allStepData["characterization"];
              const themeData = allStepData["theme_identification"];
              const intelligenceData = allStepData["intelligence_retrieval"];
              const impactData = allStepData["impact_assessment"];

              // Map probabilities from negative/neutral/positive back to sell/hold/buy for compatibility
              const probData = impactData?.probabilities || { negative: 0, neutral: 0, positive: 0 };
              const mappedProbabilities = {
                sell: probData.negative || 0,
                hold: probData.neutral || 0,
                buy: probData.positive || 0,
              };

              const finalResult: DetailedPipelineResult = {
                characterization_summary: characterizationData?.characterization_summary || "",
                asset_country: characterizationData?.asset_country || "",
                asset_region: characterizationData?.asset_region || "",
                asset_sub_region: characterizationData?.asset_sub_region || "",
                asset_type: characterizationData?.asset_type || "",
                asset_class: characterizationData?.asset_class || "",
                asset_sector: characterizationData?.asset_sector || "",
                is_emerging_market: characterizationData?.is_emerging_market || false,
                is_developed_market: characterizationData?.is_developed_market || false,
                is_global_fund: characterizationData?.is_global_fund || false,
                exposures: characterizationData?.exposures || [],
                themes: themeData?.themes || [],
                top_themes: themeData?.top_themes || [],
                signals: intelligenceData?.signals || [],
                signal_count: intelligenceData?.signal_count || 0,
                web_searches: intelligenceData?.web_searches || [],
                impact: impactData?.impact || {},
                probabilities: mappedProbabilities,
                probability_summary: impactData?.probability_summary || "",
                risk_tolerance: impactData?.risk_tolerance || "Medium",
                days_lookback: impactData?.days_lookback || 90,
                // Include asset identification for saving
                name: characterizationData?.name,
                ticker: characterizationData?.ticker,
                isin: characterizationData?.isin,
              } as DetailedPipelineResult & { name?: string; ticker?: string; isin?: string };

              onComplete(finalResult);
            }
          } catch (parseError) {
            console.error("Failed to parse SSE event:", parseError);
          }
        }
      }
    }
  } catch (error) {
    if (error instanceof Error) {
      onError(error);
    } else {
      onError(new Error("Failed to run streaming geopolitical risk scan"));
    }
  }
}
