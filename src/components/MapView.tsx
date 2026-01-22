"use client";

import maplibregl from "maplibre-gl";
import { useEffect, useRef } from "react";

type MapViewProps = {
  onHoverCountry?: (countryName: string | null) => void;
  onHoverPosition?: (position: { x: number; y: number } | null) => void;
  onSelectCountry?: (countryName: string | null) => void;
  onHoverPin?: (pin: NewsPin | null) => void;
  showLabels?: boolean;
  showCapitals?: boolean;
  showAirTraffic?: boolean;
  useGlobe?: boolean;
  issPosition?: IssPosition | null;
  airTraffic?: AirTrafficPoint[];
  pins?: NewsPin[];
};

export type NewsPin = {
  id: string;
  countryName: string;
  countryId?: string;
  title: string;
  summary: string;
  updatedAt: string;
  source: string;
  url: string;
  severity: number;
  count: number;
};

export type AirTrafficPoint = {
  id: string;
  longitude: number;
  latitude: number;
  velocity?: number | null;
};

export type IssPosition = {
  latitude: number;
  longitude: number;
  timestamp?: number;
};

export default function MapView({
  onHoverCountry,
  onHoverPosition,
  onSelectCountry,
  onHoverPin,
  showLabels = true,
  showCapitals = true,
  showAirTraffic = false,
  useGlobe = false,
  issPosition = null,
  airTraffic = [],
  pins = [],
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const hoveredIdRef = useRef<string | number | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const centroidRef = useRef<Record<string, [number, number]>>({});

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    mapRef.current = new maplibregl.Map({
      container: containerRef.current,
      style: "/map-style.json",
      center: [12, 18],
      zoom: useGlobe ? 2.1 : 1.35,
      minZoom: 1,
      maxZoom: 5,
      projection: useGlobe ? "globe" : "mercator",
      attributionControl: false,
    });


    mapRef.current.on("load", async () => {
      try {
        applyProjection(mapRef.current, useGlobe);
        const [countriesResponse, capitalsResponse] = await Promise.all([
          fetch("/countries.geojson"),
          fetch("/capitals.geojson"),
        ]);
        const data = await countriesResponse.json();
        const capitals = await capitalsResponse.json();
        const graticule = buildGraticule();
        const oceanLabels = buildOceanLabels();
        const countryLabels = buildCountryLabels(data);

        if (!mapRef.current?.getSource("country-borders")) {
          mapRef.current?.addSource("country-borders", {
            type: "geojson",
            data,
            promoteId: "name",
          });
        }

        if (!mapRef.current?.getLayer("country-fills")) {
          mapRef.current?.addLayer({
            id: "country-fills",
            type: "fill",
            source: "country-borders",
            paint: {
              "fill-color": [
                "case",
                ["boolean", ["feature-state", "hover"], false],
                "#f5f2e9",
                "#101010",
              ],
              "fill-opacity": [
                "case",
                ["boolean", ["feature-state", "hover"], false],
                0.18,
                0.45,
              ],
            },
          });
        }

        if (!mapRef.current?.getLayer("country-borders")) {
          mapRef.current?.addLayer({
            id: "country-borders",
            type: "line",
            source: "country-borders",
            paint: {
              "line-color": "#f5f5f5",
              "line-width": [
                "interpolate",
                ["linear"],
                ["zoom"],
                0.8,
                0.4,
                2.5,
                1.1,
                4,
                1.8,
              ],
              "line-opacity": 0.9,
            },
          });
        }

        if (!mapRef.current?.getSource("graticule")) {
          mapRef.current?.addSource("graticule", {
            type: "geojson",
            data: graticule,
          });
        }

        if (!mapRef.current?.getLayer("graticule-lines")) {
          mapRef.current?.addLayer({
            id: "graticule-lines",
            type: "line",
            source: "graticule",
            paint: {
              "line-color": "rgba(255,255,255,0.08)",
              "line-width": 0.6,
            },
          });
        }

        if (!mapRef.current?.getSource("country-labels")) {
          mapRef.current?.addSource("country-labels", {
            type: "geojson",
            data: countryLabels,
          });
        }

        if (!mapRef.current?.getLayer("country-labels")) {
          mapRef.current?.addLayer({
            id: "country-labels",
            type: "symbol",
            source: "country-labels",
            layout: {
              "text-field": ["get", "name"],
              "text-size": [
                "interpolate",
                ["linear"],
                ["zoom"],
                1,
                9,
                3,
                12,
              ],
              "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
              "text-transform": "uppercase",
              "text-letter-spacing": 0.12,
              "text-allow-overlap": false,
            },
            paint: {
              "text-color": "rgba(255,255,255,0.55)",
              "text-halo-color": "rgba(0,0,0,0.4)",
              "text-halo-width": 0.8,
            },
          });
        }

        if (!mapRef.current?.getSource("ocean-labels")) {
          mapRef.current?.addSource("ocean-labels", {
            type: "geojson",
            data: oceanLabels,
          });
        }

        if (!mapRef.current?.getLayer("ocean-labels")) {
          mapRef.current?.addLayer({
            id: "ocean-labels",
            type: "symbol",
            source: "ocean-labels",
            layout: {
              "text-field": ["get", "name"],
              "text-size": [
                "interpolate",
                ["linear"],
                ["zoom"],
                1,
                11,
                3,
                16,
              ],
              "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
              "text-letter-spacing": 0.18,
              "text-transform": "uppercase",
            },
            paint: {
              "text-color": "rgba(255,255,255,0.35)",
              "text-halo-color": "rgba(0,0,0,0.5)",
              "text-halo-width": 1,
            },
          });
        }

        if (!mapRef.current?.getSource("capital-labels")) {
          mapRef.current?.addSource("capital-labels", {
            type: "geojson",
            data: capitals,
          });
        }

        if (!mapRef.current?.getLayer("capital-labels")) {
          mapRef.current?.addLayer({
            id: "capital-labels",
            type: "symbol",
            source: "capital-labels",
            layout: {
              "text-field": ["get", "capital"],
              "text-size": [
                "interpolate",
                ["linear"],
                ["zoom"],
                1,
                9,
                3,
                12,
              ],
              "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
              "text-letter-spacing": 0.12,
              "text-transform": "uppercase",
              "text-offset": [0, 0.9],
              "text-anchor": "top",
            },
            paint: {
              "text-color": "rgba(255,255,255,0.75)",
              "text-halo-color": "rgba(0,0,0,0.5)",
              "text-halo-width": 1,
            },
          });
        }

        if (!mapRef.current?.getLayer("capital-dots")) {
          mapRef.current?.addLayer({
            id: "capital-dots",
            type: "circle",
            source: "capital-labels",
            paint: {
              "circle-radius": 2.5,
              "circle-color": "rgba(255,255,255,0.7)",
              "circle-stroke-color": "rgba(0,0,0,0.6)",
              "circle-stroke-width": 1,
            },
          });
        }

        centroidRef.current = buildCountryCentroids(data);
        ensurePinsLayers(mapRef.current);
        updatePinsSource(mapRef.current, centroidRef.current, pins);
        ensureAirTrafficLayers(mapRef.current);
        updateAirTrafficSource(mapRef.current, airTraffic);
        ensureIssLayer(mapRef.current);
        updateIssSource(mapRef.current, issPosition);

        const airVisibility = showAirTraffic ? "visible" : "none";
        mapRef.current?.setLayoutProperty("air-traffic-heat", "visibility", airVisibility);
        mapRef.current?.setLayoutProperty("air-traffic-points", "visibility", airVisibility);

        const labelVisibility = showLabels ? "visible" : "none";
        mapRef.current?.setLayoutProperty("country-labels", "visibility", labelVisibility);
        mapRef.current?.setLayoutProperty("ocean-labels", "visibility", labelVisibility);

        const capitalVisibility = showCapitals ? "visible" : "none";
        mapRef.current?.setLayoutProperty("capital-labels", "visibility", capitalVisibility);
        mapRef.current?.setLayoutProperty("capital-dots", "visibility", capitalVisibility);

        mapRef.current?.on("mousemove", "country-fills", (event) => {
          const feature = event.features?.[0];
          if (!feature) {
            return;
          }

          const nextId = feature.id as string | number | null;
          if (hoveredIdRef.current && hoveredIdRef.current !== nextId) {
            mapRef.current?.setFeatureState(
              { source: "country-borders", id: hoveredIdRef.current },
              { hover: false },
            );
          }

          if (nextId) {
            hoveredIdRef.current = nextId;
            mapRef.current?.setFeatureState(
              { source: "country-borders", id: nextId },
              { hover: true },
            );
          }

          const countryId = getCountryId(feature.properties);
          onHoverCountry?.(countryId);
          onHoverPosition?.({ x: event.point.x, y: event.point.y });
          onHoverPin?.(null);
        });

        mapRef.current?.on("click", "country-fills", (event) => {
          const feature = event.features?.[0];
          const countryId = getCountryId(feature?.properties);
          onSelectCountry?.(countryId);
        });

        mapRef.current?.on("click", (event) => {
          const features =
            mapRef.current?.queryRenderedFeatures(event.point, {
              layers: ["country-fills"],
            }) ?? [];
          if (features.length === 0) {
            onSelectCountry?.(null);
          }
        });

        mapRef.current?.on("mouseenter", "country-fills", () => {
          if (mapRef.current) {
            mapRef.current.getCanvas().style.cursor = "pointer";
          }
        });

        mapRef.current?.on("mouseleave", "country-fills", () => {
          if (mapRef.current) {
            mapRef.current.getCanvas().style.cursor = "";
          }
          if (hoveredIdRef.current) {
            mapRef.current?.setFeatureState(
              { source: "country-borders", id: hoveredIdRef.current },
              { hover: false },
            );
          }
          hoveredIdRef.current = null;
          onHoverCountry?.(null);
          onHoverPosition?.(null);
        });

        mapRef.current?.on("mouseenter", "news-pins", (event) => {
          if (mapRef.current) {
            mapRef.current.getCanvas().style.cursor = "pointer";
          }
          const feature = event.features?.[0];
          const pin = coercePin(feature?.properties);
          if (pin) {
            onHoverPin?.(pin);
            onHoverPosition?.({ x: event.point.x, y: event.point.y });
            onHoverCountry?.(null);
          }
        });

        mapRef.current?.on("mouseleave", "news-pins", () => {
          if (mapRef.current) {
            mapRef.current.getCanvas().style.cursor = "";
          }
          onHoverPin?.(null);
        });

        mapRef.current?.on("mousemove", "news-pins", (event) => {
          const feature = event.features?.[0];
          const pin = coercePin(feature?.properties);
          if (pin) {
            onHoverPin?.(pin);
            onHoverPosition?.({ x: event.point.x, y: event.point.y });
            onHoverCountry?.(null);
          }
        });

        const showPopup = (event: maplibregl.MapMouseEvent, html: string) => {
          if (!mapRef.current) {
            return;
          }
          if (!popupRef.current) {
            popupRef.current = new maplibregl.Popup({
              closeButton: false,
              closeOnClick: false,
              offset: [0, -8],
            });
          }
          popupRef.current.setLngLat(event.lngLat).setHTML(html).addTo(mapRef.current);
        };

        const clearPopup = () => {
          popupRef.current?.remove();
        };

        mapRef.current?.on("mouseenter", "country-labels", (event) => {
          if (mapRef.current) {
            mapRef.current.getCanvas().style.cursor = "pointer";
          }
          const name = event.features?.[0]?.properties?.name as string | undefined;
          if (name) {
            showPopup(event, `<div style="font-size:12px">Country: ${name}</div>`);
          }
        });

        mapRef.current?.on("mouseleave", "country-labels", () => {
          if (mapRef.current) {
            mapRef.current.getCanvas().style.cursor = "";
          }
          clearPopup();
        });

        mapRef.current?.on("mouseenter", "capital-labels", (event) => {
          if (mapRef.current) {
            mapRef.current.getCanvas().style.cursor = "pointer";
          }
          const capital = event.features?.[0]?.properties?.capital as string | undefined;
          const country = event.features?.[0]?.properties?.country as string | undefined;
          if (capital) {
            const label = country ? `${capital} — ${country}` : capital;
            showPopup(event, `<div style="font-size:12px">Capital: ${label}</div>`);
          }
        });

        mapRef.current?.on("mouseleave", "capital-labels", () => {
          if (mapRef.current) {
            mapRef.current.getCanvas().style.cursor = "";
          }
          clearPopup();
        });

      } catch (error) {
        console.error("Failed to load country borders", error);
      }
    });

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) {
      return;
    }
    const map = mapRef.current;
    if (map.isStyleLoaded()) {
      applyProjection(map, useGlobe);
    } else {
      map.once("load", () => applyProjection(map, useGlobe));
    }
  }, [useGlobe]);

  useEffect(() => {
    if (!mapRef.current || !mapRef.current.getSource("country-borders")) {
      return;
    }
    updatePinsSource(mapRef.current, centroidRef.current, pins);
  }, [pins]);

  useEffect(() => {
    if (!mapRef.current) {
      return;
    }
    updateAirTrafficSource(mapRef.current, airTraffic);
  }, [airTraffic]);

  useEffect(() => {
    if (!mapRef.current) {
      return;
    }
    updateIssSource(mapRef.current, issPosition);
  }, [issPosition]);

  useEffect(() => {
    if (!mapRef.current) {
      return;
    }
    const visibility = showAirTraffic ? "visible" : "none";
    if (mapRef.current.getLayer("air-traffic-heat")) {
      mapRef.current.setLayoutProperty("air-traffic-heat", "visibility", visibility);
    }
    if (mapRef.current.getLayer("air-traffic-points")) {
      mapRef.current.setLayoutProperty("air-traffic-points", "visibility", visibility);
    }
  }, [showAirTraffic]);

  useEffect(() => {
    if (!mapRef.current) {
      return;
    }
    const visibility = showLabels ? "visible" : "none";
    if (mapRef.current.getLayer("country-labels")) {
      mapRef.current.setLayoutProperty("country-labels", "visibility", visibility);
    }
    if (mapRef.current.getLayer("ocean-labels")) {
      mapRef.current.setLayoutProperty("ocean-labels", "visibility", visibility);
    }
  }, [showLabels]);

  useEffect(() => {
    if (!mapRef.current) {
      return;
    }
    const visibility = showCapitals ? "visible" : "none";
    if (mapRef.current.getLayer("capital-labels")) {
      mapRef.current.setLayoutProperty("capital-labels", "visibility", visibility);
    }
    if (mapRef.current.getLayer("capital-dots")) {
      mapRef.current.setLayoutProperty("capital-dots", "visibility", visibility);
    }
  }, [showCapitals]);

  return <div ref={containerRef} className="h-full w-full" />;
}

