"""
Ingest trending stories from Hacker News using the free Firebase API.
No authentication required.

Usage:
    python pipelines/ingest_hn.py [--days 7] [--limit 200]

Output:
    data/raw_hn.json
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

HN_API = "https://hacker-news.firebaseio.com/v0"
SESSION = requests.Session()


def fetch_story_ids(endpoint: str) -> list[int]:
    """Fetch story IDs from a HN endpoint (topstories, beststories, newstories)."""
    try:
        resp = SESSION.get(f"{HN_API}/{endpoint}.json", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"  [WARN] Failed to fetch {endpoint}: {e}", file=sys.stderr)
        return []


def fetch_item(item_id: int) -> dict | None:
    """Fetch a single HN item by ID."""
    try:
        resp = SESSION.get(f"{HN_API}/item/{item_id}.json", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return None


def extract_story(raw: dict) -> dict:
    """Extract relevant fields from a raw HN item."""
    created = datetime.fromtimestamp(raw.get("time", 0), tz=timezone.utc)
    return {
        "source": "hackernews",
        "hn_id": raw.get("id", 0),
        "title": raw.get("title", ""),
        "url": raw.get("url", ""),
        "hn_url": f"https://news.ycombinator.com/item?id={raw.get('id', 0)}",
        "score": raw.get("score", 0),
        "num_comments": raw.get("descendants", 0),
        "author": raw.get("by", ""),
        "created_utc": created.isoformat(),
        "type": raw.get("type", "story"),
    }


def filter_by_age(stories: list[dict], max_days: int) -> list[dict]:
    """Keep only stories within the last N days."""
    now = datetime.now(timezone.utc)
    return [
        s for s in stories
        if (now - datetime.fromisoformat(s["created_utc"])).total_seconds() / 86400 <= max_days
    ]


def deduplicate(stories: list[dict]) -> list[dict]:
    """Remove duplicates by hn_id."""
    seen = set()
    unique = []
    for s in stories:
        if s["hn_id"] not in seen:
            seen.add(s["hn_id"])
            unique.append(s)
    return unique


def main():
    parser = argparse.ArgumentParser(description="Ingest trending Hacker News stories")
    parser.add_argument("--days", type=int, default=7, help="Max age in days (default: 7)")
    parser.add_argument("--limit", type=int, default=200, help="Stories per endpoint (default: 200)")
    args = parser.parse_args()

    endpoints = ["topstories", "beststories", "newstories"]
    all_ids = set()

    print(f"Collecting Hacker News stories...")
    print(f"Filters: last {args.days} days, up to {args.limit} per endpoint\n")

    for ep in endpoints:
        ids = fetch_story_ids(ep)[:args.limit]
        print(f"  {ep}: {len(ids)} IDs")
        all_ids.update(ids)

    print(f"\n  Total unique IDs: {len(all_ids)}")
    print(f"  Fetching story details...", end=" ", flush=True)

    # Fetch stories in parallel (HN API has no strict rate limit)
    stories = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_item, sid): sid for sid in all_ids}
        for future in as_completed(futures):
            raw = future.result()
            if raw and raw.get("type") == "story" and raw.get("title"):
                stories.append(extract_story(raw))

    print(f"{len(stories)} stories fetched")

    # Filter and deduplicate
    before = len(stories)
    stories = filter_by_age(stories, args.days)
    print(f"  Age filter: {before} -> {len(stories)} (last {args.days} days)")

    stories = deduplicate(stories)
    stories.sort(key=lambda s: s["score"], reverse=True)

    # Save
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "raw_hn.json")

    output = {
        "source": "hackernews",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "endpoints": endpoints,
        "filters": {"max_days": args.days, "limit_per_endpoint": args.limit},
        "total_stories": len(stories),
        "stories": stories,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(stories)} stories to {output_path}")

    print("\nTop 10 stories by score:")
    for i, s in enumerate(stories[:10], 1):
        print(f"  {i:>2}. [{s['score']:>5}] {s['title'][:70]}")


if __name__ == "__main__":
    main()
