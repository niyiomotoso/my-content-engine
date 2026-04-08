"""
Ingest trending posts from Reddit using public JSON endpoints.
No API key or authentication required.

Usage:
    python pipelines/ingest_reddit.py [--days 7] [--limit 100]

Output:
    data/raw_reddit.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

# Subreddits: AI tools & news, tech business, productivity
# Intentionally non-technical — targeting a general audience
SUBREDDITS = [
    # AI news & tools (consumer-focused)
    "artificial",
    "ChatGPT",
    "OpenAI",
    "singularity",
    # AI tips, tutorials & power-user content
    "ChatGPTPro",
    "AITools",
    # Tech business & startups
    "technology",
    "startups",
    "Entrepreneur",
    "SaaS",
    # Productivity & software tools
    "productivity",
    # Finance & markets
    "fintech",
    "wallstreetbets",
]

HEADERS = {"User-Agent": "ContentEngine/1.0 (weekly content research tool)"}
BASE_URL = "https://www.reddit.com"
REQUEST_DELAY = 6  # seconds between requests (stay well under 10/min limit)


def fetch_subreddit(subreddit: str, sort: str = "hot", limit: int = 100, time_filter: str = "week") -> list[dict]:
    """Fetch posts from a single subreddit."""
    params = {"limit": min(limit, 100), "raw_json": 1}
    if sort == "top":
        params["t"] = time_filter

    url = f"{BASE_URL}/r/{subreddit}/{sort}.json"
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("children", [])
    except requests.RequestException as e:
        print(f"  [WARN] Failed to fetch r/{subreddit}/{sort}: {e}", file=sys.stderr)
        return []
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  [WARN] Bad response from r/{subreddit}/{sort}: {e}", file=sys.stderr)
        return []


def extract_post(raw: dict, source_sort: str) -> dict:
    """Extract relevant fields from a raw Reddit post."""
    d = raw.get("data", {})
    created = datetime.fromtimestamp(d.get("created_utc", 0), tz=timezone.utc)
    return {
        "source": "reddit",
        "subreddit": d.get("subreddit", ""),
        "title": d.get("title", ""),
        "selftext": (d.get("selftext", "") or "")[:500],  # cap long posts
        "score": d.get("score", 0),
        "upvote_ratio": d.get("upvote_ratio", 0),
        "num_comments": d.get("num_comments", 0),
        "url": d.get("url", ""),
        "permalink": f"https://reddit.com{d.get('permalink', '')}",
        "author": d.get("author", ""),
        "created_utc": created.isoformat(),
        "fetched_via": source_sort,
        "is_self": d.get("is_self", False),
        "link_flair_text": d.get("link_flair_text", ""),
    }


def filter_by_age(posts: list[dict], max_days: int) -> list[dict]:
    """Keep only posts created within the last N days."""
    now = datetime.now(timezone.utc)
    filtered = []
    for p in posts:
        created = datetime.fromisoformat(p["created_utc"])
        age_days = (now - created).total_seconds() / 86400
        if age_days <= max_days:
            filtered.append(p)
    return filtered


def deduplicate(posts: list[dict]) -> list[dict]:
    """Remove duplicate posts by permalink."""
    seen = set()
    unique = []
    for p in posts:
        key = p["permalink"]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def main():
    parser = argparse.ArgumentParser(description="Ingest trending Reddit posts")
    parser.add_argument("--days", type=int, default=7, help="Max age of posts in days (default: 7)")
    parser.add_argument("--limit", type=int, default=100, help="Posts per subreddit per sort (default: 100)")
    args = parser.parse_args()

    all_posts = []
    total_requests = 0

    print(f"Collecting Reddit posts from {len(SUBREDDITS)} subreddits...")
    print(f"Filters: last {args.days} days, up to {args.limit} per sort\n")

    for sub in SUBREDDITS:
        for sort in ["hot", "top"]:
            if total_requests > 0:
                time.sleep(REQUEST_DELAY)

            print(f"  Fetching r/{sub}/{sort}...", end=" ", flush=True)
            raw_posts = fetch_subreddit(sub, sort=sort, limit=args.limit)
            extracted = [extract_post(p, sort) for p in raw_posts if p.get("kind") == "t3"]
            all_posts.extend(extracted)
            total_requests += 1
            print(f"{len(extracted)} posts")

    # Filter and deduplicate
    before_filter = len(all_posts)
    all_posts = filter_by_age(all_posts, args.days)
    print(f"\nAge filter: {before_filter} -> {len(all_posts)} posts (last {args.days} days)")

    all_posts = deduplicate(all_posts)
    print(f"After dedup: {len(all_posts)} unique posts")

    # Sort by score descending
    all_posts.sort(key=lambda p: p["score"], reverse=True)

    # Save
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "raw_reddit.json")

    output = {
        "source": "reddit",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "subreddits": SUBREDDITS,
        "filters": {"max_days": args.days, "limit_per_sort": args.limit},
        "total_posts": len(all_posts),
        "posts": all_posts,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(all_posts)} posts to {output_path}")

    # Quick summary
    print("\nTop 10 posts by score:")
    for i, p in enumerate(all_posts[:10], 1):
        print(f"  {i:>2}. [{p['score']:>6}] r/{p['subreddit']}: {p['title'][:70]}")


if __name__ == "__main__":
    main()