function applyProjection(map: maplibregl.Map, useGlobe: boolean) {
  if ("setProjection" in map) {
    map.setProjection({ type: useGlobe ? "globe" : "mercator" });
  }
  if (useGlobe && map.getZoom() < 2.1) {
    map.easeTo({ zoom: 3.5, duration: 800 });
  }
  if ("setFog" in map) {
    if (useGlobe) {
      map.setFog({
        range: [0.5, 8],
        color: "rgba(20, 20, 20, 0.55)",
        "high-color": "rgba(8, 8, 10, 0.9)",
        "horizon-blend": 0.15,
        "space-color": "rgba(0, 0, 0, 0.95)",
        "star-intensity": 0.25,
      });
    } else {
      map.setFog();
    }
  }
}

function buildGraticule() {
  const features = [];
  for (let lat = -80; lat <= 80; lat += 10) {
    const coords = [];
    for (let lon = -180; lon <= 180; lon += 5) {
      coords.push([lon, lat]);
    }
    features.push({
      type: "Feature",
      geometry: { type: "LineString", coordinates: coords },
      properties: { kind: "lat" },
    });
  }
  for (let lon = -180; lon <= 180; lon += 10) {
    const coords = [];
    for (let lat = -85; lat <= 85; lat += 5) {
      coords.push([lon, lat]);
    }
    features.push({
      type: "Feature",
      geometry: { type: "LineString", coordinates: coords },
      properties: { kind: "lon" },
    });
  }
  return { type: "FeatureCollection", features };
}

