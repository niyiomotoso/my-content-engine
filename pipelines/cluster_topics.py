"""
Cluster and deduplicate items from all data sources into unified topics.

Loads raw data from Reddit, HN, YouTube, and Google Trends, embeds titles
using sentence-transformers, clusters with BERTopic, and produces a clean
list of deduplicated topic clusters.

Usage:
    python pipelines/cluster_topics.py [--min-cluster 5] [--max-cluster 50]

Output:
    data/clustered_topics.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from umap import UMAP

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_raw_data() -> list[dict]:
    """Load and normalize all raw data into a common schema."""
    items = []

    # Reddit
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

    # Hacker News
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

    # YouTube
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

    # Google Trends
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


def embed_items(items: list[dict], model: SentenceTransformer) -> np.ndarray:
    """Embed item titles (+ text snippet) for clustering."""
    docs = []
    for item in items:
        text_snippet = (item.get("text", "") or "")[:100]
        doc = item["title"]
        if text_snippet:
            doc += " " + text_snippet
        docs.append(doc)

    print(f"\n  Embedding {len(docs)} documents...", end=" ", flush=True)
    embeddings = model.encode(docs, show_progress_bar=False, batch_size=64)
    print(f"done (shape: {embeddings.shape})")
    return embeddings


def sub_cluster(indices: list[int], embeddings: np.ndarray, max_size: int) -> list[list[int]]:
    """Split an oversized cluster into smaller sub-clusters using KMeans."""
    n_sub = max(2, len(indices) // max_size)
    sub_embeddings = embeddings[indices]
    km = KMeans(n_clusters=n_sub, random_state=42, n_init=10)
    labels = km.fit_predict(sub_embeddings)
    groups = {}
    for idx, label in zip(indices, labels):
        groups.setdefault(int(label), []).append(idx)
    return list(groups.values())


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


def cluster_items(
    items: list[dict], embeddings: np.ndarray, min_cluster_size: int, max_cluster_size: int
) -> list[dict]:
    """Run BERTopic clustering, split oversized clusters, build topic list."""
    docs = [item["title"] for item in items]

    umap_model = UMAP(
        n_components=10, n_neighbors=20, min_dist=0.05,
        metric="cosine", random_state=42,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=min_cluster_size, min_samples=3,
        metric="euclidean", prediction_data=True,
    )

    print(f"  Clustering with BERTopic (min={min_cluster_size}, max={max_cluster_size})...", end=" ", flush=True)
    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        nr_topics="auto",
        calculate_probabilities=False,
    )
    topics, _ = topic_model.fit_transform(docs, embeddings)
    print("done")

    n_topics = len(set(topics)) - (1 if -1 in topics else 0)
    n_outliers = topics.count(-1)
    print(f"  Found {n_topics} topics, {n_outliers} outliers")

    # Build clusters, splitting oversized ones
    topic_info = topic_model.get_topic_info()
    clusters = []
    next_id = 1000  # IDs for sub-clusters

    for _, row in topic_info.iterrows():
        topic_id = row["Topic"]
        if topic_id == -1:
            continue

        member_indices = [i for i, t in enumerate(topics) if t == topic_id]
        topic_words = topic_model.get_topic(topic_id)
        keywords = [w for w, _ in topic_words[:10]] if topic_words else []

        if len(member_indices) > max_cluster_size:
            # Split oversized cluster
            sub_groups = sub_cluster(member_indices, embeddings, max_cluster_size)
            print(f"  Split topic {topic_id} ({len(member_indices)} items) into {len(sub_groups)} sub-clusters")
            for sg in sub_groups:
                if len(sg) >= 3:  # only keep meaningful sub-clusters
                    clusters.append(build_cluster(sg, items, next_id, keywords, f"{row.get('Name', '')}__sub"))
                    next_id += 1
        else:
            clusters.append(build_cluster(member_indices, items, topic_id, keywords, row.get("Name", "")))

    # Sort: cross-source coverage first, then total engagement
    clusters.sort(
        key=lambda c: (c["cross_source_count"], c["total_engagement"]),
        reverse=True,
    )

    for rank, cluster in enumerate(clusters, 1):
        cluster["rank"] = rank

    return clusters


def main():
    parser = argparse.ArgumentParser(description="Cluster and deduplicate topics")
    parser.add_argument("--min-cluster", type=int, default=5, help="Minimum cluster size (default: 5)")
    parser.add_argument("--max-cluster", type=int, default=50, help="Maximum cluster size before splitting (default: 50)")
    args = parser.parse_args()

    print("Loading raw data from all sources...")
    items = load_raw_data()
    print(f"\n  Total items: {len(items)}")

    if not items:
        print("No data found. Run the ingest scripts first.")
        sys.exit(1)

    print("\nLoading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embed_items(items, model)

    print("\nRunning topic clustering...")
    clusters = cluster_items(items, embeddings, args.min_cluster, args.max_cluster)

    # Save
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

    # Summary
    print(f"\nTop 25 topic clusters:")
    print(f"{'Rank':>4} {'Items':>5} {'Srcs':>4} {'Engagement':>12} {'Representative Title'}")
    print("-" * 90)
    for c in clusters[:25]:
        src_list = sorted(c["sources"].keys())
        src_short = ",".join(s[:2].upper() for s in src_list)  # RE,HN,YT,GT
        print(
            f"{c['rank']:>4} {c['num_items']:>5} {src_short:>4} "
            f"{c['total_engagement']:>12,} {c['representative_title'][:50]}"
        )


if __name__ == "__main__":
    main()
