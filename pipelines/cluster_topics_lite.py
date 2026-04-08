"""
Lightweight topic clustering using TF-IDF + Agglomerative Clustering.
Drop-in replacement for cluster_topics.py when BERTopic/torch are unavailable.

Usage:
    python pipelines/cluster_topics_lite.py [--min-cluster 3] [--max-cluster 50]

Output:
    data/clustered_topics.json
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_raw_data() -> list[dict]:
    """Load and normalize all raw data into a common schema."""
    items = []

    path = os.path.join(DATA_DIR, "raw_reddit.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        for p in data.get("posts", []):
            items.append({
                "source": "reddit",
                "title": p["title"],
                "text": p.get("selftext", ""),
                "score": p.get("score", 0),
                "engagement": p.get("num_comments", 0),
                "url": p.get("permalink", ""),
                "created_utc": p.get("created_utc", ""),
                "meta": {
                    "subreddit": p.get("subreddit", ""),
                    "upvote_ratio": p.get("upvote_ratio", 0),
                },
            })
        print(f"  Reddit: {len(data.get('posts', []))} posts")

    path = os.path.join(DATA_DIR, "raw_hn.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        for s in data.get("stories", []):
            items.append({
                "source": "hackernews",
                "title": s["title"],
                "text": "",
                "score": s.get("score", 0),
                "engagement": s.get("num_comments", 0),
                "url": s.get("hn_url", ""),
                "created_utc": s.get("created_utc", ""),
                "meta": {},
            })
        print(f"  Hacker News: {len(data.get('stories', []))} stories")

    path = os.path.join(DATA_DIR, "raw_youtube.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        for v in data.get("videos", []):
            items.append({
                "source": "youtube",
                "title": v["title"],
                "text": v.get("description", ""),
                "score": v.get("view_count", 0),
                "engagement": v.get("view_count", 0),
                "url": v.get("url", ""),
                "created_utc": v.get("created_utc", ""),
                "meta": {
                    "channel": v.get("channel", ""),
                    "duration": v.get("duration", 0),
                },
            })
        print(f"  YouTube: {len(data.get('videos', []))} videos")

    path = os.path.join(DATA_DIR, "raw_trends.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        for t in data.get("trends", []):
            headlines = " | ".join(
                a["headline"] for a in t.get("articles", []) if a.get("headline")
            )
            traffic = int(t.get("traffic", "0").replace("+", "").replace(",", "") or 0)
            items.append({
                "source": "google_trends",
                "title": t["trend"],
                "text": headlines,
                "score": traffic,
                "engagement": traffic,
                "url": t.get("explore_link", ""),
                "created_utc": t.get("published", ""),
                "meta": {
                    "geo": t.get("geo", ""),
                    "articles": t.get("articles", []),
                },
            })
        print(f"  Google Trends: {len(data.get('trends', []))} trends")

    return items


def extract_keywords(texts: list[str], top_n: int = 10) -> list[str]:
    """Extract top TF-IDF keywords from a list of texts."""
    if not texts:
        return []
    try:
        vec = TfidfVectorizer(max_features=50, stop_words="english", ngram_range=(1, 2))
        tfidf = vec.fit_transform(texts)
        scores = np.asarray(tfidf.mean(axis=0)).flatten()
        feature_names = vec.get_feature_names_out()
        top_indices = scores.argsort()[::-1][:top_n]
        return [feature_names[i] for i in top_indices]
    except Exception:
        return []


def build_cluster(member_indices: list[int], items: list[dict], topic_id: int,
                  keywords: list[str], label: str) -> dict:
    """Build a cluster dict from member indices."""
    members = [items[i] for i in member_indices]

    source_counts = {}
    for m in members:
        src = m["source"]
        source_counts[src] = source_counts.get(src, 0) + 1

    members.sort(key=lambda m: m.get("score", 0), reverse=True)
    top_item = members[0]

    total_score = sum(m.get("score", 0) for m in members)
    total_engagement = sum(m.get("engagement", 0) for m in members)
    avg_score = total_score / len(members) if members else 0

    return {
        "topic_id": int(topic_id),
        "label": label,
        "keywords": keywords,
        "representative_title": top_item["title"],
        "num_items": len(members),
        "sources": source_counts,
        "cross_source_count": len(source_counts),
        "total_score": total_score,
        "total_engagement": total_engagement,
        "avg_score": round(avg_score, 1),
        "items": members,
    }


def cluster_items(items: list[dict], min_cluster_size: int, max_cluster_size: int) -> list[dict]:
    """Cluster items using TF-IDF + Agglomerative Clustering."""
    docs = []
    for item in items:
        text_snippet = (item.get("text", "") or "")[:100]
        doc = item["title"]
        if text_snippet:
            doc += " " + text_snippet
        docs.append(doc)

    print(f"  Vectorizing {len(docs)} documents...", end=" ", flush=True)
    vectorizer = TfidfVectorizer(
        max_features=5000, stop_words="english",
        ngram_range=(1, 2), min_df=2, max_df=0.8,
    )
    tfidf_matrix = vectorizer.fit_transform(docs)
    print(f"done (shape: {tfidf_matrix.shape})")

    # Compute cosine distance
    print("  Computing similarity matrix...", end=" ", flush=True)
    sim_matrix = cosine_similarity(tfidf_matrix)
    dist_matrix = 1 - sim_matrix
    np.fill_diagonal(dist_matrix, 0)
    dist_matrix = np.clip(dist_matrix, 0, None)
    print("done")

    # Agglomerative clustering
    print("  Running agglomerative clustering...", end=" ", flush=True)
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.75,
        metric="precomputed",
        linkage="average",
    )
    labels = clustering.fit_predict(dist_matrix)
    print("done")

    n_clusters = len(set(labels))
    print(f"  Found {n_clusters} raw clusters")

    # Group by cluster label
    cluster_groups = {}
    for idx, label in enumerate(labels):
        cluster_groups.setdefault(int(label), []).append(idx)

    # Filter: only keep clusters with min_cluster_size or more items
    clusters = []
    topic_id = 0
    for label, member_indices in sorted(cluster_groups.items()):
        if len(member_indices) < min_cluster_size:
            continue

        # Split oversized clusters
        if len(member_indices) > max_cluster_size:
            from sklearn.cluster import KMeans
            n_sub = max(2, len(member_indices) // max_cluster_size)
            sub_matrix = tfidf_matrix[member_indices].toarray()
            km = KMeans(n_clusters=n_sub, random_state=42, n_init=10)
            sub_labels = km.fit_predict(sub_matrix)
            sub_groups = {}
            for i, sl in enumerate(sub_labels):
                sub_groups.setdefault(int(sl), []).append(member_indices[i])
            for sg in sub_groups.values():
                if len(sg) >= min_cluster_size:
                    member_texts = [docs[i] for i in sg]
                    keywords = extract_keywords(member_texts)
                    clusters.append(build_cluster(sg, items, topic_id, keywords, f"cluster_{topic_id}"))
                    topic_id += 1
        else:
            member_texts = [docs[i] for i in member_indices]
            keywords = extract_keywords(member_texts)
            clusters.append(build_cluster(member_indices, items, topic_id, keywords, f"cluster_{topic_id}"))
            topic_id += 1

    # Sort: cross-source coverage first, then total engagement
    clusters.sort(
        key=lambda c: (c["cross_source_count"], c["total_engagement"]),
        reverse=True,
    )

    for rank, cluster in enumerate(clusters, 1):
        cluster["rank"] = rank

    return clusters


def main():
    parser = argparse.ArgumentParser(description="Cluster and deduplicate topics (lightweight)")
    parser.add_argument("--min-cluster", type=int, default=3, help="Minimum cluster size (default: 3)")
    parser.add_argument("--max-cluster", type=int, default=50, help="Maximum cluster size before splitting (default: 50)")
    args = parser.parse_args()

    print("Loading raw data from all sources...")
    items = load_raw_data()
    print(f"\n  Total items: {len(items)}")

    if not items:
        print("No data found. Run the ingest scripts first.")
        sys.exit(1)

    print("\nRunning topic clustering...")
    clusters = cluster_items(items, args.min_cluster, args.max_cluster)

    output_path = os.path.join(DATA_DIR, "clustered_topics.json")
    output = {
        "clustered_at": datetime.now(timezone.utc).isoformat(),
        "total_input_items": len(items),
        "total_clusters": len(clusters),
        "settings": {"min_cluster_size": args.min_cluster, "max_cluster_size": args.max_cluster},
        "clusters": clusters,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(clusters)} clusters to {output_path}")

    print(f"\nTop 25 topic clusters:")
    print(f"{'Rank':>4} {'Items':>5} {'Srcs':>4} {'Engagement':>12} {'Representative Title'}")
    print("-" * 90)
    for c in clusters[:25]:
        src_list = sorted(c["sources"].keys())
        src_short = ",".join(s[:2].upper() for s in src_list)
        print(
            f"{c['rank']:>4} {c['num_items']:>5} {src_short:>4} "
            f"{c['total_engagement']:>12,} {c['representative_title'][:50]}"
        )


if __name__ == "__main__":
    main()