function buildOceanLabels() {
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: { type: "Point", coordinates: [-150, 5] },
        properties: { name: "Pacific Ocean" },
      },
      {
        type: "Feature",
        geometry: { type: "Point", coordinates: [-30, 0] },
        properties: { name: "Atlantic Ocean" },
      },
      {
        type: "Feature",
        geometry: { type: "Point", coordinates: [80, -20] },
        properties: { name: "Indian Ocean" },
      },
      {
        type: "Feature",
        geometry: { type: "Point", coordinates: [160, 45] },
        properties: { name: "North Pacific" },
      },
      {
        type: "Feature",
        geometry: { type: "Point", coordinates: [10, 60] },
        properties: { name: "Arctic Ocean" },
      },
    ],
  };
}

function buildCountryLabels(geojson: GeoJSON.FeatureCollection) {
  const features =
    geojson.features?.flatMap((feature) => {
      const geometry = feature.geometry;
      if (!geometry || (geometry.type !== "Polygon" && geometry.type !== "MultiPolygon")) {
        return [];
      }

      const name = (feature.properties as { name?: string })?.name;
      if (!name) {
        return [];
      }

      const polygons =
        geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;

      let bestArea = -Infinity;
      let bestCentroid: [number, number] | null = null;

      polygons.forEach((rings) => {
        const outer = rings[0];
        if (!outer || outer.length < 3) {
          return;
        }
        const area = Math.abs(polygonArea(outer));
        if (area > bestArea) {
          bestArea = area;
          bestCentroid = polygonCentroid(outer);
        }
      });

      if (!bestCentroid) {
        return [];
      }

      return [
        {
          type: "Feature",
          geometry: { type: "Point", coordinates: bestCentroid },
          properties: { name },
        },
      ];
    }) ?? [];

  return {
    type: "FeatureCollection",
    features,
  };
}

