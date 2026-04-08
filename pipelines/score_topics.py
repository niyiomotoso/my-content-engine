"""
Score and rank clustered topics by velocity, engagement, relevance, and novelty.

Takes clustered_topics.json and produces scored_topics.json with composite scores
and relevance filtering for the AI/tech/business niche.

Usage:
    python pipelines/score_topics.py [--top 20] [--relevance-threshold 0.25]

Output:
    data/scored_topics.json
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone

import numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Scoring weights
WEIGHTS = {
    "velocity": 0.30,
    "engagement": 0.25,
    "relevance": 0.30,
    "novelty": 0.15,
}

# Niche keywords — topics are scored by semantic similarity to these
NICHE_KEYWORDS = [
    "artificial intelligence AI tools",
    "ChatGPT OpenAI Claude AI assistant",
    "AI productivity software automation",
    "tech startup business SaaS",
    "AI news latest update release",
    "machine learning deep learning model",
    "AI ethics safety regulation",
    "tech industry layoffs hiring",
    "fintech cryptocurrency blockchain",
    "software development programming tools",
    "AI video content creation",
    "tech business investment funding",
]


def load_clusters() -> list[dict]:
    """Load clustered topics."""
    path = os.path.join(DATA_DIR, "clustered_topics.json")
    if not os.path.exists(path):
        print("Error: clustered_topics.json not found. Run cluster_topics.py first.")
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    return data.get("clusters", [])


def score_velocity(cluster: dict) -> float:
    """Score based on how many sources picked up this topic (cross-source = high velocity).

    Also considers recency of items — more recent items = higher velocity.
    """
    cross_source = cluster.get("cross_source_count", 1)
    num_items = cluster.get("num_items", 1)

    # Cross-source signal (max at 4 sources)
    source_score = min(cross_source / 4.0, 1.0)

    # Volume signal (log scale, caps at ~50 items)
    volume_score = min(math.log(num_items + 1) / math.log(51), 1.0)

    # Combine: cross-source matters more
    return 0.7 * source_score + 0.3 * volume_score


def score_engagement(cluster: dict, max_engagement: float) -> float:
    """Score based on total engagement (log-normalized against dataset max)."""
    engagement = cluster.get("total_engagement", 0)
    if max_engagement <= 0 or engagement <= 0:
        return 0.0
    # Log scale to prevent mega-viral posts from dominating
    return min(math.log(engagement + 1) / math.log(max_engagement + 1), 1.0)


def score_relevance(cluster: dict, model: SentenceTransformer, niche_embeddings: np.ndarray) -> float:
    """Score by semantic similarity to niche keywords."""
    # Build a text representation of the cluster
    title = cluster.get("representative_title", "")
    keywords = " ".join(cluster.get("keywords", []))
    # Include a few item titles for richer signal
    sample_titles = " ".join(
        item["title"] for item in cluster.get("items", [])[:5]
    )
    cluster_text = f"{title} {keywords} {sample_titles}"

    cluster_emb = model.encode([cluster_text])
    # Cosine similarity against all niche keyword embeddings
    similarities = np.dot(cluster_emb, niche_embeddings.T)[0]
    # Take the max similarity (best match to any niche keyword)
    return float(np.max(similarities))


def score_novelty(cluster: dict) -> float:
    """Score based on uniqueness indicators.

    Higher novelty for:
    - Fewer items (niche/emerging topic)
    - Topics with specific keywords (not generic)
    """
    num_items = cluster.get("num_items", 1)
    keywords = cluster.get("keywords", [])

    # Smaller clusters are more novel (emerging topics)
    # Sweet spot: 5-15 items = high novelty, >30 = lower
    if num_items <= 15:
        size_score = 1.0
    elif num_items <= 30:
        size_score = 0.7
    else:
        size_score = 0.4

    # Keywords specificity: longer/more specific keywords = more novel
    avg_keyword_len = np.mean([len(k) for k in keywords]) if keywords else 0
    keyword_score = min(avg_keyword_len / 10.0, 1.0)

    return 0.6 * size_score + 0.4 * keyword_score


def classify_content_type(cluster: dict) -> str:
    """Classify a topic as NEWS, HOW_TO, OPINION, or ROUNDUP based on title/keyword patterns.

    This helps enforce a content mix — not everything should be news reporting.
    """
    title = cluster.get("representative_title", "").lower()
    keywords = " ".join(cluster.get("keywords", [])).lower()
    # Include sample item titles for better signal
    sample_titles = " ".join(
        item.get("title", "").lower() for item in cluster.get("items", [])[:10]
    )
    text = f"{title} {keywords} {sample_titles}"

    # HOW_TO patterns — tutorials, guides, step-by-step
    howto_signals = [
        "how to", "tutorial", "step by step", "guide", "tips",
        "hack", "hacks", "trick", "tricks", "let me show you",
        "here's how", "walkthrough", "setup", "set up", "workflow",
        "prompt", "prompts for", "use case", "use cases",
        "beginner", "learn how", "teach you",
    ]
    howto_count = sum(1 for s in howto_signals if s in text)

    # ROUNDUP patterns — lists, best-of, comparisons
    roundup_signals = [
        "best ", "top ", " tools", " apps", "free ai",
        "roundup", "compared", "comparison", "vs ",
        "you need", "must have", "essential", "worth",
    ]
    roundup_count = sum(1 for s in roundup_signals if s in text)

    # Check for numbered lists (e.g., "5 AI tools", "10 best")
    import re
    number_list = len(re.findall(r'\b\d+\s+(ai|tool|app|way|tip|hack|course|platform|skill)', text))
    roundup_count += number_list

    # NEWS patterns — breaking events, company actions
    news_signals = [
        "launch", "announce", "release", "drop", "unveil",
        "acquire", "deal", "funding", "raise", "ipo",
        "earning", "report", "billion", "million",
        "ban", "sue", "fire", "resign", "deadline",
    ]
    news_count = sum(1 for s in news_signals if s in text)

    # OPINION patterns — takes, debates
    opinion_signals = [
        "opinion", "debate", "overblown", "controversial",
        "think", "believe", "predict", "warn", "fear",
        "destroy", "kill", "end of", "death of",
    ]
    opinion_count = sum(1 for s in opinion_signals if s in text)

    # Pick the strongest signal
    scores = {
        "HOW_TO": howto_count * 1.2,   # slight boost to surface tutorials
        "ROUNDUP": roundup_count * 1.1,
        "NEWS": news_count,
        "OPINION": opinion_count,
    }

    best_type = max(scores, key=scores.get)
    # Default to NEWS if no strong signal
    if scores[best_type] == 0:
        return "NEWS"
    return best_type


def main():
    parser = argparse.ArgumentParser(description="Score and rank topics")
    parser.add_argument("--top", type=int, default=20, help="Number of top topics to output (default: 20)")
    parser.add_argument("--relevance-threshold", type=float, default=0.25,
                        help="Minimum relevance score to keep (default: 0.25)")
    args = parser.parse_args()

    print("Loading clusters...")
    clusters = load_clusters()
    print(f"  {len(clusters)} clusters loaded")

    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    niche_embeddings = model.encode(NICHE_KEYWORDS)
    # Normalize for cosine similarity
    niche_embeddings = niche_embeddings / np.linalg.norm(niche_embeddings, axis=1, keepdims=True)

    # Compute max engagement for normalization
    max_engagement = max(c.get("total_engagement", 0) for c in clusters) if clusters else 1

    print("Scoring topics...\n")
    scored = []
    for cluster in clusters:
        v = score_velocity(cluster)
        e = score_engagement(cluster, max_engagement)
        r = score_relevance(cluster, model, niche_embeddings)
        n = score_novelty(cluster)

        composite = (
            WEIGHTS["velocity"] * v +
            WEIGHTS["engagement"] * e +
            WEIGHTS["relevance"] * r +
            WEIGHTS["novelty"] * n
        )

        cluster["scores"] = {
            "velocity": round(v, 3),
            "engagement": round(e, 3),
            "relevance": round(r, 3),
            "novelty": round(n, 3),
            "composite": round(composite, 3),
        }
        cluster["content_type"] = classify_content_type(cluster)
        scored.append(cluster)

    # Filter by relevance threshold
    before = len(scored)
    scored = [s for s in scored if s["scores"]["relevance"] >= args.relevance_threshold]
    filtered_out = before - len(scored)
    print(f"  Relevance filter: {before} -> {len(scored)} topics (removed {filtered_out} off-niche)")

    # Sort by composite score
    scored.sort(key=lambda s: s["scores"]["composite"], reverse=True)

    # Take top N
    top_topics = scored[:args.top]

    # Re-rank
    for rank, topic in enumerate(top_topics, 1):
        topic["rank"] = rank

    # Save
    output_path = os.path.join(DATA_DIR, "scored_topics.json")
    output = {
        "scored_at": datetime.now(timezone.utc).isoformat(),
        "weights": WEIGHTS,
        "relevance_threshold": args.relevance_threshold,
        "total_scored": len(scored),
        "top_n": len(top_topics),
        "topics": top_topics,
    }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved top {len(top_topics)} topics to {output_path}")

    # Display
    # Show content type distribution
    type_counts = {}
    for t in top_topics:
        ct = t.get("content_type", "NEWS")
        type_counts[ct] = type_counts.get(ct, 0) + 1
    print(f"\nContent type distribution: {type_counts}")

    print(f"\nTop {len(top_topics)} topics for content creation:")
    print(f"{'Rank':>4} {'Score':>6} {'V':>5} {'E':>5} {'R':>5} {'N':>5} {'Srcs':>4} {'Type':<8} {'Title'}")
    print("-" * 105)
    for t in top_topics:
        s = t["scores"]
        src_count = t["cross_source_count"]
        ct = t.get("content_type", "NEWS")
        print(
            f"{t['rank']:>4} {s['composite']:>6.3f} "
            f"{s['velocity']:>5.2f} {s['engagement']:>5.2f} {s['relevance']:>5.2f} {s['novelty']:>5.2f} "
            f"{src_count:>4} {ct:<8} {t['representative_title'][:50]}"
        )


if __name__ == "__main__":
    main()
