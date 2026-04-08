"""
Ingest trending searches from Google Trends using trendspyg RSS feeds.
No API key or authentication required.

Collects daily trending searches from multiple English-speaking regions
and extracts associated news articles/headlines for context.

Usage:
    python pipelines/ingest_trends.py

Output:
    data/raw_trends.json
"""

import json
import os
import sys
from datetime import datetime, timezone

from trendspyg import download_google_trends_rss

# English-speaking regions to pull trends from
GEOS = ["US", "GB", "CA", "AU"]


def collect_trends() -> list[dict]:
    """Collect trending searches from all configured regions."""
    all_trends = []

    for geo in GEOS:
        print(f"  Fetching trends for {geo}...", end=" ", flush=True)
        try:
            results = download_google_trends_rss(
                geo=geo,
                max_articles_per_trend=5,
                cache=False,
            )
            for trend in results:
                all_trends.append(extract_trend(trend, geo))
            print(f"{len(results)} trends")
        except Exception as e:
            print(f"[WARN] Failed: {e}", file=sys.stderr)

    return all_trends


def extract_trend(raw: dict, geo: str) -> dict:
    """Extract relevant fields from a trendspyg trend result."""
    articles = []
    for a in raw.get("news_articles", []):
        articles.append({
            "headline": a.get("headline", ""),
            "url": a.get("url", ""),
            "source": a.get("source", ""),
        })

    return {
        "source": "google_trends",
        "trend": raw.get("trend", ""),
        "traffic": raw.get("traffic", ""),
        "geo": geo,
        "published": str(raw.get("published", "")),
        "explore_link": raw.get("explore_link", ""),
        "articles": articles,
    }


def deduplicate(trends: list[dict]) -> list[dict]:
    """Remove duplicate trends (same trend name across regions)."""
    seen = set()
    unique = []
    for t in trends:
        key = t["trend"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(t)
        else:
            # Merge: add the geo to existing trend's info
            for existing in unique:
                if existing["trend"].lower().strip() == key:
                    if t["geo"] not in existing.get("also_trending_in", []):
                        existing.setdefault("also_trending_in", []).append(t["geo"])
                    break
    return unique


def parse_traffic(traffic_str: str) -> int:
    """Parse traffic string like '2000+' into an integer for sorting."""
    return int(traffic_str.replace("+", "").replace(",", "").strip() or "0")


def main():
    print(f"Collecting Google Trends from {len(GEOS)} regions...\n")

    trends = collect_trends()
    print(f"\nTotal collected: {len(trends)} trends")

    trends = deduplicate(trends)
    print(f"After dedup: {len(trends)} unique trends")

    # Sort by traffic volume
    trends.sort(key=lambda t: parse_traffic(t.get("traffic", "0")), reverse=True)

    # Save
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "raw_trends.json")

    output = {
        "source": "google_trends",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "geos": GEOS,
        "total_trends": len(trends),
        "trends": trends,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(trends)} trends to {output_path}")

    print("\nAll trends (sorted by traffic):")
    for i, t in enumerate(trends, 1):
        geos = t["geo"]
        if t.get("also_trending_in"):
            geos += ", " + ", ".join(t["also_trending_in"])
        article_count = len(t.get("articles", []))
        print(f"  {i:>2}. [{t['traffic']:>7}] {t['trend']} ({geos}) - {article_count} articles")


if __name__ == "__main__":
    main()