function buildCountryCentroids(
  geojson: GeoJSON.FeatureCollection,
): Record<string, [number, number]> {
  const map: Record<string, [number, number]> = {};
  geojson.features?.forEach((feature) => {
    const geometry = feature.geometry;
    if (!geometry || (geometry.type !== "Polygon" && geometry.type !== "MultiPolygon")) {
      return;
    }

    const name = (feature.properties as { name?: string })?.name;
    if (!name) {
      return;
    }

    const polygons =
      geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
    let bestArea = -Infinity;
    let bestCentroid: [number, number] | null = null;

    polygons.forEach((rings) => {
      const outer = rings[0];
      if (!outer || outer.length < 3) {
        return;
      }
      const area = Math.abs(polygonArea(outer));
      if (area > bestArea) {
        bestArea = area;
        bestCentroid = polygonCentroid(outer);
      }
    });

    if (bestCentroid) {
      map[name] = bestCentroid;
    }
  });
  return map;
}

function ensurePinsLayers(map: maplibregl.Map) {
  if (!map.getSource("news-pins")) {
    map.addSource("news-pins", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
  }

  if (!map.getLayer("news-heat")) {
    map.addLayer({
      id: "news-heat",
      type: "heatmap",
      source: "news-pins",
      maxzoom: 4.5,
      paint: {
        "heatmap-weight": ["interpolate", ["linear"], ["get", "severity"], 0, 0, 1, 1],
        "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 1, 0.6, 4, 1.4],
        "heatmap-color": [
          "interpolate",
          ["linear"],
          ["heatmap-density"],
          0,
          "rgba(0,0,0,0)",
          0.3,
          "rgba(255,178,102,0.35)",
          0.6,
          "rgba(255,128,64,0.55)",
          1,
          "rgba(255,86,36,0.85)",
        ],
        "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 1, 18, 4, 32],
        "heatmap-opacity": 0.8,
      },
    });
  }

  if (!map.getLayer("news-glow")) {
    map.addLayer({
      id: "news-glow",
      type: "circle",
      source: "news-pins",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "count"], 1, 10, 6, 24],
        "circle-color": [
          "interpolate",
          ["linear"],
          ["get", "severity"],
          0,
          "rgba(255,190,120,0.25)",
          1,
          "rgba(255,110,60,0.45)",
        ],
        "circle-blur": 0.9,
        "circle-opacity": 0.8,
      },
    });
  }

  if (!map.getLayer("news-pins")) {
    map.addLayer({
      id: "news-pins",
      type: "circle",
      source: "news-pins",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "count"], 1, 3, 6, 10],
        "circle-color": [
          "interpolate",
          ["linear"],
          ["get", "severity"],
          0,
          "rgba(255,200,120,0.65)",
          1,
          "rgba(255,120,60,0.9)",
        ],
        "circle-blur": 0.4,
        "circle-stroke-color": "rgba(0,0,0,0.6)",
        "circle-stroke-width": 1,
        "circle-opacity": 0.95,
      },
    });
  }
}

