import json
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List

import feedparser

from .models import CountrySnapshot, CountryStats, EventCluster, GlobalItem, SourceRef

DATA_DIR = Path(__file__).resolve().parent / "data"
COUNTRIES_PATH = DATA_DIR / "countries.json"
GEOJSON_PATH = Path(__file__).resolve().parents[1] / "public" / "countries.geojson"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or value.lower()


def _load_countries() -> List[Dict[str, List[str] | str]]:
    if not COUNTRIES_PATH.exists():
        return []

    try:
        countries_raw = json.loads(COUNTRIES_PATH.read_text())
    except json.JSONDecodeError:
        return []

    geojson_names_by_code: Dict[str, str] = {}
    geojson_names: List[str] = []
    if GEOJSON_PATH.exists():
        try:
            geojson = json.loads(GEOJSON_PATH.read_text())
        except json.JSONDecodeError:
            geojson = {}
        for feature in geojson.get("features", []):
            props = feature.get("properties", {})
            name = props.get("name")
            if not name:
                continue
            geojson_names.append(name)
            code2 = props.get("ISO3166-1-Alpha-2")
            code3 = props.get("ISO3166-1-Alpha-3")
            if code2:
                geojson_names_by_code[code2] = name
            if code3:
                geojson_names_by_code[code3] = name

    merged: Dict[str, Dict[str, List[str] | str]] = {}
    for entry in countries_raw:
        name_info = entry.get("name", {})
        common = name_info.get("common") or ""
        official = name_info.get("official") or ""
        cca2 = entry.get("cca2") or ""
        cca3 = entry.get("cca3") or ""
        country_id = cca2 or cca3 or _slugify(common or official)
        canonical = (
            geojson_names_by_code.get(cca2)
            or geojson_names_by_code.get(cca3)
            or common
            or official
        )
        if not canonical:
            continue

        aliases = set()
        for value in (common, official, canonical):
            if value:
                aliases.add(value)
        for value in entry.get("altSpellings", []):
            if value:
                aliases.add(value)
        if len(cca3) == 3:
            aliases.add(cca3)

        if canonical in merged:
            combined = set(merged[canonical]["aliases"])
            combined.update(aliases)
            merged[canonical]["aliases"] = sorted(combined)
            if not merged[canonical].get("id"):
                merged[canonical]["id"] = country_id
        else:
            merged[canonical] = {
                "id": country_id,
                "name": canonical,
                "aliases": sorted(aliases),
            }

    for name in geojson_names:
        if name not in merged:
            merged[name] = {
                "id": _slugify(name),
                "name": name,
                "aliases": [name],
            }

    return list(merged.values())


COUNTRIES = _load_countries()

TOPIC_KEYWORDS = {
    "security": ["military", "defense", "missile", "strike", "border", "troops"],
    "energy": ["gas", "oil", "energy", "pipeline", "nuclear", "power"],
    "diplomacy": ["talks", "summit", "minister", "agreement", "sanction"],
    "economy": ["trade", "tariff", "economy", "inflation", "export", "import"],
    "humanitarian": ["aid", "refugee", "humanitarian", "evacuation", "crisis"],
}
TOPIC_ALLOWLIST = {"security", "energy", "diplomacy", "economy", "humanitarian"}
BLOCKLIST_KEYWORDS = [
    "sport",
    "sports",
    "football",
    "soccer",
    "cricket",
    "tennis",
    "golf",
    "basketball",
    "baseball",
    "olympic",
    "entertainment",
    "celebrity",
    "movie",
    "film",
    "music",
    "concert",
    "award",
    "fashion",
]

GLOBAL_FEEDS = [
    ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("DW World", "https://rss.dw.com/rdf/rss-en-world"),
    ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    ("ReliefWeb", "https://reliefweb.int/updates/rss.xml"),
    ("NATO", "https://www.nato.int/cps/en/natohq/rss/news.rss"),
    ("IAEA", "https://www.iaea.org/feeds/press_release.xml"),
]


def _infer_topic(text: str) -> str:
    lowered = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return topic
    return "general"


def _is_blocked(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in BLOCKLIST_KEYWORDS)


def _match_countries(text: str) -> List[Dict[str, str]]:
    lowered = text.lower()
    matches: List[Dict[str, str]] = []
    seen = set()
    for country in COUNTRIES:
        for alias in country["aliases"]:
            alias_lower = alias.lower()
            if len(alias_lower) <= 2:
                continue
            if len(alias_lower) <= 3:
                if not re.search(rf"\\b{re.escape(alias_lower)}\\b", lowered):
                    continue
            elif alias_lower not in lowered:
                continue
            if country["id"] not in seen:
                matches.append({"id": country["id"], "name": country["name"]})
                seen.add(country["id"])
                break
    return matches


