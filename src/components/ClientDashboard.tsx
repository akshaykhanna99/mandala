"use client";

import React, { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { runGeoRiskScanDetailed, runGeoRiskScanDetailedStreaming, type PipelineStepUpdate } from "@/lib/api/geoRisk";
import { searchAsset, type AssetSearchResponse } from "@/lib/api/assetSearch";
import { saveGPScan } from "@/lib/api/gpScans";
import { generateGPScanReport, downloadReport } from "@/lib/api/reports";
import type {
  DetailedPipelineResult,
  GeoRiskScanRequest,
  GeoRiskScanResult,
  Holding as GeoHolding,
} from "@/types/geoRisk";
import PipelineProgress, { type PipelineStep, type PipelineStepStatus } from "./PipelineProgress";

type AssetClass = 
  | "Equities"
  | "Fixed Income"
  | "Alternatives"
  | "Cash"
  | "Commodities"
  | "Real Estate"
  | "Private Equity";

type DetailedHolding = {
  id: string;
  name: string;
  ticker?: string;
  isin?: string;
  country?: string;
  class: AssetClass;
  sector: string;
  region: string;
  sub_region?: string;
  quantity?: number;
  value: number;
  cost_basis?: number;
  allocation_pct: number;
  allocation_class_pct?: number;
  pnl_to_date: number;
  pnl_pct: number;
  ytd_return?: number;
  last_price?: number;
  last_valuation_date?: string;
  entry_date?: string;
  currency: string;
  beta?: number;
  duration?: number;
  credit_rating?: string;
  gp_score?: {
    sell: number; // Probability (0-1)
    hold: number; // Probability (0-1)
    buy: number; // Probability (0-1)
  };
};

type ClientData = {
  id: string;
  name: string;
  riskTolerance: string;
  totalPortfolioValue: number;
  holdings: DetailedHolding[];
  assetClasses: Array<{
    class: string;
    allocation: number;
  }>;
  regions: Array<{
    region: string;
    allocation: number;
  }>;
  sectors: Array<{
    sector: string;
    allocation: number;
  }>;
};

// Mock client data generator with detailed investments
function getClientData(clientId: string, clientName: string, riskTolerance: string): ClientData {
  // Deterministic data based on client ID
  const seed = clientId.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  
  const baseValue = 50000000 + (seed % 200000000); // $50M - $250M
  
  // Generate detailed holdings
  const holdingsTemplates: Array<{
    name: string;
    class: AssetClass;
    region: string;
    country?: string;
    sub_region?: string;
    sector: string;
    allocation: number;
    ticker?: string;
    isin?: string;
  }> = [
    {
      name: "Indian Semiconductor Manufacturing Corp",
      class: "Equities",
      region: "Emerging Markets",
      country: "India",
      sub_region: "South Asia",
      sector: "Technology",
      allocation: 1.0, // Single asset, 100% allocation
      ticker: "ISMC",
      isin: "INE123A01001",
    },
  ];
  
  // Generate holdings with all properties
  const holdings: DetailedHolding[] = holdingsTemplates.map((template, idx) => {
    const value = baseValue * template.allocation;
    // Deterministic PnL based on seed + index
    const pnlSeed = (seed + idx * 17) % 100;
    const pnlPct = ((pnlSeed - 50) / 100) * 0.2; // -10% to +10% range
    const pnlToDate = value * pnlPct;
    const costBasis = value - pnlToDate;
    
    // Entry date (1-3 years ago)
    const entryDaysAgo = 365 + (seed % 730);
    const entryDate = new Date();
    entryDate.setDate(entryDate.getDate() - entryDaysAgo);
    
    // Last valuation (recent)
    const lastValuationDate = new Date();
    lastValuationDate.setDate(lastValuationDate.getDate() - (seed % 30));
    
    // Quantity (shares/units) - deterministic
    const quantity = Math.floor(1000 + (seed + idx * 23) % 10000);
    const lastPrice = value / quantity;
    
    // YTD return (slightly different from total return)
    const ytdReturn = pnlPct * 100 + ((seed + idx * 7) % 20 - 10) / 10;
    
    // Beta (for equities only)
    const beta = template.class === "Equities" ? 0.8 + ((seed + idx * 11) % 40) / 100 : undefined;
    
    // Duration (for fixed income only)
    const duration = template.class === "Fixed Income" ? 3 + ((seed + idx * 13) % 10) : undefined;
    
    // Credit rating (for fixed income only)
    const creditRatings = ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-"];
    const creditRating = template.class === "Fixed Income" 
      ? creditRatings[(seed + idx * 19) % creditRatings.length] 
      : undefined;
    
    // Calculate allocation within asset class
    const classAllocation = template.allocation * 100;
    
    return {
      id: `holding_${clientId}_${idx}`,
      name: template.name,
      ticker: template.ticker,
      isin: template.isin,
      country: template.country,
      class: template.class,
      sector: template.sector,
      region: template.region,
      sub_region: template.sub_region,
      quantity: quantity,
      value: value,
      cost_basis: costBasis,
      allocation_pct: template.allocation * 100,
      allocation_class_pct: classAllocation,
      pnl_to_date: pnlToDate,
      pnl_pct: pnlPct * 100,
      ytd_return: ytdReturn,
      last_price: lastPrice,
      last_valuation_date: lastValuationDate.toISOString().split("T")[0],
      entry_date: entryDate.toISOString().split("T")[0],
      currency: "USD",
      beta: beta,
      duration: duration,
      credit_rating: creditRating,
      // GP score will be populated when scan is run
      gp_score: undefined,
    };
  });
  
  // Calculate aggregated allocations
  const assetClassMap = new Map<string, number>();
  const regionMap = new Map<string, number>();
  const sectorMap = new Map<string, number>();
  
  holdings.forEach((h) => {
    assetClassMap.set(h.class, (assetClassMap.get(h.class) || 0) + h.allocation_pct);
    regionMap.set(h.region, (regionMap.get(h.region) || 0) + h.allocation_pct);
    sectorMap.set(h.sector, (sectorMap.get(h.sector) || 0) + h.allocation_pct);
  });
  
  return {
    id: clientId,
    name: clientName,
    riskTolerance,
    totalPortfolioValue: baseValue,
    holdings,
    assetClasses: Array.from(assetClassMap.entries()).map(([class_, allocation]) => ({
      class: class_,
      allocation: allocation / 100,
    })),
    regions: Array.from(regionMap.entries()).map(([region, allocation]) => ({
      region,
      allocation: allocation / 100,
    })),
    sectors: Array.from(sectorMap.entries()).map(([sector, allocation]) => ({
      sector,
      allocation: allocation / 100,
    })),
  };
}

type Client = {
  id: string;
  name: string;
  riskTolerance: string;
};

type ClientDashboardProps = {
  clients: Client[];
  selectedClientId: string;
  onClientChange: (clientId: string) => void;
  hideClientSelector?: boolean;
  demoMode?: boolean; // Demo mode: shows asset search instead of client holdings
};

export default function ClientDashboard({
  clients,
  selectedClientId,
  onClientChange,
  hideClientSelector = false,
  demoMode = false,
}: ClientDashboardProps) {
  const selectedClient = clients.find((c) => c.id === selectedClientId);
  const clientData = selectedClient
    ? getClientData(selectedClient.id, selectedClient.name, selectedClient.riskTolerance)
    : null;

  // Demo mode: Asset search state
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchedAsset, setSearchedAsset] = useState<AssetSearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const [scanResult, setScanResult] = useState<GeoRiskScanResult | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [pnlHorizon, setPnlHorizon] = useState<"ytd" | "1y" | "all">("all");
  const [gpScores, setGpScores] = useState<Record<string, { sell: number; hold: number; buy: number }>>({});
  const [scanningHoldings, setScanningHoldings] = useState<Set<string>>(new Set());
  const [currentPipelineResult, setCurrentPipelineResult] = useState<DetailedPipelineResult | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  
  // Pipeline progress tracking
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>([
    {
      id: "characterization",
      name: "Asset Characterization",
      description: "Extracting asset characteristics (country, region, sector, class)",
      status: "pending",
    },
    {
      id: "theme_identification",
      name: "Theme Identification",
      description: "Mapping asset to relevant geopolitical themes",
      status: "pending",
    },
    {
      id: "intelligence_retrieval",
      name: "Intelligence Retrieval",
      description: "Querying data sources for relevant signals",
      status: "pending",
    },
    {
      id: "impact_assessment",
      name: "Impact Assessment",
      description: "Analyzing signal direction and magnitude",
      status: "pending",
    },
  ]);
  
  // Column visibility state - default to essential columns only
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>({
    name: true,
    ticker: false,
    country: true,
    class: true,
    sector: true,
    region: true,
    quantity: false,
    value: true,
    cost_basis: false,
    allocation_pct: true,
    allocation_class_pct: false,
    pnl_to_date: true,
    pnl_pct: false,
    ytd_return: false,
    last_price: false,
    entry_date: false,
    last_valuation_date: false,
    beta: false,
    duration: false,
    credit_rating: false,
    gp_score: true,
  });
  
  // Sorting state
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  
  // Merge GP scores from scan results into holdings
  const holdingsWithGpScores = useMemo(() => {
    if (!clientData) return [];
    return clientData.holdings.map((holding) => ({
      ...holding,
      gp_score: gpScores[holding.id] || undefined,
    }));
  }, [clientData, gpScores]);

  const updateStepStatus = (
    stepId: string,
    status: PipelineStepStatus,
    details?: string,
    duration?: number,
    detailedData?: DetailedPipelineResult | null
  ) => {
    setPipelineSteps((prev) =>
      prev.map((step) =>
        step.id === stepId
          ? { ...step, status, details, duration, detailedData }
          : step
      )
    );
  };

  const resetPipelineSteps = () => {
    setPipelineSteps((prev) =>
      prev.map((step) => ({
        ...step,
        status: "pending" as PipelineStepStatus,
        details: undefined,
        duration: undefined,
        detailedData: undefined,
      }))
    );
  };

  // Debounced asset search
  const performSearch = useCallback(async (query: string) => {
    if (!query || query.trim().length < 2) {
      setSearchedAsset(null);
      setSearchError(null);
      return;
    }

    setIsSearching(true);
    setSearchError(null);

    try {
      const result = await searchAsset(query.trim());
      setSearchedAsset(result);
      setSearchError(null);
    } catch (error) {
      console.error("Asset search failed:", error);
      setSearchError(error instanceof Error ? error.message : "Failed to search for asset");
      setSearchedAsset(null);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Effect for debounced search
  useEffect(() => {
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Don't search for empty or very short queries
    if (!searchQuery || searchQuery.trim().length < 2) {
      setSearchedAsset(null);
      setSearchError(null);
      return;
    }

    // Set new timeout for debounced search
    searchTimeoutRef.current = setTimeout(() => {
      performSearch(searchQuery);
    }, 500); // 500ms debounce

    // Cleanup on unmount
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, performSearch]);

  const handleSaveResults = async (pipelineResult: DetailedPipelineResult) => {
    if (!pipelineResult) return;
    
    setIsSaving(true);
    try {
      await saveGPScan(
        pipelineResult as DetailedPipelineResult & { name?: string; ticker?: string; isin?: string },
        pipelineResult.risk_tolerance || "Medium",
        pipelineResult.days_lookback || 90
      );
      alert("✅ Scan results saved successfully!");
    } catch (error) {
      console.error("Failed to save scan:", error);
      alert(`Failed to save scan: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateReport = async (pipelineResult: DetailedPipelineResult) => {
    if (!pipelineResult) return;
    
    try {
      // Generate PDF report
      const blob = await generateGPScanReport(pipelineResult);
      
      // Generate filename
      const assetName = (pipelineResult as any).name || "asset";
      const dateStr = new Date().toISOString().split("T")[0].replace(/-/g, "");
      const filename = `mandala_gp_scan_${assetName.replace(/\s+/g, "_")}_${dateStr}.pdf`;
      
      // Download the PDF
      await downloadReport(blob, filename);
    } catch (error) {
      console.error("Failed to generate report:", error);
      alert(`Failed to generate report: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  const handleScan = async () => {
    if (demoMode) {
      // Demo mode: scan searched asset
      if (!searchedAsset) return;

      setIsScanning(true);
      setScanError(null);
      setScanResult(null);
      resetPipelineSteps();

      const holdingForScan: GeoHolding = {
        id: searchedAsset.ticker || searchedAsset.isin || searchedAsset.name,
        name: searchedAsset.name,
        class: searchedAsset.asset_class as AssetClass || "Equities",
        region: searchedAsset.region || "Unknown",
        sector: searchedAsset.sector || "Unknown",
        value: 1000000, // Demo value
        allocation_pct: 100,
        pnl_to_date: 0,
        pnl_pct: 0,
        currency: "USD",
        ticker: searchedAsset.ticker,
        isin: searchedAsset.isin,
        country: searchedAsset.country,
        sub_region: searchedAsset.sub_region,
      };

      const request: GeoRiskScanRequest = {
        client_id: "demo",
        as_of: new Date().toISOString().split("T")[0],
        horizon_days: 365,
        risk_tolerance: "medium",
        portfolio: {
          total_value: 1000000,
          holdings: [holdingForScan],
        },
      };

      await runGeoRiskScanDetailedStreaming(
        request,
        // onStepUpdate callback
        (update: PipelineStepUpdate) => {
          if (update.status === "completed") {
            // Map step IDs to match frontend step IDs
            let stepDetails = "";

            if (update.step_id === "characterization") {
              stepDetails = update.data?.characterization_summary || "Asset characterized";
            } else if (update.step_id === "theme_identification") {
              stepDetails = `Identified ${update.data?.themes?.length || 0} relevant themes`;
            } else if (update.step_id === "intelligence_retrieval") {
              stepDetails = `Retrieved ${update.data?.signal_count || 0} intelligence signals`;
            } else if (update.step_id === "impact_assessment") {
              stepDetails = `Impact direction: ${update.data?.impact?.overall_direction || "unknown"}`;
            } else if (update.step_id === "probability_calculation") {
              const probs = update.data?.probabilities;
              if (probs) {
                stepDetails = `Sell: ${Math.round(probs.sell * 100)}% | Hold: ${Math.round(probs.hold * 100)}% | Buy: ${Math.round(probs.buy * 100)}%`;
              }
            }

            updateStepStatus(update.step_id, "completed", stepDetails, update.duration_ms, null);
          } else if (update.status === "running") {
            updateStepStatus(update.step_id, "running", "", undefined, null);
          }
        },
        // onComplete callback
        (finalData: DetailedPipelineResult) => {
          // Store the final pipeline result with asset info
          const finalDataWithAsset = {
            ...finalData,
            name: searchedAsset?.name,
            ticker: searchedAsset?.ticker,
            isin: searchedAsset?.isin,
          };
          setCurrentPipelineResult(finalDataWithAsset as DetailedPipelineResult);
          const sellProb = finalData.probabilities.sell;
          const holdProb = finalData.probabilities.hold;
          const buyProb = finalData.probabilities.buy;

          // Update all steps with final detailed data
          updateStepStatus("characterization", "completed", finalData.characterization_summary, undefined, finalDataWithAsset as DetailedPipelineResult);
          updateStepStatus("theme_identification", "completed", `Identified ${finalData.themes.length} relevant themes`, undefined, finalDataWithAsset as DetailedPipelineResult);
          updateStepStatus("intelligence_retrieval", "completed", `Retrieved ${finalData.signal_count} intelligence signals`, undefined, finalDataWithAsset as DetailedPipelineResult);
          const probDetails = `Negative: ${Math.round(sellProb * 100)}% | Neutral: ${Math.round(holdProb * 100)}% | Positive: ${Math.round(buyProb * 100)}%`;
          updateStepStatus("impact_assessment", "completed", probDetails, undefined, finalDataWithAsset as DetailedPipelineResult);

          const primaryAction = sellProb > holdProb && sellProb > buyProb
            ? "SELL"
            : buyProb > holdProb && buyProb > sellProb
              ? "BUY"
              : "HOLD";

          setIsScanning(false);
        },
        // onError callback
        (error: Error) => {
          console.error("Demo scan error:", error);
          setScanError(error.message);
          setIsScanning(false);
        }
      );
      return;
    }

    // Regular mode: scan client holdings
    if (!selectedClient || !clientData) {
      return;
    }

    setIsScanning(true);
    setScanError(null);
    setScanResult(null);
    setScanningHoldings(new Set(clientData.holdings.map((h) => h.id)));
    resetPipelineSteps();

    try {
      // Scan each investment individually
      const newGpScores: Record<string, { sell: number; hold: number; buy: number }> = {};

      for (const holding of clientData.holdings) {
        const holdingForScan: GeoHolding = {
          id: holding.id,
          name: holding.name,
          class: holding.class,
          region: holding.region,
          sector: holding.sector,
          value: holding.value,
          allocation_pct: holding.allocation_pct,
          pnl_to_date: holding.pnl_to_date,
          pnl_pct: holding.pnl_pct,
          currency: holding.currency || "USD",
          entry_date: holding.entry_date,
          last_valuation_date: holding.last_valuation_date,
          ticker: holding.ticker,
          isin: holding.isin,
          country: holding.country,
          sub_region: holding.sub_region,
        };

        const request: GeoRiskScanRequest = {
          client_id: selectedClient.id,
          as_of: new Date().toISOString().split("T")[0],
          horizon_days: 365,
          risk_tolerance: selectedClient.riskTolerance.toLowerCase() as "low" | "medium" | "high",
          portfolio: {
            total_value: holding.value,
            holdings: [holdingForScan],
          },
        };

        await runGeoRiskScanDetailedStreaming(
          request,
          // onStepUpdate callback
          (update: PipelineStepUpdate) => {
            if (update.status === "completed") {
              let stepDetails = "";

              if (update.step_id === "characterization") {
                stepDetails = update.data?.characterization_summary || `Country: ${holding.country || "N/A"}, Region: ${holding.region}, Sector: ${holding.sector}`;
              } else if (update.step_id === "theme_identification") {
                stepDetails = `Identified ${update.data?.themes?.length || 0} relevant themes`;
              } else if (update.step_id === "intelligence_retrieval") {
                stepDetails = `Retrieved ${update.data?.signal_count || 0} intelligence signals`;
              } else if (update.step_id === "impact_assessment") {
                const probs = update.data?.probabilities;
                if (probs) {
                  stepDetails = `Negative: ${Math.round(probs.negative * 100)}% | Neutral: ${Math.round(probs.neutral * 100)}% | Positive: ${Math.round(probs.positive * 100)}%`;
                } else {
                  stepDetails = "Impact assessed";
                }
              }

              updateStepStatus(update.step_id, "completed", stepDetails, update.duration_ms, null);
            } else if (update.status === "running") {
              let runningDetails = "";
              if (update.step_id === "characterization") {
                runningDetails = `Analyzing ${holding.name}...`;
              } else if (update.step_id === "theme_identification") {
                runningDetails = "Identifying relevant themes...";
              } else if (update.step_id === "intelligence_retrieval") {
                runningDetails = "Querying intelligence signals...";
              } else if (update.step_id === "impact_assessment") {
                runningDetails = "Assessing geopolitical impact...";
              } else if (update.step_id === "probability_calculation") {
                runningDetails = "Calculating Sell/Hold/Buy probabilities...";
              }

              updateStepStatus(update.step_id, "running", runningDetails, undefined, null);
            }
          },
          // onComplete callback
          (finalData: DetailedPipelineResult) => {
            // Store the final pipeline result
            setCurrentPipelineResult(finalData);
            // Store the final pipeline result
            setCurrentPipelineResult(finalData);
            const sellProb = finalData.probabilities.sell;
            const holdProb = finalData.probabilities.hold;
            const buyProb = finalData.probabilities.buy;

            // Update all steps with final detailed data
            updateStepStatus("characterization", "completed", finalData.characterization_summary, undefined, finalData);
          updateStepStatus("theme_identification", "completed", `Identified ${finalData.themes.length} relevant themes`, undefined, finalDataWithAsset as DetailedPipelineResult);
          updateStepStatus("intelligence_retrieval", "completed", `Retrieved ${finalData.signal_count} intelligence signals`, undefined, finalDataWithAsset as DetailedPipelineResult);
          const probDetails = `Negative: ${Math.round(sellProb * 100)}% | Neutral: ${Math.round(holdProb * 100)}% | Positive: ${Math.round(buyProb * 100)}%`;
          updateStepStatus("impact_assessment", "completed", probDetails, undefined, finalDataWithAsset as DetailedPipelineResult);

            const primaryAction = sellProb > holdProb && sellProb > buyProb
              ? "SELL"
              : buyProb > holdProb && buyProb > sellProb
                ? "BUY"
              : "HOLD";

            newGpScores[holding.id] = { sell: sellProb, hold: holdProb, buy: buyProb };

            // Update state incrementally
            setGpScores((prev) => ({
              ...prev,
              [holding.id]: { sell: sellProb, hold: holdProb, buy: buyProb },
            }));

            // Remove from scanning set
            setScanningHoldings((prev) => {
              const next = new Set(prev);
              next.delete(holding.id);
              return next;
            });
          },
          // onError callback
          (error: Error) => {
            console.error(`Failed to scan ${holding.name}:`, error);
            // Continue with other holdings even if one fails
            setScanningHoldings((prev) => {
              const next = new Set(prev);
              next.delete(holding.id);
              return next;
            });
          }
        );
      }

      setGpScores(newGpScores);
    } catch (error) {
      setScanError(error instanceof Error ? error.message : "Failed to run scan");
    } finally {
      setIsScanning(false);
      setScanningHoldings(new Set());
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  // Column definitions
  type ColumnDef = {
    key: string;
    label: string;
    accessor: (h: DetailedHolding) => string | number | undefined;
    render?: (h: DetailedHolding) => React.ReactNode;
    sortable: boolean;
    align: "left" | "right";
  };

  const columns: ColumnDef[] = [
    {
      key: "name",
      label: "Name",
      accessor: (h) => h.name,
      render: (h) => (
        <div>
          <p className="font-medium text-slate-900">{h.name}</p>
          {h.isin && <p className="text-[10px] text-slate-500 mt-0.5">{h.isin}</p>}
        </div>
      ),
      sortable: true,
      align: "left",
    },
    {
      key: "ticker",
      label: "Ticker",
      accessor: (h) => h.ticker || "",
      sortable: true,
      align: "left",
    },
    {
      key: "country",
      label: "Country",
      accessor: (h) => h.country || "",
      sortable: true,
      align: "left",
    },
    {
      key: "class",
      label: "Class",
      accessor: (h) => h.class,
      sortable: true,
      align: "left",
    },
    {
      key: "sector",
      label: "Sector",
      accessor: (h) => h.sector,
      sortable: true,
      align: "left",
    },
    {
      key: "region",
      label: "Region",
      accessor: (h) => h.region,
      render: (h) => (
        <div>
          <p className="text-slate-700">{h.region}</p>
          {h.sub_region && <p className="text-[10px] text-slate-500 mt-0.5">{h.sub_region}</p>}
        </div>
      ),
      sortable: true,
      align: "left",
    },
    {
      key: "quantity",
      label: "Quantity",
      accessor: (h) => h.quantity || 0,
      render: (h) => h.quantity?.toLocaleString() || "-",
      sortable: true,
      align: "right",
    },
    {
      key: "value",
      label: "Value",
      accessor: (h) => h.value,
      render: (h) => formatCurrency(h.value),
      sortable: true,
      align: "right",
    },
    {
      key: "cost_basis",
      label: "Cost Basis",
      accessor: (h) => h.cost_basis || 0,
      render: (h) => h.cost_basis ? formatCurrency(h.cost_basis) : "-",
      sortable: true,
      align: "right",
    },
    {
      key: "allocation_pct",
      label: "% Portfolio",
      accessor: (h) => h.allocation_pct,
      render: (h) => `${h.allocation_pct.toFixed(2)}%`,
      sortable: true,
      align: "right",
    },
    {
      key: "allocation_class_pct",
      label: "% of Class",
      accessor: (h) => h.allocation_class_pct || 0,
      render: (h) => h.allocation_class_pct ? `${h.allocation_class_pct.toFixed(2)}%` : "-",
      sortable: true,
      align: "right",
    },
    {
      key: "pnl_to_date",
      label: "PnL",
      accessor: (h) => h.pnl_to_date,
      render: (h) => (
        <span className={h.pnl_to_date >= 0 ? "text-green-700" : "text-red-700"}>
          {formatCurrency(h.pnl_to_date)}
        </span>
      ),
      sortable: true,
      align: "right",
    },
    {
      key: "pnl_pct",
      label: "Return %",
      accessor: (h) => h.pnl_pct,
      render: (h) => (
        <span className={h.pnl_pct >= 0 ? "text-green-700" : "text-red-700"}>
          {h.pnl_pct >= 0 ? "+" : ""}{h.pnl_pct.toFixed(2)}%
        </span>
      ),
      sortable: true,
      align: "right",
    },
    {
      key: "ytd_return",
      label: "YTD Return %",
      accessor: (h) => h.ytd_return || 0,
      render: (h) => h.ytd_return !== undefined ? `${h.ytd_return >= 0 ? "+" : ""}${h.ytd_return.toFixed(2)}%` : "-",
      sortable: true,
      align: "right",
    },
    {
      key: "last_price",
      label: "Last Price",
      accessor: (h) => h.last_price || 0,
      render: (h) => h.last_price ? formatCurrency(h.last_price) : "-",
      sortable: true,
      align: "right",
    },
    {
      key: "entry_date",
      label: "Entry Date",
      accessor: (h) => h.entry_date || "",
      render: (h) => h.entry_date ? new Date(h.entry_date).toLocaleDateString() : "-",
      sortable: true,
      align: "left",
    },
    {
      key: "last_valuation_date",
      label: "Last Valuation",
      accessor: (h) => h.last_valuation_date || "",
      render: (h) => h.last_valuation_date ? new Date(h.last_valuation_date).toLocaleDateString() : "-",
      sortable: true,
      align: "left",
    },
    {
      key: "beta",
      label: "Beta",
      accessor: (h) => h.beta || 0,
      render: (h) => h.beta !== undefined ? h.beta.toFixed(2) : "-",
      sortable: true,
      align: "right",
    },
    {
      key: "duration",
      label: "Duration",
      accessor: (h) => h.duration || 0,
      render: (h) => h.duration !== undefined ? h.duration.toFixed(1) : "-",
      sortable: true,
      align: "right",
    },
    {
      key: "credit_rating",
      label: "Credit Rating",
      accessor: (h) => h.credit_rating || "",
      sortable: true,
      align: "left",
    },
    {
      key: "gp_score",
      label: "GP Score",
      accessor: (h) => h.gp_score?.hold || 0, // Sort by hold probability
      render: (h) => {
        const isScanning = scanningHoldings.has(h.id);
        
        if (isScanning) {
          return (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>Scanning...</span>
            </div>
          );
        }
        
        if (!h.gp_score) {
          return (
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span>Not scanned</span>
            </div>
          );
        }
        
        const { sell, hold, buy } = h.gp_score;
        const sellPct = Math.round(sell * 100);
        const holdPct = Math.round(hold * 100);
        const buyPct = Math.round(buy * 100);
        
        return (
          <div className="relative flex h-6 w-40 overflow-hidden rounded border border-slate-300">
            {/* Sell segment */}
            {sellPct > 0 && (
              <div
                className={`relative flex items-center justify-center text-[10px] font-semibold ${
                  demoMode ? "bg-pink-300 text-slate-700" : "bg-red-500 text-white"
                }`}
                style={{ width: `${sellPct}%` }}
              >
                {sellPct >= 10 && `${sellPct}%`}
              </div>
            )}
            {/* Hold segment */}
            {holdPct > 0 && (
              <div
                className={`relative flex items-center justify-center text-[10px] font-semibold ${
                  demoMode ? "bg-yellow-200 text-slate-700" : "bg-yellow-500 text-slate-900"
                }`}
                style={{ width: `${holdPct}%` }}
              >
                {holdPct >= 10 && `${holdPct}%`}
              </div>
            )}
            {/* Buy segment */}
            {buyPct > 0 && (
              <div
                className={`relative flex items-center justify-center text-[10px] font-semibold ${
                  demoMode ? "bg-green-300 text-slate-700" : "bg-green-500 text-white"
                }`}
                style={{ width: `${buyPct}%` }}
              >
                {buyPct >= 10 && `${buyPct}%`}
              </div>
            )}
          </div>
        );
      },
      sortable: true,
      align: "right",
    },
  ];

  // Sort holdings (use holdings with GP scores)
  const sortedHoldings = useMemo(() => {
    if (!clientData || !sortColumn) return holdingsWithGpScores;
    
    const sorted = [...holdingsWithGpScores].sort((a, b) => {
      const col = columns.find((c) => c.key === sortColumn);
      if (!col) return 0;
      
      const aVal = col.accessor(a);
      const bVal = col.accessor(b);
      
      // Handle undefined/null values
      if (aVal === undefined || aVal === null) return 1;
      if (bVal === undefined || bVal === null) return -1;
      
      // Compare values
      let comparison = 0;
      if (typeof aVal === "number" && typeof bVal === "number") {
        comparison = aVal - bVal;
      } else {
        comparison = String(aVal).localeCompare(String(bVal));
      }
      
      return sortDirection === "asc" ? comparison : -comparison;
    });
    
    return sorted;
  }, [holdingsWithGpScores, sortColumn, sortDirection]);

  const handleSort = (columnKey: string) => {
    if (sortColumn === columnKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(columnKey);
      setSortDirection("asc");
    }
  };

  const toggleColumn = (columnKey: string) => {
    setVisibleColumns((prev) => ({
      ...prev,
      [columnKey]: !prev[columnKey],
    }));
  };

  const visibleColumnsList = columns.filter((col) => visibleColumns[col.key]);

  return (
    <div className="pointer-events-auto absolute left-40 right-40 top-24 z-20 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
      <div className="flex h-[calc(100vh-120px)] flex-col overflow-hidden">
        {/* Header */}
        <div className="border-b border-slate-200 bg-slate-50 px-6 py-5">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
            {demoMode ? "Geopolitics Risk Calculator" : "Client"}
          </p>
          
          {/* Client Search - Hidden in demo mode */}
          {!hideClientSelector && (
            <div className="mt-4">
              <label className="mb-2 block text-xs font-medium text-slate-700">
                Client Search
              </label>
              <select
                value={selectedClientId}
                onChange={(e) => onClientChange(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-sm transition focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400/20"
              >
                <option value="">Select a client...</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* GP Health Scan Button - Only show in non-demo mode here */}
          {!demoMode && (
            <button
              type="button"
              onClick={handleScan}
              disabled={!selectedClient || isScanning}
              className="mt-3 rounded-full border border-slate-300 bg-slate-900 px-4 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-400/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isScanning ? "Scanning..." : "GP Health Scan"}
            </button>
          )}

          {/* Client Info - Hidden in demo mode */}
          {selectedClient && !demoMode && (
            <>
              <h1 className="mt-5 text-2xl font-semibold text-slate-900">{selectedClient.name}</h1>
              <div className="mt-3 flex items-center gap-3">
                <span className="rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  {selectedClient.riskTolerance} Risk Tolerance
                </span>
              </div>
            </>
          )}
        </div>

        {/* Content - Scrollable */}
        {(clientData || demoMode) ? (
          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className="space-y-6">

              {/* Scan Error */}
              {scanError && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                  <p className="font-semibold">Error</p>
                  <p>{scanError}</p>
                </div>
              )}

              {/* Scan Results */}
              {scanResult && (
                <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="border-b border-slate-200 pb-3">
                    <h3 className="text-sm font-semibold text-slate-900">Geopolitical Risk Assessment</h3>
                    <p className="mt-1 text-xs text-slate-500">
                      As of {scanResult.inputs.as_of} • {scanResult.inputs.horizon_days} day horizon
                    </p>
                  </div>

                  {/* Scenarios */}
                  <div>
                    <p className="mb-2 text-xs font-medium text-slate-700">Risk Scenarios</p>
                    <div className="space-y-2">
                      {scanResult.geo_risk.scenarios.map((scenario) => (
                        <div key={scenario.name} className="flex items-center gap-3">
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-medium text-slate-700 capitalize">
                                {scenario.name}
                              </span>
                              <span className="text-xs font-semibold text-slate-900">
                                {(scenario.p * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                              <div
                                className="h-full bg-slate-600 transition-all"
                                style={{ width: `${scenario.p * 100}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Confidence */}
                  <div>
                    <p className="mb-1 text-xs font-medium text-slate-700">Confidence</p>
                    <span className="inline-block rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 capitalize">
                      {scanResult.geo_risk.confidence}
                    </span>
                  </div>

                  {/* Drivers */}
                  <div>
                    <p className="mb-2 text-xs font-medium text-slate-700">Key Drivers</p>
                    <ul className="list-disc list-inside space-y-1 text-xs text-slate-600">
                      {scanResult.geo_risk.drivers.map((driver, idx) => (
                        <li key={idx}>{driver}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Suitability Impact */}
                  <div>
                    <p className="mb-2 text-xs font-medium text-slate-700">Suitability Impact</p>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {scanResult.geo_risk.suitability_impact}
                    </p>
                  </div>

                  {/* Limitations */}
                  <div>
                    <p className="mb-2 text-xs font-medium text-slate-700">Limitations</p>
                    <ul className="list-disc list-inside space-y-1 text-xs text-slate-600">
                      {scanResult.geo_risk.limitations.map((limitation, idx) => (
                        <li key={idx}>{limitation}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Disclaimer */}
                  <div className="rounded border border-slate-200 bg-slate-50 p-3">
                    <p className="text-xs font-medium text-slate-700 mb-1">Disclaimer</p>
                    <p className="text-xs text-slate-600">{scanResult.geo_risk.disclaimer}</p>
                  </div>

                  {/* Metadata */}
                  <div className="border-t border-slate-200 pt-3 text-xs text-slate-500">
                    <p>Created: {new Date(scanResult.created_at).toLocaleString()}</p>
                    <p>Model: {scanResult.meta.model} {scanResult.meta.used_fallback && "(fallback)"}</p>
                    {scanResult.meta.validation.errors.length > 0 && (
                      <p className="text-red-600">
                        Validation errors: {scanResult.meta.validation.errors.join(", ")}
                      </p>
                    )}
                  </div>

                  {/* Raw JSON (collapsible) */}
                  <details className="mt-4">
                    <summary className="cursor-pointer text-xs font-medium text-slate-700">
                      Raw JSON
                    </summary>
                    <pre className="mt-2 overflow-auto rounded border border-slate-200 bg-slate-50 p-3 text-[10px] text-slate-600">
                      {JSON.stringify(scanResult, null, 2)}
                    </pre>
                  </details>
                </div>
              )}

              {/* Portfolio Metrics - Hidden in demo mode */}
              {!demoMode && clientData && (
                <div className="flex gap-4">
                  {/* Total Portfolio Value */}
                  <div className="w-[280px] rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-4 shadow-sm">
                    <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                      Portfolio Value
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">
                      {formatCurrency(clientData.totalPortfolioValue)}
                    </p>
                  </div>

                  {/* Total PnL */}
                  <div className="w-[280px] rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
                        Total PnL
                      </p>
                      <select
                        value={pnlHorizon}
                        onChange={(e) => setPnlHorizon(e.target.value as "ytd" | "1y" | "all")}
                        className="text-[10px] rounded border border-slate-200 bg-white px-2 py-0.5 text-slate-600 focus:outline-none focus:ring-1 focus:ring-slate-400"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <option value="ytd">YTD</option>
                        <option value="1y">1Y</option>
                        <option value="all">All Time</option>
                      </select>
                    </div>
                    {(() => {
                      let totalPnl = 0;
                      if (pnlHorizon === "all") {
                        totalPnl = clientData.holdings.reduce((sum, h) => sum + h.pnl_to_date, 0);
                      } else if (pnlHorizon === "ytd") {
                        // For YTD, use ytd_return if available, otherwise estimate
                        totalPnl = clientData.holdings.reduce((sum, h) => {
                          if (h.ytd_return !== undefined) {
                            return sum + (h.value * h.ytd_return / 100);
                          }
                          // Estimate YTD as 70% of total return
                          return sum + (h.pnl_to_date * 0.7);
                        }, 0);
                      } else if (pnlHorizon === "1y") {
                        // For 1Y, estimate as 80% of total return
                        totalPnl = clientData.holdings.reduce((sum, h) => sum + (h.pnl_to_date * 0.8), 0);
                      }
                      const pnlPct = (totalPnl / clientData.totalPortfolioValue) * 100;
                      return (
                        <>
                          <p className={`mt-2 text-2xl font-semibold ${
                            totalPnl >= 0 ? "text-green-700" : "text-red-700"
                          }`}>
                            {formatCurrency(totalPnl)}
                          </p>
                          <p className={`mt-1 text-sm font-medium ${
                            pnlPct >= 0 ? "text-green-700" : "text-red-700"
                          }`}>
                            {pnlPct >= 0 ? "+" : ""}{pnlPct.toFixed(2)}%
                          </p>
                        </>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Asset Search - Demo Mode */}
              {demoMode && (
                <div>
                  <h3 className="mb-4 text-sm font-semibold text-slate-900">
                    Asset Search
                  </h3>

                  {/* Search Input */}
                  <div className="mb-4">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search for an asset (e.g., TSMC, Saudi Aramco, Gold...)"
                      className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 shadow-sm transition focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400/20"
                    />

                    {/* Search Status */}
                    {isSearching && (
                      <div className="mt-2 flex items-center gap-2 text-xs text-slate-600">
                        <div className="h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
                        <span>Searching for asset...</span>
                      </div>
                    )}

                    {/* Search Error */}
                    {searchError && !isSearching && (
                      <div className="mt-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                        {searchError}
                      </div>
                    )}

                    {/* No Results */}
                    {!isSearching && searchQuery.length >= 2 && !searchedAsset && !searchError && (
                      <div className="mt-2 text-xs text-slate-500">
                        No asset found. Try a different search term.
                      </div>
                    )}
                  </div>

                  {/* Asset Summary (only shown when asset found) */}
                  {searchedAsset && (
                    <>
                      <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
                        <div className="mb-3 flex items-start justify-between">
                          <h4 className="text-xs font-semibold text-slate-900">Asset Summary</h4>
                          <div className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-700">
                            {Math.round(searchedAsset.confidence * 100)}% confidence
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <span className="font-medium text-slate-600">Name:</span>
                            <span className="ml-2 text-slate-900">{searchedAsset.name}</span>
                          </div>
                          {searchedAsset.ticker && (
                            <div>
                              <span className="font-medium text-slate-600">Ticker:</span>
                              <span className="ml-2 text-slate-900">{searchedAsset.ticker}</span>
                            </div>
                          )}
                          {searchedAsset.country && (
                            <div>
                              <span className="font-medium text-slate-600">Country:</span>
                              <span className="ml-2 text-slate-900">{searchedAsset.country}</span>
                            </div>
                          )}
                          {searchedAsset.region && (
                            <div>
                              <span className="font-medium text-slate-600">Region:</span>
                              <span className="ml-2 text-slate-900">{searchedAsset.region}</span>
                            </div>
                          )}
                          {searchedAsset.sector && (
                            <div>
                              <span className="font-medium text-slate-600">Sector:</span>
                              <span className="ml-2 text-slate-900">{searchedAsset.sector}</span>
                            </div>
                          )}
                          {searchedAsset.asset_class && (
                            <div>
                              <span className="font-medium text-slate-600">Class:</span>
                              <span className="ml-2 text-slate-900">{searchedAsset.asset_class}</span>
                            </div>
                          )}
                        </div>
                        {searchedAsset.description && (
                          <div className="mt-3 border-t border-slate-200 pt-3">
                            <span className="block text-[10px] font-medium uppercase tracking-wide text-slate-500 mb-1">Description</span>
                            <p className="text-xs leading-relaxed text-slate-700">{searchedAsset.description}</p>
                          </div>
                        )}
                      </div>

                      {/* GP Health Scan Button (after summary) */}
                      <button
                        type="button"
                        onClick={handleScan}
                        disabled={isScanning}
                        className="w-full rounded-full border border-slate-300 bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-400/20 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isScanning ? "Scanning..." : "Run GP Health Scan"}
                      </button>
                    </>
                  )}
                </div>
              )}

            {/* Current Holdings - Modular Table (Hidden in demo mode) */}
            {!demoMode && clientData && (
            <div>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">
                  Current Holdings / Allocations
                </h3>
                <div className="flex items-center gap-3">
                  {/* GP Score Legend */}
                  <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5">
                    <div className="flex items-center gap-1.5">
                      <div className={`h-3 w-3 rounded ${demoMode ? "bg-pink-300" : "bg-red-500"}`} />
                      <span className="text-[10px] font-medium text-slate-700">
                        {demoMode ? "Negative" : "Sell"}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className={`h-3 w-3 rounded ${demoMode ? "bg-yellow-200" : "bg-yellow-500"}`} />
                      <span className="text-[10px] font-medium text-slate-700">
                        {demoMode ? "Neutral" : "Hold"}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className={`h-3 w-3 rounded ${demoMode ? "bg-green-300" : "bg-green-500"}`} />
                      <span className="text-[10px] font-medium text-slate-700">
                        {demoMode ? "Positive" : "Buy"}
                      </span>
                    </div>
                  </div>
                  
                  {/* Column Visibility Toggle */}
                  <details className="relative">
                    <summary className="cursor-pointer text-xs font-medium text-slate-600 hover:text-slate-900">
                      Columns
                    </summary>
                    <div className="absolute right-0 top-6 z-20 w-48 rounded-lg border border-slate-200 bg-white p-2 shadow-lg">
                      <div className="max-h-64 space-y-1 overflow-y-auto">
                        {columns.map((col) => (
                          <label
                            key={col.key}
                            className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-slate-50"
                          >
                            <input
                              type="checkbox"
                              checked={visibleColumns[col.key]}
                              onChange={() => toggleColumn(col.key)}
                              className="h-3 w-3 rounded border-slate-300 text-slate-600 focus:ring-slate-400"
                            />
                            <span className="text-xs text-slate-700">{col.label}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  </details>
                </div>
              </div>
              
              <div className="overflow-hidden rounded-lg border border-slate-200">
                <div className="max-h-[500px] overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 z-10 bg-slate-50">
                      <tr className="border-b border-slate-200">
                        {visibleColumnsList.map((col) => (
                          <th
                            key={col.key}
                            className={`px-4 py-3 font-semibold text-slate-700 ${
                              col.align === "right" ? "text-right" : "text-left"
                            } ${
                              col.sortable ? "cursor-pointer select-none hover:bg-slate-100" : ""
                            }`}
                            onClick={() => col.sortable && handleSort(col.key)}
                          >
                            <div className="flex items-center gap-1">
                              <span>{col.label}</span>
                              {col.sortable && sortColumn === col.key && (
                                <span className="text-slate-400">
                                  {sortDirection === "asc" ? "↑" : "↓"}
                                </span>
                              )}
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {sortedHoldings.map((holding) => (
                        <tr
                          key={holding.id}
                          className="hover:bg-slate-50 transition-colors"
                        >
                          {visibleColumnsList.map((col) => (
                            <td
                              key={col.key}
                              className={`px-4 py-3 text-slate-700 ${
                                col.align === "right" ? "text-right" : "text-left"
                              } whitespace-nowrap`}
                            >
                              {col.render ? col.render(holding) : String(col.accessor(holding) || "-")}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
            )}

            {/* Pipeline Progress */}
            <PipelineProgress 
              steps={pipelineSteps} 
              isRunning={isScanning}
              onSaveResults={handleSaveResults}
              onGenerateReport={handleGenerateReport}
            />

          </div>
        </div>
        ) : (
          <div className="flex-1 px-6 py-12">
            <p className="text-center text-sm text-slate-500">
              Select a client to view their portfolio dashboard
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