function updatePinsSource(
  map: maplibregl.Map,
  centroids: Record<string, [number, number]>,
  pins: NewsPin[],
) {
  const source = map.getSource("news-pins") as maplibregl.GeoJSONSource | undefined;
  if (!source) {
    return;
  }
  const features = pins
    .map((pin) => {
      const coords = centroids[pin.countryName];
      if (!coords) {
        return null;
      }
      return {
        type: "Feature",
        geometry: { type: "Point", coordinates: coords },
        properties: pin,
      };
    })
    .filter(Boolean);
  source.setData({ type: "FeatureCollection", features });
}

function ensureAirTrafficLayers(map: maplibregl.Map) {
  if (!map.getSource("air-traffic")) {
    map.addSource("air-traffic", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
  }

  if (!map.getLayer("air-traffic-heat")) {
    map.addLayer({
      id: "air-traffic-heat",
      type: "heatmap",
      source: "air-traffic",
      maxzoom: 4.5,
      paint: {
        "heatmap-weight": ["interpolate", ["linear"], ["get", "velocity"], 0, 0.2, 900, 1],
        "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 1, 0.5, 4, 1.2],
        "heatmap-color": [
          "interpolate",
          ["linear"],
          ["heatmap-density"],
          0,
          "rgba(0,0,0,0)",
          0.3,
          "rgba(110,180,255,0.35)",
          0.6,
          "rgba(70,140,255,0.6)",
          1,
          "rgba(40,110,255,0.85)",
        ],
        "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 1, 10, 4, 20],
        "heatmap-opacity": 0.7,
      },
      layout: { visibility: "none" },
    });
  }

  if (!map.getLayer("air-traffic-points")) {
    map.addLayer({
      id: "air-traffic-points",
      type: "circle",
      source: "air-traffic",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "velocity"], 0, 1, 900, 3],
        "circle-color": "rgba(120,190,255,0.7)",
        "circle-opacity": 0.7,
        "circle-stroke-color": "rgba(0,0,0,0.4)",
        "circle-stroke-width": 0.5,
      },
      layout: { visibility: "none" },
    });
  }
}

