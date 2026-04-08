"""
Ingest trending AI/tech videos from YouTube using yt-dlp search.
No API key required — uses YouTube search via yt-dlp.

Usage:
    python pipelines/ingest_youtube.py [--days 7] [--limit 50]

Output:
    data/raw_youtube.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

import yt_dlp

# Search queries to find trending AI/tech content
# Each query targets a different angle of what the target audience cares about
SEARCH_QUERIES = [
    # News-focused queries
    "AI tools news this week",
    "new AI tools released 2026",
    "AI business news today",
    "AI startups funding news",
    "tech news this week AI",
    "ChatGPT update news",
    # Tutorial & how-to queries (for content mix)
    "AI tool tutorial how to use",
    "how to use ChatGPT for work productivity",
    "AI productivity hack workflow tips",
    "best AI workflow automation tutorial",
    "AI tools for students beginners guide",
    "AI side hustle tutorial step by step",
    "AI hacks tips tricks you need to know",
    "ChatGPT prompts tips for professionals",
]

RESULTS_PER_QUERY = 15  # yt-dlp search results per query


def search_youtube(query: str, max_results: int) -> list[dict]:
    """Search YouTube and return flat metadata for each result."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlist_items": f"1-{max_results}",
    }

    search_url = f"ytsearch{max_results}:{query}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            return info.get("entries", []) or []
    except Exception as e:
        print(f"  [WARN] Search failed for '{query}': {e}", file=sys.stderr)
        return []


def extract_video(raw: dict, query: str) -> dict:
    """Extract relevant fields from a yt-dlp flat result."""
    # yt-dlp flat mode gives timestamp (unix) or None
    ts = raw.get("timestamp") or raw.get("release_timestamp")
    if ts:
        created = datetime.fromtimestamp(ts, tz=timezone.utc)
    else:
        created = None

    return {
        "source": "youtube",
        "video_id": raw.get("id", ""),
        "title": raw.get("title", ""),
        "description": (raw.get("description", "") or "")[:500],
        "channel": raw.get("channel", "") or raw.get("uploader", ""),
        "view_count": raw.get("view_count", 0) or 0,
        "duration": raw.get("duration", 0) or 0,
        "url": f"https://www.youtube.com/watch?v={raw.get('id', '')}",
        "created_utc": created.isoformat() if created else None,
        "search_query": query,
        "channel_verified": raw.get("channel_is_verified", False),
    }


def filter_by_age(videos: list[dict], max_days: int) -> list[dict]:
    """Keep only videos within the last N days. Videos without dates are kept."""
    now = datetime.now(timezone.utc)
    filtered = []
    for v in videos:
        if v["created_utc"] is None:
            filtered.append(v)  # keep videos with unknown date
            continue
        created = datetime.fromisoformat(v["created_utc"])
        age_days = (now - created).total_seconds() / 86400
        if age_days <= max_days:
            filtered.append(v)
    return filtered


def deduplicate(videos: list[dict]) -> list[dict]:
    """Remove duplicates by video_id."""
    seen = set()
    unique = []
    for v in videos:
        vid = v["video_id"]
        if vid and vid not in seen:
            seen.add(vid)
            unique.append(v)
    return unique


def main():
    parser = argparse.ArgumentParser(description="Ingest trending YouTube AI/tech videos")
    parser.add_argument("--days", type=int, default=7, help="Max age in days (default: 7)")
    parser.add_argument("--limit", type=int, default=15, help="Results per search query (default: 15)")
    args = parser.parse_args()

    all_videos = []

    print(f"Searching YouTube across {len(SEARCH_QUERIES)} queries...")
    print(f"Filters: last {args.days} days, {args.limit} results per query\n")

    for i, query in enumerate(SEARCH_QUERIES):
        if i > 0:
            time.sleep(2)  # small delay between searches

        print(f"  Searching: '{query}'...", end=" ", flush=True)
        raw_results = search_youtube(query, args.limit)
        videos = [extract_video(r, query) for r in raw_results if r.get("title")]
        all_videos.extend(videos)
        print(f"{len(videos)} videos")

    # Filter and deduplicate
    before = len(all_videos)
    all_videos = filter_by_age(all_videos, args.days)
    print(f"\nAge filter: {before} -> {len(all_videos)} (last {args.days} days)")

    all_videos = deduplicate(all_videos)
    print(f"After dedup: {len(all_videos)} unique videos")

    # Sort by view count descending
    all_videos.sort(key=lambda v: v["view_count"], reverse=True)

    # Save
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "raw_youtube.json")

    output = {
        "source": "youtube",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "search_queries": SEARCH_QUERIES,
        "filters": {"max_days": args.days, "results_per_query": args.limit},
        "total_videos": len(all_videos),
        "videos": all_videos,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(all_videos)} videos to {output_path}")

    print("\nTop 10 videos by views:")
    for i, v in enumerate(all_videos[:10], 1):
        views = f"{v['view_count']:,}" if v["view_count"] else "?"
        print(f"  {i:>2}. [{views:>12} views] {v['title'][:60]}")
        print(f"      channel: {v['channel']}")


if __name__ == "__main__":
    main()
