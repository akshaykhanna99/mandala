/** API functions for report generation. */

import type { DetailedPipelineResult } from "@/types/geoRisk";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function generateGPScanReport(
  pipelineResult: DetailedPipelineResult
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/reports/generate-gp-scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pipelineResult),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to generate report: ${response.statusText}`);
  }
  
  return response.blob();
}

export async function downloadReport(blob: Blob, filename: string): Promise<void> {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