function updateAirTrafficSource(map: maplibregl.Map, points: AirTrafficPoint[]) {
  const source = map.getSource("air-traffic") as maplibregl.GeoJSONSource | undefined;
  if (!source) {
    return;
  }
  const features = points.map((point) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [point.longitude, point.latitude] },
    properties: {
      id: point.id,
      velocity: point.velocity ?? 0,
    },
  }));
  source.setData({ type: "FeatureCollection", features });
}

function ensureIssLayer(map: maplibregl.Map) {
  if (!map.getSource("iss-position")) {
    map.addSource("iss-position", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });
  }

  if (!map.getLayer("iss-glow")) {
    map.addLayer({
      id: "iss-glow",
      type: "circle",
      source: "iss-position",
      paint: {
        "circle-radius": 12,
        "circle-color": "rgba(120,200,255,0.25)",
        "circle-blur": 0.9,
        "circle-opacity": 0.9,
      },
    });
  }

  if (!map.getLayer("iss-dot")) {
    map.addLayer({
      id: "iss-dot",
      type: "circle",
      source: "iss-position",
      paint: {
        "circle-radius": 3.5,
        "circle-color": "rgba(170,230,255,0.95)",
        "circle-stroke-color": "rgba(0,0,0,0.6)",
        "circle-stroke-width": 1,
      },
    });
  }

  if (!map.getLayer("iss-label")) {
    map.addLayer({
      id: "iss-label",
      type: "symbol",
      source: "iss-position",
      layout: {
        "text-field": "ISS",
        "text-size": 11,
        "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
        "text-offset": [0, 1.2],
        "text-anchor": "top",
      },
      paint: {
        "text-color": "rgba(200,230,255,0.9)",
        "text-halo-color": "rgba(0,0,0,0.6)",
        "text-halo-width": 0.8,
      },
    });
  }
}