def _translate_text(text: str) -> str:
    return text


def _parse_published(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def fetch_rss(
    name: str,
    url: str,
    require_country: bool = True,
    max_age_days: int | None = None,
) -> List[Dict]:
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []
    results = []
    for entry in feed.entries[:30]:
        title = _translate_text(entry.get("title") or "")
        summary = _translate_text(entry.get("summary") or "")
        combined = f"{title} {summary}"
        if _is_blocked(combined):
            continue
        if max_age_days is not None:
            published_raw = entry.get("published", "")
            published_at = _parse_published(published_raw)
            if published_at is not None:
                cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
                if published_at < cutoff:
                    continue
        matches = _match_countries(combined)
        if require_country and not matches:
            continue
        countries = [match["name"] for match in matches]
        country_ids = [match["id"] for match in matches]
        results.append(
            {
                "title": title,
                "summary": summary,
                "url": entry.get("link"),
                "source": name,
                "published": entry.get("published", ""),
                "countries": countries,
                "country_ids": country_ids,
            }
        )
    return results


def build_global_items(max_age_days: int = 1) -> List[GlobalItem]:
    items: List[GlobalItem] = []
    for name, url in GLOBAL_FEEDS:
        entries = fetch_rss(name, url, require_country=True, max_age_days=max_age_days)
        for entry in entries:
            if not entry.get("title"):
                continue
            topic = _infer_topic(f"{entry['title']} {entry['summary']}")
            if topic not in TOPIC_ALLOWLIST:
                continue
            items.append(
                GlobalItem(
                    title=entry["title"],
                    summary=entry["summary"] or "",
                    source=SourceRef(name=name, url=entry["url"]),
                    url=entry["url"],
                    published_at=entry.get("published", "") or "",
                    topic=topic,
                    countries=entry.get("countries") or [],
                    country_ids=entry.get("country_ids") or [],
                )
            )
    return items


def build_snapshots(global_items: List[GlobalItem] | None = None) -> List[CountrySnapshot]:
    articles: List[Dict] = []
    if global_items:
        for item in global_items:
            for country_id in item.country_ids:
                articles.append(
                    {
                        "title": item.title,
                        "summary": item.summary,
                        "url": item.url,
                        "source": item.source.name,
                        "published": item.published_at,
                        "country_id": country_id,
                    }
                )

    grouped: Dict[str, List[Dict]] = {}
    for article in articles:
        grouped.setdefault(article["country_id"], []).append(article)

    snapshots: List[CountrySnapshot] = []
    for country in COUNTRIES:
        country_id = country["id"]
        name = country["name"]
        items = grouped.get(country_id, [])
        clusters_by_topic: Dict[str, List[Dict]] = {}
        for item in items:
            topic = _infer_topic(f"{item['title']} {item['summary']}")
            clusters_by_topic.setdefault(topic, []).append(item)

        events: List[EventCluster] = []
        for topic, topic_items in clusters_by_topic.items():
            topic_items = sorted(topic_items, key=lambda x: x.get("published") or "", reverse=True)
            head = topic_items[0]
            sources = [
                SourceRef(name=item["source"], url=item["url"])
                for item in topic_items[:3]
                if item.get("url")
            ]
            confidence = "High" if len(sources) > 1 else "Medium"
            events.append(
                EventCluster(
                    title=head["title"],
                    summary=head["summary"] or "",
                    why="",
                    confidence=confidence,
                    sources=sources,
                    updated_at=head.get("published", "") or "",
                    topic=topic,
                )
            )

        events = events[:5]
        activity_level = "Calm"
        if len(events) >= 4:
            activity_level = "Escalating"
        elif len(events) >= 1:
            activity_level = "Active"

        latest_item = ""
        if items:
            latest_item = sorted(
                items, key=lambda item: item.get("published") or "", reverse=True
            )[0].get("published", "")

        disputes = sum(1 for event in events if event.topic == "security")
        confidence = round(
            sum(0.8 if event.confidence == "High" else 0.6 for event in events) / max(len(events), 1),
            2,
        )

        snapshots.append(
            CountrySnapshot(
                id=country_id,
                name=name,
                activity_level=activity_level,
                updated_at=latest_item,
                events=events,
                stats=CountryStats(
                    signals=len(events),
                    disputes=disputes,
                    confidence=confidence,
                ),
            )
        )
    return snapshots
