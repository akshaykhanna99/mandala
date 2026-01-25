"use client";
import React, { useState } from "react";
import type { DetailedPipelineResult } from "@/types/geoRisk";

export type PipelineStepStatus = "pending" | "running" | "completed" | "error";

export interface PipelineStep {
  id: string;
  name: string;
  description: string;
  status: PipelineStepStatus;
  details?: string;
  duration?: number; // milliseconds
  detailedData?: DetailedPipelineResult | null; // Full pipeline result for detailed view
}

interface PipelineProgressProps {
  steps: PipelineStep[];
  isRunning: boolean;
  onSaveResults?: (pipelineResult: DetailedPipelineResult) => Promise<void>;
  onGenerateReport?: (pipelineResult: DetailedPipelineResult) => Promise<void>;
}

export default function PipelineProgress({ steps, isRunning, onSaveResults, onGenerateReport }: PipelineProgressProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [showAllSignals, setShowAllSignals] = useState<Record<string, boolean>>({});

  const toggleStep = (stepId: string) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  if (!isRunning && steps.every((s) => s.status === "pending")) {
    return null; // Don't show if not started
  }

  const renderStepDetails = (step: PipelineStep, showAllSignals: Record<string, boolean>, setShowAllSignals: React.Dispatch<React.SetStateAction<Record<string, boolean>>>) => {
    if (!step.detailedData || step.status !== "completed") {
      return null;
    }

    const data = step.detailedData;

    switch (step.id) {
      case "characterization":
        const characteristics = [];
        if (data.asset_country) {
          characteristics.push({ label: "Country", value: data.asset_country });
        }
        characteristics.push({ label: "Region", value: data.asset_region });
        characteristics.push({ label: "Class", value: data.asset_class });
        characteristics.push({ label: "Sector", value: data.asset_sector });
        const marketType = data.is_emerging_market
          ? "Emerging"
          : data.is_developed_market
            ? "Developed"
            : data.is_global_fund
              ? "Global"
              : null;
        if (marketType) {
          characteristics.push({ label: "Market", value: marketType });
        }
        
        return (
          <div className="mt-3 rounded-md bg-slate-50 p-3 text-xs">
            <div className="font-medium text-slate-700 mb-3">
              Asset Characteristics:
            </div>
            <div className="flex flex-wrap gap-2">
              {characteristics.map((char, idx) => (
                <div
                  key={idx}
                  className="rounded-full border border-slate-300 bg-white px-3 py-1.5 flex items-center gap-2"
                >
                  <span className="text-slate-500 text-[10px] font-medium">
                    {char.label}:
                  </span>
                  <span className="font-medium text-slate-800">
                    {char.value}
                  </span>
                </div>
              ))}
              {data.exposures.length > 0 &&
                data.exposures
                  .filter((exposure) => {
                    // Filter out exposures that exactly match the sector to avoid redundancy
                    const sector = (data.asset_sector || "").toLowerCase();
                    const exposureLower = exposure.toLowerCase();
                    return sector !== exposureLower;
                  })
                  .map((exposure, idx) => (
                    <div
                      key={`exposure-${idx}`}
                      className="rounded-full border border-orange-300 bg-orange-50 px-3 py-1.5"
                    >
                      <span className="font-medium text-orange-800">
                        {exposure}
                      </span>
                    </div>
                  ))}
            </div>
          </div>
        );

      case "theme_identification":
        const formatThemeName = (theme: string) => {
          return theme
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
        };

        return (
          <div className="mt-3 rounded-md bg-slate-50 p-3 text-xs">
            <div className="font-medium text-slate-700 mb-3">
              Identified Themes ({data.themes.length}):
            </div>
            <div className="flex flex-wrap gap-2">
              {data.themes.map((theme, idx) => (
                <div
                  key={idx}
                  className="rounded-full border border-slate-300 bg-white px-3 py-1.5 flex items-center gap-2"
                >
                  <span className="font-medium text-slate-800">
                    {formatThemeName(theme.theme)}
                  </span>
                  <span className="text-slate-500 text-[10px] font-semibold">
                    {(theme.relevance_score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        );

      case "intelligence_retrieval":
        const stepId = step.id;
        const isShowingAll = showAllSignals[stepId] || false;
        const dbSignals = data.signals.filter((s) => s.source !== "web_search");
        const webSignals = data.signals.filter((s) => s.source === "web_search");
        const displayedSignals = isShowingAll ? data.signals : data.signals.slice(0, 10);
        
        return (
          <div className="mt-3 space-y-3 rounded-md bg-slate-50 p-3 text-xs">
            {/* Web Search Section */}
            {data.web_searches && data.web_searches.length > 0 && (
              <div className="mb-3 rounded border border-blue-200 bg-blue-50 p-2">
                <div className="font-medium text-blue-800 mb-2">
                  🔍 Web Searches ({data.web_searches.length} themes):
                </div>
                {data.web_searches.map((search, idx) => (
                  <div key={idx} className="mb-2 rounded bg-white p-2 text-slate-700">
                    <div className="font-medium">{search.theme.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}</div>
                    <div className="text-slate-600 text-[10px] mt-1">
                      Query: "{search.query}"
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-slate-500">
                      <span>
                        {search.results_count} articles found
                        <span className="text-slate-400 ml-1" title="Raw web search results from Tavily">
                          (raw)
                        </span>
                      </span>
                      <span>•</span>
                      <span>
                        {search.signals_count} signals extracted
                        <span className="text-slate-400 ml-1" title="Processed and scored intelligence signals ready for analysis">
                          (processed)
                        </span>
                      </span>
                      {search.error && (
                        <>
                          <span>•</span>
                          <span className="text-red-500">Error</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
                <div className="mt-2 text-[10px] text-slate-500 italic">
                  <strong>Articles</strong> = raw web search results. <strong>Signals</strong> = processed, scored intelligence ready for analysis.
                </div>
              </div>
            )}
            
            {/* Signals Section */}
            <div className="font-medium text-slate-700 mb-2">
              Intelligence Signals ({data.signals.length} total):
              {dbSignals.length > 0 && (
                <span className="text-slate-500 ml-2">
                  {dbSignals.length} from database
                </span>
              )}
              {webSignals.length > 0 && (
                <span className="text-blue-600 ml-2">
                  {webSignals.length} from web search
                </span>
              )}
            </div>
            
            {/* Scrollable Signals Table */}
            <div className="max-h-96 overflow-y-auto rounded border border-slate-200 bg-white">
              <div className="divide-y divide-slate-100">
                {displayedSignals.map((signal, idx) => (
                  <div key={idx} className="p-2 hover:bg-slate-50 transition-colors">
                    <div className="flex items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <div className="font-medium text-slate-800 truncate">{signal.title}</div>
                          {signal.source === "web_search" && (
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 whitespace-nowrap">
                              Web
                            </span>
                          )}
                          <span className="text-slate-400 text-[10px] whitespace-nowrap">
                            {(signal.relevance_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="mt-1 text-slate-600 text-[11px] line-clamp-2">{signal.summary}</p>
                        <div className="mt-2 flex items-center gap-3 text-slate-500 text-[10px] flex-wrap">
                          {signal.theme_match && (
                            <span className="px-1.5 py-0.5 rounded bg-slate-100">
                              {signal.theme_match.replace(/_/g, " ")}
                            </span>
                          )}
                          {signal.country && <span>📍 {signal.country}</span>}
                          <span>{new Date(signal.published_at).toLocaleDateString()}</span>
                          {signal.url && (
                            <a
                              href={signal.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline"
                            >
                              View source →
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {data.signals.length > 10 && (
              <button
                onClick={() => setShowAllSignals((prev) => ({
                  ...prev,
                  [stepId]: !isShowingAll,
                }))}
                className="w-full mt-2 text-xs text-blue-600 hover:text-blue-800 font-medium py-1"
              >
                {isShowingAll ? (
                  <>Show less (showing all {data.signals.length})</>
                ) : (
                  <>Show all {data.signals.length} signals (showing first 10)</>
                )}
              </button>
            )}
          </div>
        );

      case "impact_assessment":
        // Helper function to get direction pill styling
        const getDirectionPillClass = (direction: string) => {
          const dir = direction.toLowerCase();
          if (dir === "negative") {
            return "rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700";
          } else if (dir === "positive") {
            return "rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700";
          } else {
            return "rounded-full bg-yellow-100 px-3 py-1 text-xs font-medium text-yellow-700";
          }
        };

        // Get probabilities - handle both formats (negative/neutral/positive or sell/hold/buy)
        const probData = data.probabilities || {};
        let negative = 0;
        let neutral = 0;
        let positive = 0;

        if (probData.negative !== undefined || probData.neutral !== undefined || probData.positive !== undefined) {
          // New format: negative/neutral/positive
          negative = probData.negative || 0;
          neutral = probData.neutral || 0;
          positive = probData.positive || 0;
        } else {
          // Old format: sell/hold/buy (map to negative/neutral/positive)
          negative = probData.sell || 0;
          neutral = probData.hold || 0;
          positive = probData.buy || 0;
        }

        // Calculate percentages (ensure they sum to 100%)
        const total = negative + neutral + positive;
        const negativePct = total > 0 ? Math.round((negative / total) * 100) : 33;
        const neutralPct = total > 0 ? Math.round((neutral / total) * 100) : 34;
        const positivePct = total > 0 ? Math.round((positive / total) * 100) : 33;

        return (
          <div className="mt-3 space-y-4 text-xs">
            {/* Geopolitical Health Score Section */}
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Geopolitical Health Score</h3>
              <div className="flex items-center gap-4">
                {/* Bar - 70% width */}
                <div className="flex-[0.7]">
                  <div className="relative h-12 w-full rounded-full border-2 border-slate-300 overflow-hidden bg-slate-200">
                    {/* Negative segment (red) */}
                    <div 
                      className="absolute left-0 top-0 h-full bg-red-500 flex items-center justify-center transition-all z-10"
                      style={{ width: `${negativePct}%` }}
                    >
                      {negativePct >= 10 && (
                        <div className="text-xs font-semibold text-white">
                          Negative {negativePct}%
                        </div>
                      )}
                    </div>
                    {/* Neutral segment (yellow) */}
                    <div 
                      className="absolute top-0 h-full bg-yellow-500 flex items-center justify-center transition-all z-10"
                      style={{ left: `${negativePct}%`, width: `${neutralPct}%` }}
                    >
                      {neutralPct >= 10 && (
                        <div className="text-xs font-semibold text-white">
                          Neutral {neutralPct}%
                        </div>
                      )}
                    </div>
                    {/* Positive segment (green) */}
                    <div 
                      className="absolute top-0 h-full bg-green-500 flex items-center justify-center transition-all z-10"
                      style={{ left: `${negativePct + neutralPct}%`, width: `${positivePct}%` }}
                    >
                      {positivePct >= 10 && (
                        <div className="text-xs font-semibold text-white">
                          Positive {positivePct}%
                        </div>
                      )}
                    </div>
                    {/* Labels for small segments */}
                    {negativePct > 0 && negativePct < 10 && (
                      <div className="absolute left-1 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-red-700 z-20">
                        {negativePct}%
                      </div>
                    )}
                    {neutralPct > 0 && neutralPct < 10 && (
                      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-[10px] font-semibold text-yellow-700 z-20">
                        {neutralPct}%
                      </div>
                    )}
                    {positivePct > 0 && positivePct < 10 && (
                      <div className="absolute right-1 top-1/2 -translate-y-1/2 text-[10px] font-semibold text-green-700 z-20">
                        {positivePct}%
                      </div>
                    )}
                  </div>
                </div>
                {/* Confidence - 15% width */}
                <div className="flex-[0.15] flex flex-col items-center justify-center border-l border-slate-200 pl-4">
                  <span className="text-slate-500 text-xs mb-1">Confidence</span>
                  <span className="font-semibold text-slate-900 text-sm">
                    {(data.impact.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                {/* Total Signals - 15% width */}
                <div className="flex-[0.15] flex flex-col items-center justify-center border-l border-slate-200 pl-4">
                  <span className="text-slate-500 text-xs mb-1">Total Signals</span>
                  <span className="font-semibold text-slate-900 text-sm">{data.impact.total_signals}</span>
                </div>
              </div>
            </div>

            {/* Theme Impacts Section */}
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900 mb-3">Theme Impact Analysis</h3>
              <div className="space-y-3">
            {data.impact.theme_impacts.map((impact, idx) => (
              <div key={idx} className="rounded border border-slate-200 bg-white overflow-hidden">
                {/* Split-screen layout - 30/70 */}
                <div className="flex divide-x divide-slate-200">
                  {/* Left side: Theme info and scores - 30% */}
                  <div className="flex-[0.3] p-3 bg-slate-50">
                    {/* Theme name and direction pill */}
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="font-semibold text-slate-900 text-sm leading-tight">
                        {impact.theme.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                      </h4>
                      <span className={getDirectionPillClass(impact.impact_direction)}>
                        {impact.impact_direction.charAt(0).toUpperCase() + impact.impact_direction.slice(1)}
                      </span>
                    </div>

                    {/* Key scores */}
                    <div className="space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-600 font-medium">Magnitude:</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                impact.impact_direction === 'negative' ? 'bg-red-500' :
                                impact.impact_direction === 'positive' ? 'bg-green-500' :
                                'bg-yellow-500'
                              }`}
                              style={{ width: `${impact.impact_magnitude * 100}%` }}
                            />
                          </div>
                          <span className="font-semibold text-slate-800 w-10 text-right">
                            {(impact.impact_magnitude * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-slate-600 font-medium">Confidence:</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500"
                              style={{ width: `${impact.confidence * 100}%` }}
                            />
                          </div>
                          <span className="font-semibold text-slate-800 w-10 text-right">
                            {(impact.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-1 border-t border-slate-200">
                        <span className="text-slate-600 font-medium">Signals:</span>
                        <span className="font-semibold text-slate-800">{impact.signal_count}</span>
                      </div>
                    </div>
                  </div>

                  {/* Right side: Claude-generated summary - 70% */}
                  <div className="flex-[0.7] p-3 bg-white">
                    <div className="text-xs text-slate-500 uppercase font-semibold mb-1.5 tracking-wide">
                      Analysis
                    </div>
                    <p className="text-sm text-slate-700 leading-relaxed">
                      {impact.summary || impact.reasoning}
                    </p>
                  </div>
                </div>
              </div>
            ))}
              </div>
              
              {/* Action Buttons */}
              <div className="mt-4 flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
                <button
                  onClick={async () => {
                    if (onSaveResults && data) {
                      try {
                        await onSaveResults(data);
                      } catch (error) {
                        console.error("Failed to save results:", error);
                        alert("Failed to save results. Please try again.");
                      }
                    }
                  }}
                  disabled={!data || !onSaveResults}
                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Save Results
                </button>
                <button
                  onClick={async () => {
                    if (onGenerateReport && data) {
                      try {
                        await onGenerateReport(data);
                      } catch (error) {
                        console.error("Failed to generate report:", error);
                        alert("Failed to generate report. Please try again.");
                      }
                    }
                  }}
                  disabled={!data || !onGenerateReport}
                  className="rounded-lg bg-slate-900 px-4 py-2 text-xs font-medium text-white hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Generate Report
                </button>
              </div>
            </div>
          </div>
        );



      default:
        return null;
    }
  };

  return (
    <div className="mt-6 rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Pipeline Progress</h3>
        {isRunning && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <div className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
            <span>Analyzing...</span>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {steps.map((step, index) => {
          const isExpanded = expandedSteps.has(step.id);
          const hasDetails = step.detailedData && step.status === "completed";

          return (
            <div key={step.id} className="flex items-start gap-4">
              {/* Step Number & Status Indicator */}
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-semibold transition-all ${
                    step.status === "completed"
                      ? "border-green-500 bg-green-50 text-green-700"
                      : step.status === "running"
                        ? "border-blue-500 bg-blue-50 text-blue-700 animate-pulse"
                        : step.status === "error"
                          ? "border-red-500 bg-red-50 text-red-700"
                          : "border-slate-300 bg-slate-50 text-slate-400"
                  }`}
                >
                  {step.status === "completed" ? (
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={3}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : step.status === "error" ? (
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={3}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  ) : (
                    index + 1
                  )}
                </div>
                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div
                    className={`mt-2 h-8 w-0.5 transition-colors ${
                      step.status === "completed" ? "bg-green-500" : "bg-slate-200"
                    }`}
                  />
                )}
              </div>

              {/* Step Content */}
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4
                    className={`text-sm font-medium transition-colors ${
                      step.status === "completed"
                        ? "text-green-700"
                        : step.status === "running"
                          ? "text-blue-700"
                          : step.status === "error"
                            ? "text-red-700"
                            : "text-slate-500"
                    }`}
                  >
                    {step.name}
                  </h4>
                  <div className="flex items-center gap-2">
                    {step.duration && step.status === "completed" && (
                      <span className="text-xs text-slate-400">{step.duration}ms</span>
                    )}
                    {hasDetails && (
                      <button
                        onClick={() => toggleStep(step.id)}
                        className="text-xs text-blue-600 hover:text-blue-800"
                      >
                        {isExpanded ? "Hide" : "Expand"}
                      </button>
                    )}
                  </div>
                </div>
                <p className="mt-1 text-xs text-slate-600">{step.description}</p>
                {isExpanded && renderStepDetails(step, showAllSignals, setShowAllSignals)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