function updateIssSource(map: maplibregl.Map, position: IssPosition | null) {
  const source = map.getSource("iss-position") as maplibregl.GeoJSONSource | undefined;
  if (!source) {
    return;
  }
  if (!position) {
    source.setData({ type: "FeatureCollection", features: [] });
    return;
  }
  source.setData({
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [position.longitude, position.latitude],
        },
        properties: {
          timestamp: position.timestamp ?? null,
        },
      },
    ],
  });
}

function coercePin(properties?: maplibregl.GeoJSONFeature["properties"]): NewsPin | null {
  if (!properties) {
    return null;
  }
  const severityValue = Number(properties.severity);
  if (!properties.id || !properties.title || !properties.countryName) {
    return null;
  }
  const countValue = Number(properties.count);
  return {
    id: String(properties.id),
    countryName: String(properties.countryName),
    countryId: properties.countryId ? String(properties.countryId) : undefined,
    title: String(properties.title),
    summary: String(properties.summary ?? ""),
    updatedAt: String(properties.updatedAt ?? ""),
    source: String(properties.source ?? ""),
    url: String(properties.url ?? ""),
    severity: Number.isNaN(severityValue) ? 0.5 : severityValue,
    count: Number.isNaN(countValue) ? 1 : Math.max(1, countValue),
  };
}

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function getCountryId(properties?: maplibregl.GeoJSONFeature["properties"]): string | null {
  if (!properties) {
    return null;
  }
  const code2 = properties["ISO3166-1-Alpha-2"];
  if (typeof code2 === "string" && code2.trim()) {
    return code2.trim();
  }
  const code3 = properties["ISO3166-1-Alpha-3"];
  if (typeof code3 === "string" && code3.trim()) {
    return code3.trim();
  }
  const name = properties.name;
  if (typeof name === "string" && name.trim()) {
    return slugify(name.trim());
  }
  return null;
}

function polygonArea(ring: number[][]) {
  let sum = 0;
  for (let i = 0; i < ring.length - 1; i += 1) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[i + 1];
    sum += x1 * y2 - x2 * y1;
  }
  return sum / 2;
}

function polygonCentroid(ring: number[][]): [number, number] {
  let areaSum = 0;
  let xSum = 0;
  let ySum = 0;
  for (let i = 0; i < ring.length - 1; i += 1) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[i + 1];
    const cross = x1 * y2 - x2 * y1;
    areaSum += cross;
    xSum += (x1 + x2) * cross;
    ySum += (y1 + y2) * cross;
  }

  const area = areaSum / 2;
  if (Math.abs(area) < 1e-7) {
    const [x1, y1] = ring[0];
    return [x1, y1];
  }
  return [xSum / (6 * area), ySum / (6 * area)];
}
