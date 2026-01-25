"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { listThemes, updateTheme, createTheme, type Theme, type ThemeCreate } from "@/lib/api/themes";
import {
  getActiveScoringSettings,
  updateScoringSettings,
  type ScoringSettings,
} from "@/lib/api/scoringSettings";

type SettingsTab = "themes" | "scoring";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>("themes");
  const [themes, setThemes] = useState<Theme[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingTheme, setEditingTheme] = useState<string | null>(null);
  const [editedTheme, setEditedTheme] = useState<Partial<Theme> | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showHowThemesDefined, setShowHowThemesDefined] = useState(false);
  const [showAddTheme, setShowAddTheme] = useState(false);
  const [newTheme, setNewTheme] = useState<Partial<Theme>>({
    name: "",
    display_name: "",
    keywords: [],
    relevant_countries: [],
    relevant_regions: [],
    relevant_sectors: [],
    country_match_weight: 0.4,
    region_match_weight: 0.2,
    sector_match_weight: 0.3,
    exposure_bonus_weight: 0.3,
    emerging_market_bonus: 0.1,
    min_relevance_threshold: 0.1,
    is_active: true,
  });

  // Scoring settings state
  const [scoringSettings, setScoringSettings] = useState<ScoringSettings | null>(null);
  const [loadingScoring, setLoadingScoring] = useState(true);
  const [editingScoring, setEditingScoring] = useState(false);
  const [editedScoring, setEditedScoring] = useState<Partial<ScoringSettings>>({});
  const [editingSources, setEditingSources] = useState(false);
  const [newSourceName, setNewSourceName] = useState("");
  const [newSourceScore, setNewSourceScore] = useState(0.7);

  // Load themes from API
  useEffect(() => {
    if (isOpen) {
      loadThemes();
      loadScoringSettings();
    }
  }, [isOpen]);

  const loadThemes = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listThemes(false); // Get all themes, including inactive
      setThemes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load themes");
      console.error("Error loading themes:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditTheme = (theme: Theme) => {
    setEditingTheme(theme.name);
    setEditedTheme({ ...theme });
  };

  const handleCancelEdit = () => {
    setEditingTheme(null);
    setEditedTheme(null);
  };

  const handleSaveTheme = async () => {
    if (!editingTheme || !editedTheme) return;

    try {
      setSaving(true);
      setError(null);
      await updateTheme(editingTheme, editedTheme);
      await loadThemes(); // Reload to get updated data
      setEditingTheme(null);
      setEditedTheme(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save theme");
      console.error("Error saving theme:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleFieldChange = (field: keyof Theme, value: any) => {
    if (!editedTheme) return;
    setEditedTheme({ ...editedTheme, [field]: value });
  };

  const handleArrayFieldChange = (field: keyof Theme, value: string) => {
    if (!editedTheme) return;
    const currentArray = (editedTheme[field] as string[]) || [];
    const newArray = value.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
    setEditedTheme({ ...editedTheme, [field]: newArray });
  };

  const loadScoringSettings = async () => {
    try {
      setLoadingScoring(true);
      setError(null);
      const data = await getActiveScoringSettings();
      setScoringSettings(data);
      setEditedScoring({});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load scoring settings");
      console.error("Error loading scoring settings:", err);
    } finally {
      setLoadingScoring(false);
    }
  };

  const handleEditScoring = () => {
    if (scoringSettings) {
      setEditingScoring(true);
      setEditedScoring({ ...scoringSettings });
    }
  };

  const handleCancelScoringEdit = () => {
    setEditingScoring(false);
    setEditedScoring({});
  };

  const handleSaveScoring = async () => {
    if (!scoringSettings || !scoringSettings.name) return;

    try {
      setSaving(true);
      setError(null);
      await updateScoringSettings(scoringSettings.name, editedScoring);
      await loadScoringSettings();
      setEditingScoring(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save scoring settings");
      console.error("Error saving scoring settings:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleScoringFieldChange = (field: keyof ScoringSettings, value: any) => {
    setEditedScoring({ ...editedScoring, [field]: value });
  };

  const handleScoringDictFieldChange = (
    field: "activity_level_scores" | "source_quality_scores",
    key: string,
    value: number
  ) => {
    const current = (editedScoring[field] as Record<string, number>) || {};
    setEditedScoring({
      ...editedScoring,
      [field]: { ...current, [key]: value },
    });
  };

  const handleAddSource = () => {
    if (!newSourceName.trim()) return;
    
    const current = (editedScoring.source_quality_scores as Record<string, number>) || 
                    (scoringSettings?.source_quality_scores as Record<string, number>) || {};
    
    setEditedScoring({
      ...editedScoring,
      source_quality_scores: { ...current, [newSourceName.trim()]: newSourceScore },
    });
    
    setNewSourceName("");
    setNewSourceScore(0.7);
  };

  const handleDeleteSource = (sourceName: string) => {
    const current = (editedScoring.source_quality_scores as Record<string, number>) || 
                    (scoringSettings?.source_quality_scores as Record<string, number>) || {};
    
    const updated = { ...current };
    delete updated[sourceName];
    
    setEditedScoring({
      ...editedScoring,
      source_quality_scores: updated,
    });
  };

  const handleAddTheme = async () => {
    if (!newTheme.name || !newTheme.display_name || !newTheme.relevant_sectors || newTheme.relevant_sectors.length === 0) {
      setError("Name, display name, and at least one relevant sector are required");
      return;
    }

    try {
      setSaving(true);
      setError(null);
      const themeToCreate: ThemeCreate = {
        name: newTheme.name!,
        display_name: newTheme.display_name!,
        keywords: newTheme.keywords || [],
        relevant_countries: newTheme.relevant_countries || [],
        relevant_regions: newTheme.relevant_regions || [],
        relevant_sectors: newTheme.relevant_sectors || [],
        country_match_weight: newTheme.country_match_weight,
        region_match_weight: newTheme.region_match_weight,
        sector_match_weight: newTheme.sector_match_weight,
        exposure_bonus_weight: newTheme.exposure_bonus_weight,
        emerging_market_bonus: newTheme.emerging_market_bonus,
        min_relevance_threshold: newTheme.min_relevance_threshold,
        is_active: newTheme.is_active,
      };
      await createTheme(themeToCreate);
      await loadThemes();
      setShowAddTheme(false);
      setNewTheme({
        name: "",
        display_name: "",
        keywords: [],
        relevant_countries: [],
        relevant_regions: [],
        relevant_sectors: [],
        country_match_weight: 0.4,
        region_match_weight: 0.2,
        sector_match_weight: 0.3,
        exposure_bonus_weight: 0.3,
        emerging_market_bonus: 0.1,
        min_relevance_threshold: 0.1,
        is_active: true,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create theme");
      console.error("Error creating theme:", err);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const modalContent = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center pointer-events-auto">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm pointer-events-auto"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-[10000] flex h-[80vh] w-[90vw] max-w-6xl rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden pointer-events-auto">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 z-[102] flex h-8 w-8 items-center justify-center rounded-full border border-slate-300 bg-white text-slate-600 transition hover:bg-slate-50 hover:text-slate-900"
          aria-label="Close settings"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Left Navigation - 20% */}
        <div className="w-[20%] border-r border-slate-200 bg-slate-50 p-4">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
            Settings
          </h2>
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab("themes")}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition ${
                activeTab === "themes"
                  ? "bg-slate-900 text-white"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              Themes
            </button>
            <button
              onClick={() => setActiveTab("scoring")}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm font-medium transition ${
                activeTab === "scoring"
                  ? "bg-slate-900 text-white"
                  : "text-slate-700 hover:bg-slate-100"
              }`}
            >
              Scoring
            </button>
          </nav>
        </div>

        {/* Right Content - 80% */}
        <div className="w-[80%] overflow-y-auto p-8">
          {activeTab === "themes" && (
            <div className="space-y-6">
              <div>
                <h3 className="mb-2 text-2xl font-semibold text-slate-900">Themes</h3>
                <p className="text-slate-600 leading-relaxed">
                  Geopolitical themes are predefined categories of risk that help identify
                  relevant geopolitical factors affecting an asset. Each theme represents a
                  specific type of geopolitical risk that can impact investments.
                </p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50">
                <button
                  onClick={() => setShowHowThemesDefined(!showHowThemesDefined)}
                  className="w-full p-4 text-left flex items-center justify-between hover:bg-slate-100 transition"
                >
                  <h4 className="text-sm font-semibold text-slate-900">How Themes Are Defined</h4>
                  <svg
                    className={`h-4 w-4 text-slate-600 transition-transform ${showHowThemesDefined ? "rotate-180" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {showHowThemesDefined && (
                  <div className="p-4 pt-0 space-y-3">
                    <p className="mb-3 text-sm text-slate-600">
                      Each theme is defined by:
                    </p>
                    <ul className="ml-4 list-disc space-y-1 text-sm text-slate-600">
                      <li>
                        <strong>Keywords:</strong> Terms that indicate this theme in intelligence
                        signals and news articles. These are used to match intelligence signals
                        to themes during analysis.
                      </li>
                      <li>
                        <strong>Relevant Countries:</strong> Countries where this theme is
                        historically or commonly observed. If your asset is located in one of
                        these countries, the theme receives a higher relevance score (+0.4).
                        These are countries that have frequently experienced or are particularly
                        vulnerable to this type of geopolitical risk.
                      </li>
                      <li>
                        <strong>Relevant Sectors:</strong> Industry sectors most exposed to this
                        type of risk. If your asset operates in one of these sectors, the theme
                        receives a higher relevance score (+0.3).
                      </li>
                      <li>
                        <strong>Relevant Regions:</strong> (For some themes) Geographic regions
                        where this theme is particularly relevant. If your asset is in one of
                        these regions, the theme receives a moderate relevance score (+0.2).
                      </li>
                    </ul>
                    <p className="mt-3 text-sm text-slate-600">
                      During the GP Health Scan, the system identifies which themes are relevant
                      to your asset based on its country, region, sector, and other characteristics.
                      The relevance score indicates how strongly each theme applies to your
                      specific asset.
                    </p>
                    <p className="mt-2 text-sm text-slate-600">
                      <strong>Customizable Scoring:</strong> You can adjust the scoring weights
                      for each theme to fine-tune how relevance is calculated. Higher weights
                      mean that matching criteria contribute more to the final relevance score.
                    </p>
                  </div>
                )}
              </div>

              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div>
                <div className="mb-4 flex items-center justify-between">
                  <h4 className="text-lg font-semibold text-slate-900">
                    All Available Themes ({loading ? "..." : themes.length})
                  </h4>
                  <div className="flex gap-2">
                    {!loading && themes.length === 0 && (
                      <button
                        onClick={async () => {
                          try {
                            setLoading(true);
                            setError(null);
                            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/themes/seed`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                            });
                            if (!response.ok) {
                              throw new Error("Failed to seed themes");
                            }
                            await loadThemes();
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Failed to seed themes");
                          } finally {
                            setLoading(false);
                          }
                        }}
                        className="rounded-lg border border-green-300 bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100"
                      >
                        Seed Default Themes
                      </button>
                    )}
                    {!loading && (
                      <>
                        <button
                          onClick={() => setShowAddTheme(true)}
                          className="rounded-lg border border-blue-300 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100"
                        >
                          Add
                        </button>
                        <button
                          onClick={loadThemes}
                          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Refresh
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {loading ? (
                  <div className="text-center py-8 text-slate-500">Loading themes...</div>
                ) : (
                  <div className="space-y-4">
                    {themes.map((theme) => {
                      const isEditing = editingTheme === theme.name;
                      const displayTheme = isEditing && editedTheme ? editedTheme : theme;

                      return (
                        <div
                          key={theme.name}
                          className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
                        >
                          <div className="mb-3 flex items-center justify-between">
                            <h5 className="text-base font-semibold text-slate-900">
                              {displayTheme.display_name}
                            </h5>
                            {!isEditing ? (
                              <button
                                onClick={() => handleEditTheme(theme)}
                                className="rounded-lg border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                              >
                                Edit
                              </button>
                            ) : (
                              <div className="flex gap-2">
                                <button
                                  onClick={handleSaveTheme}
                                  disabled={saving}
                                  className="rounded-lg border border-green-300 bg-green-50 px-3 py-1 text-xs font-medium text-green-700 hover:bg-green-100 disabled:opacity-50"
                                >
                                  {saving ? "Saving..." : "Save"}
                                </button>
                                <button
                                  onClick={handleCancelEdit}
                                  disabled={saving}
                                  className="rounded-lg border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                                >
                                  Cancel
                                </button>
                              </div>
                            )}
                          </div>

                          <div className="space-y-3 text-sm">
                            {/* Keywords */}
                            <div>
                              <label className="mb-1 block font-medium text-slate-700">
                                Keywords:
                              </label>
                              {isEditing ? (
                                <input
                                  type="text"
                                  value={(displayTheme.keywords || []).join(", ")}
                                  onChange={(e) => handleArrayFieldChange("keywords", e.target.value)}
                                  className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                                  placeholder="keyword1, keyword2, keyword3"
                                />
                              ) : (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {theme.keywords.map((keyword, idx) => (
                                    <span
                                      key={idx}
                                      className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700"
                                    >
                                      {keyword}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Relevant Countries */}
                            <div>
                              <label className="mb-1 block font-medium text-slate-700">
                                Relevant Countries:
                              </label>
                              {isEditing ? (
                                <input
                                  type="text"
                                  value={(displayTheme.relevant_countries || []).join(", ")}
                                  onChange={(e) => handleArrayFieldChange("relevant_countries", e.target.value)}
                                  className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                                  placeholder="Country1, Country2, Country3"
                                />
                              ) : (
                                <span className="text-slate-600">
                                  {theme.relevant_countries && theme.relevant_countries.length > 0
                                    ? theme.relevant_countries.join(", ")
                                    : "None"}
                                </span>
                              )}
                            </div>

                            {/* Relevant Regions */}
                            <div>
                              <label className="mb-1 block font-medium text-slate-700">
                                Relevant Regions:
                              </label>
                              {isEditing ? (
                                <input
                                  type="text"
                                  value={(displayTheme.relevant_regions || []).join(", ")}
                                  onChange={(e) => handleArrayFieldChange("relevant_regions", e.target.value)}
                                  className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                                  placeholder="Region1, Region2"
                                />
                              ) : (
                                <span className="text-slate-600">
                                  {theme.relevant_regions && theme.relevant_regions.length > 0
                                    ? theme.relevant_regions.join(", ")
                                    : "None"}
                                </span>
                              )}
                            </div>

                            {/* Relevant Sectors */}
                            <div>
                              <label className="mb-1 block font-medium text-slate-700">
                                Relevant Sectors:
                              </label>
                              {isEditing ? (
                                <input
                                  type="text"
                                  value={(displayTheme.relevant_sectors || []).join(", ")}
                                  onChange={(e) => handleArrayFieldChange("relevant_sectors", e.target.value)}
                                  className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                                  placeholder="Sector1, Sector2, Sector3"
                                />
                              ) : (
                                <span className="text-slate-600">
                                  {theme.relevant_sectors.join(", ")}
                                </span>
                              )}
                            </div>

                            {/* Scoring Weights */}
                            {isEditing && (
                              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
                                <h6 className="mb-2 text-xs font-semibold text-slate-900">
                                  Scoring Weights (0.0 - 1.0)
                                </h6>
                                <div className="grid grid-cols-2 gap-3 text-xs">
                                  <div>
                                    <label className="block font-medium text-slate-700">
                                      Country Match:
                                    </label>
                                    <input
                                      type="number"
                                      min="0"
                                      max="1"
                                      step="0.1"
                                      value={displayTheme.country_match_weight || 0.4}
                                      onChange={(e) =>
                                        handleFieldChange("country_match_weight", parseFloat(e.target.value))
                                      }
                                      className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                                    />
                                  </div>
                                  <div>
                                    <label className="block font-medium text-slate-700">
                                      Region Match:
                                    </label>
                                    <input
                                      type="number"
                                      min="0"
                                      max="1"
                                      step="0.1"
                                      value={displayTheme.region_match_weight || 0.2}
                                      onChange={(e) =>
                                        handleFieldChange("region_match_weight", parseFloat(e.target.value))
                                      }
                                      className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                                    />
                                  </div>
                                  <div>
                                    <label className="block font-medium text-slate-700">
                                      Sector Match:
                                    </label>
                                    <input
                                      type="number"
                                      min="0"
                                      max="1"
                                      step="0.1"
                                      value={displayTheme.sector_match_weight || 0.3}
                                      onChange={(e) =>
                                        handleFieldChange("sector_match_weight", parseFloat(e.target.value))
                                      }
                                      className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                                    />
                                  </div>
                                  <div>
                                    <label className="block font-medium text-slate-700">
                                      Exposure Bonus:
                                    </label>
                                    <input
                                      type="number"
                                      min="0"
                                      max="1"
                                      step="0.1"
                                      value={displayTheme.exposure_bonus_weight || 0.3}
                                      onChange={(e) =>
                                        handleFieldChange("exposure_bonus_weight", parseFloat(e.target.value))
                                      }
                                      className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                                    />
                                  </div>
                                  <div>
                                    <label className="block font-medium text-slate-700">
                                      Emerging Market Bonus:
                                    </label>
                                    <input
                                      type="number"
                                      min="0"
                                      max="1"
                                      step="0.1"
                                      value={displayTheme.emerging_market_bonus || 0.1}
                                      onChange={(e) =>
                                        handleFieldChange("emerging_market_bonus", parseFloat(e.target.value))
                                      }
                                      className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                                    />
                                  </div>
                                  <div>
                                    <label className="block font-medium text-slate-700">
                                      Min Relevance Threshold:
                                    </label>
                                    <input
                                      type="number"
                                      min="0"
                                      max="1"
                                      step="0.05"
                                      value={displayTheme.min_relevance_threshold || 0.1}
                                      onChange={(e) =>
                                        handleFieldChange("min_relevance_threshold", parseFloat(e.target.value))
                                      }
                                      className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                                    />
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Add Theme Form */}
                {showAddTheme && (
                  <div className="mt-6 rounded-lg border-2 border-blue-200 bg-blue-50 p-4">
                    <div className="mb-3 flex items-center justify-between">
                      <h5 className="text-base font-semibold text-slate-900">Create New Theme</h5>
                      <button
                        onClick={() => {
                          setShowAddTheme(false);
                          setError(null);
                        }}
                        className="rounded-lg border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                      >
                        Cancel
                      </button>
                    </div>

                    <div className="space-y-3 text-sm">
                      {/* Name */}
                      <div>
                        <label className="mb-1 block font-medium text-slate-700">
                          Name (identifier): <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={newTheme.name || ""}
                          onChange={(e) => setNewTheme({ ...newTheme, name: e.target.value })}
                          className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                          placeholder="e.g., cyber_security"
                        />
                      </div>

                      {/* Display Name */}
                      <div>
                        <label className="mb-1 block font-medium text-slate-700">
                          Display Name: <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={newTheme.display_name || ""}
                          onChange={(e) => setNewTheme({ ...newTheme, display_name: e.target.value })}
                          className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                          placeholder="e.g., Cyber Security"
                        />
                      </div>

                      {/* Keywords */}
                      <div>
                        <label className="mb-1 block font-medium text-slate-700">Keywords:</label>
                        <input
                          type="text"
                          value={(newTheme.keywords || []).join(", ")}
                          onChange={(e) => {
                            const keywords = e.target.value.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
                            setNewTheme({ ...newTheme, keywords });
                          }}
                          className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                          placeholder="keyword1, keyword2, keyword3"
                        />
                      </div>

                      {/* Relevant Countries */}
                      <div>
                        <label className="mb-1 block font-medium text-slate-700">Relevant Countries:</label>
                        <input
                          type="text"
                          value={(newTheme.relevant_countries || []).join(", ")}
                          onChange={(e) => {
                            const countries = e.target.value.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
                            setNewTheme({ ...newTheme, relevant_countries: countries });
                          }}
                          className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                          placeholder="Country1, Country2, Country3"
                        />
                      </div>

                      {/* Relevant Regions */}
                      <div>
                        <label className="mb-1 block font-medium text-slate-700">Relevant Regions:</label>
                        <input
                          type="text"
                          value={(newTheme.relevant_regions || []).join(", ")}
                          onChange={(e) => {
                            const regions = e.target.value.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
                            setNewTheme({ ...newTheme, relevant_regions: regions });
                          }}
                          className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                          placeholder="Region1, Region2"
                        />
                      </div>

                      {/* Relevant Sectors */}
                      <div>
                        <label className="mb-1 block font-medium text-slate-700">
                          Relevant Sectors: <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={(newTheme.relevant_sectors || []).join(", ")}
                          onChange={(e) => {
                            const sectors = e.target.value.split(",").map((s) => s.trim()).filter((s) => s.length > 0);
                            setNewTheme({ ...newTheme, relevant_sectors: sectors });
                          }}
                          className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                          placeholder="Sector1, Sector2, Sector3"
                        />
                      </div>

                      {/* Scoring Weights */}
                      <div className="mt-4 rounded-lg border border-slate-200 bg-white p-3">
                        <h6 className="mb-2 text-xs font-semibold text-slate-900">
                          Scoring Weights (0.0 - 1.0)
                        </h6>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <label className="block font-medium text-slate-700">Country Match:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={newTheme.country_match_weight || 0.4}
                              onChange={(e) => setNewTheme({ ...newTheme, country_match_weight: parseFloat(e.target.value) })}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Region Match:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={newTheme.region_match_weight || 0.2}
                              onChange={(e) => setNewTheme({ ...newTheme, region_match_weight: parseFloat(e.target.value) })}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Sector Match:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={newTheme.sector_match_weight || 0.3}
                              onChange={(e) => setNewTheme({ ...newTheme, sector_match_weight: parseFloat(e.target.value) })}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Exposure Bonus:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={newTheme.exposure_bonus_weight || 0.3}
                              onChange={(e) => setNewTheme({ ...newTheme, exposure_bonus_weight: parseFloat(e.target.value) })}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Emerging Market Bonus:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={newTheme.emerging_market_bonus || 0.1}
                              onChange={(e) => setNewTheme({ ...newTheme, emerging_market_bonus: parseFloat(e.target.value) })}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Min Relevance Threshold:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.05"
                              value={newTheme.min_relevance_threshold || 0.1}
                              onChange={(e) => setNewTheme({ ...newTheme, min_relevance_threshold: parseFloat(e.target.value) })}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="flex justify-end gap-2 pt-2">
                        <button
                          onClick={() => {
                            setShowAddTheme(false);
                            setError(null);
                          }}
                          disabled={saving}
                          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleAddTheme}
                          disabled={saving}
                          className="rounded-lg border border-green-300 bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100 disabled:opacity-50"
                        >
                          {saving ? "Creating..." : "Create Theme"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "scoring" && (
            <div className="space-y-6">
              <div>
                <h3 className="mb-2 text-2xl font-semibold text-slate-900">Scoring Settings</h3>
                <p className="text-slate-600 leading-relaxed">
                  Configure how intelligence signals are scored and filtered. These settings control
                  the weights, thresholds, and parameters used throughout the intelligence retrieval pipeline.
                </p>
              </div>

              {loadingScoring ? (
                <div className="text-center py-8 text-slate-500">Loading scoring settings...</div>
              ) : scoringSettings ? (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <h4 className="text-lg font-semibold text-slate-900">
                      {scoringSettings.name} Settings
                    </h4>
                    {!editingScoring && (
                      <button
                        onClick={handleEditScoring}
                        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                      >
                        Edit
                      </button>
                    )}
                  </div>

                  {editingScoring ? (
                    <div className="space-y-6">
                      {/* Scoring Weights */}
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                        <h5 className="mb-3 text-sm font-semibold text-slate-900">
                          Scoring Weights (should sum to 1.0)
                        </h5>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <label className="block font-medium text-slate-700">Base Relevance:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.05"
                              value={editedScoring.weight_base_relevance ?? scoringSettings.weight_base_relevance}
                              onChange={(e) => handleScoringFieldChange("weight_base_relevance", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Theme Match:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.05"
                              value={editedScoring.weight_theme_match ?? scoringSettings.weight_theme_match}
                              onChange={(e) => handleScoringFieldChange("weight_theme_match", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Recency:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.05"
                              value={editedScoring.weight_recency ?? scoringSettings.weight_recency}
                              onChange={(e) => handleScoringFieldChange("weight_recency", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Source Quality:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.05"
                              value={editedScoring.weight_source_quality ?? scoringSettings.weight_source_quality}
                              onChange={(e) => handleScoringFieldChange("weight_source_quality", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Activity Level:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.05"
                              value={editedScoring.weight_activity_level ?? scoringSettings.weight_activity_level}
                              onChange={(e) => handleScoringFieldChange("weight_activity_level", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Recency Decay */}
                      <div className="rounded-lg border border-slate-200 bg-white p-4">
                        <h5 className="mb-3 text-sm font-semibold text-slate-900">Recency Decay</h5>
                        <div className="text-xs">
                          <label className="block font-medium text-slate-700 mb-1">
                            Decay Constant (higher = slower decay):
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="100"
                            step="1"
                            value={editedScoring.recency_decay_constant ?? scoringSettings.recency_decay_constant}
                            onChange={(e) => handleScoringFieldChange("recency_decay_constant", parseFloat(e.target.value))}
                            className="w-full rounded border border-slate-300 px-2 py-1"
                          />
                          <p className="mt-1 text-slate-500">
                            Default: 30.0 (half-life ~21 days)
                          </p>
                        </div>
                      </div>

                      {/* Base Relevance Scores */}
                      <div className="rounded-lg border border-slate-200 bg-white p-4">
                        <h5 className="mb-3 text-sm font-semibold text-slate-900">Base Relevance Scores</h5>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <label className="block font-medium text-slate-700">Country Exact Match:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={editedScoring.score_country_exact_match ?? scoringSettings.score_country_exact_match}
                              onChange={(e) => handleScoringFieldChange("score_country_exact_match", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Country Partial Match:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={editedScoring.score_country_partial_match ?? scoringSettings.score_country_partial_match}
                              onChange={(e) => handleScoringFieldChange("score_country_partial_match", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Region Match:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={editedScoring.score_region_match ?? scoringSettings.score_region_match}
                              onChange={(e) => handleScoringFieldChange("score_region_match", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Sector Match:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={editedScoring.score_sector_match ?? scoringSettings.score_sector_match}
                              onChange={(e) => handleScoringFieldChange("score_sector_match", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Thresholds */}
                      <div className="rounded-lg border border-slate-200 bg-white p-4">
                        <h5 className="mb-3 text-sm font-semibold text-slate-900">Thresholds</h5>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <label className="block font-medium text-slate-700">Semantic Threshold:</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.05"
                              value={editedScoring.semantic_threshold ?? scoringSettings.semantic_threshold}
                              onChange={(e) => handleScoringFieldChange("semantic_threshold", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Relevance Threshold (Low):</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.01"
                              value={editedScoring.relevance_threshold_low ?? scoringSettings.relevance_threshold_low}
                              onChange={(e) => handleScoringFieldChange("relevance_threshold_low", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Relevance Threshold (High):</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.01"
                              value={editedScoring.relevance_threshold_high ?? scoringSettings.relevance_threshold_high}
                              onChange={(e) => handleScoringFieldChange("relevance_threshold_high", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Theme Threshold (Web):</label>
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.05"
                              value={editedScoring.theme_relevance_threshold_web ?? scoringSettings.theme_relevance_threshold_web}
                              onChange={(e) => handleScoringFieldChange("theme_relevance_threshold_web", parseFloat(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Pipeline Parameters */}
                      <div className="rounded-lg border border-slate-200 bg-white p-4">
                        <h5 className="mb-3 text-sm font-semibold text-slate-900">Pipeline Parameters</h5>
                        <div className="grid grid-cols-3 gap-3 text-xs">
                          <div>
                            <label className="block font-medium text-slate-700">Days Lookback:</label>
                            <input
                              type="number"
                              min="1"
                              max="365"
                              step="1"
                              value={editedScoring.days_lookback_default ?? scoringSettings.days_lookback_default}
                              onChange={(e) => handleScoringFieldChange("days_lookback_default", parseInt(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Max Signals:</label>
                            <input
                              type="number"
                              min="1"
                              max="100"
                              step="1"
                              value={editedScoring.max_signals_default ?? scoringSettings.max_signals_default}
                              onChange={(e) => handleScoringFieldChange("max_signals_default", parseInt(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                          <div>
                            <label className="block font-medium text-slate-700">Max Events/Snapshot:</label>
                            <input
                              type="number"
                              min="1"
                              max="10"
                              step="1"
                              value={editedScoring.max_events_per_snapshot ?? scoringSettings.max_events_per_snapshot}
                              onChange={(e) => handleScoringFieldChange("max_events_per_snapshot", parseInt(e.target.value))}
                              className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Semantic Filtering */}
                      <div className="rounded-lg border border-slate-200 bg-white p-4">
                        <h5 className="mb-3 text-sm font-semibold text-slate-900">Semantic Filtering</h5>
                        <div className="text-xs">
                          <label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={editedScoring.use_semantic_filtering ?? scoringSettings.use_semantic_filtering}
                              onChange={(e) => handleScoringFieldChange("use_semantic_filtering", e.target.checked)}
                              className="rounded border-slate-300"
                            />
                            <span className="font-medium text-slate-700">Enable Claude Semantic Filtering</span>
                          </label>
                        </div>
                      </div>

                      {/* Activity Level Scores */}
                      <div className="rounded-lg border border-slate-200 bg-white p-4">
                        <h5 className="mb-3 text-sm font-semibold text-slate-900">Activity Level Scores</h5>
                        <div className="grid grid-cols-3 gap-3 text-xs">
                          {Object.entries(editedScoring.activity_level_scores || scoringSettings.activity_level_scores).map(([level, score]) => (
                            <div key={level}>
                              <label className="block font-medium text-slate-700">{level}:</label>
                              <input
                                type="number"
                                min="0"
                                max="1"
                                step="0.1"
                                value={typeof score === 'number' ? score : 0}
                                onChange={(e) => handleScoringDictFieldChange("activity_level_scores", level, parseFloat(e.target.value))}
                                className="mt-1 w-full rounded border border-slate-300 px-2 py-1"
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Source Quality Scores */}
                      <div className="rounded-lg border border-slate-200 bg-white p-4">
                        <div className="mb-3 flex items-center justify-between">
                          <h5 className="text-sm font-semibold text-slate-900">Source Quality Scores</h5>
                          <button
                            type="button"
                            onClick={() => setEditingSources(!editingSources)}
                            className="rounded border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
                          >
                            {editingSources ? "Done Editing" : "Edit Sources"}
                          </button>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-3 text-xs max-h-96 overflow-y-auto">
                          {Object.entries(editedScoring.source_quality_scores || scoringSettings.source_quality_scores).map(([source, score]) => (
                            <div key={source} className="relative">
                              <label className="block font-medium text-slate-700">{source}:</label>
                              <div className="flex items-center gap-2">
                                <input
                                  type="number"
                                  min="0"
                                  max="1"
                                  step="0.05"
                                  value={typeof score === 'number' ? score : 0}
                                  onChange={(e) => handleScoringDictFieldChange("source_quality_scores", source, parseFloat(e.target.value))}
                                  className="mt-1 flex-1 rounded border border-slate-300 px-2 py-1"
                                />
                                {editingSources && source !== "default" && (
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteSource(source)}
                                    className="mt-1 rounded border border-red-300 bg-red-50 px-2 py-1 text-[10px] font-medium text-red-700 hover:bg-red-100 transition-colors"
                                    title="Delete source"
                                  >
                                    ×
                                  </button>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        {/* Add New Source */}
                        {editingSources && (
                          <div className="mt-4 rounded-lg border border-slate-300 bg-slate-50 p-3">
                            <h6 className="mb-2 text-xs font-semibold text-slate-900">Add New Source</h6>
                            <div className="flex items-end gap-2">
                              <div className="flex-1">
                                <label className="block text-[10px] font-medium text-slate-700 mb-1">Source Name:</label>
                                <input
                                  type="text"
                                  value={newSourceName}
                                  onChange={(e) => setNewSourceName(e.target.value)}
                                  placeholder="e.g., CNN"
                                  className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                      e.preventDefault();
                                      handleAddSource();
                                    }
                                  }}
                                />
                              </div>
                              <div className="w-20">
                                <label className="block text-[10px] font-medium text-slate-700 mb-1">Score:</label>
                                <input
                                  type="number"
                                  min="0"
                                  max="1"
                                  step="0.05"
                                  value={newSourceScore}
                                  onChange={(e) => setNewSourceScore(parseFloat(e.target.value))}
                                  className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                                />
                              </div>
                              <button
                                type="button"
                                onClick={handleAddSource}
                                disabled={!newSourceName.trim()}
                                className="rounded border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                Add
                              </button>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="flex justify-end gap-2 pt-2">
                        <button
                          onClick={handleCancelScoringEdit}
                          disabled={saving}
                          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleSaveScoring}
                          disabled={saving}
                          className="rounded-lg border border-green-300 bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100 disabled:opacity-50"
                        >
                          {saving ? "Saving..." : "Save Settings"}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4 text-sm">
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                        <h5 className="mb-2 text-sm font-semibold text-slate-900">Scoring Weights</h5>
                        <div className="space-y-1 text-xs text-slate-600">
                          <div>Base Relevance: {scoringSettings.weight_base_relevance}</div>
                          <div>Theme Match: {scoringSettings.weight_theme_match}</div>
                          <div>Recency: {scoringSettings.weight_recency}</div>
                          <div>Source Quality: {scoringSettings.weight_source_quality}</div>
                          <div>Activity Level: {scoringSettings.weight_activity_level}</div>
                        </div>
                      </div>
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                        <h5 className="mb-2 text-sm font-semibold text-slate-900">Thresholds</h5>
                        <div className="space-y-1 text-xs text-slate-600">
                          <div>Semantic: {scoringSettings.semantic_threshold}</div>
                          <div>Relevance (Low): {scoringSettings.relevance_threshold_low}</div>
                          <div>Relevance (High): {scoringSettings.relevance_threshold_high}</div>
                          <div>Theme (Web): {scoringSettings.theme_relevance_threshold_web}</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">No scoring settings found</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Render modal using portal at document body level
  if (typeof window !== "undefined") {
    return createPortal(modalContent, document.body);
  }
  return null;
}
