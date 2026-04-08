"""
Score and rank clustered topics (lightweight, no torch required).
Uses TF-IDF cosine similarity instead of sentence-transformers.

Usage:
    python pipelines/score_topics_lite.py [--top 30] [--relevance-threshold 0.15]

Output:
    data/scored_topics.json
"""

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

WEIGHTS = {
    "velocity": 0.30,
    "engagement": 0.25,
    "relevance": 0.30,
    "novelty": 0.15,
}

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
    path = os.path.join(DATA_DIR, "clustered_topics.json")
    if not os.path.exists(path):
        print("Error: clustered_topics.json not found. Run cluster_topics.py first.")
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    return data.get("clusters", [])


def score_velocity(cluster: dict) -> float:
    cross_source = cluster.get("cross_source_count", 1)
    num_items = cluster.get("num_items", 1)
    source_score = min(cross_source / 4.0, 1.0)
    volume_score = min(math.log(num_items + 1) / math.log(51), 1.0)
    return 0.7 * source_score + 0.3 * volume_score


def score_engagement(cluster: dict, max_engagement: float) -> float:
    engagement = cluster.get("total_engagement", 0)
    if max_engagement <= 0 or engagement <= 0:
        return 0.0
    return min(math.log(engagement + 1) / math.log(max_engagement + 1), 1.0)


def score_relevance_tfidf(cluster: dict, vectorizer: TfidfVectorizer, niche_vectors) -> float:
    title = cluster.get("representative_title", "")
    keywords = " ".join(cluster.get("keywords", []))
    sample_titles = " ".join(
        item["title"] for item in cluster.get("items", [])[:5]
    )
    cluster_text = f"{title} {keywords} {sample_titles}"

    cluster_vec = vectorizer.transform([cluster_text])
    similarities = cosine_similarity(cluster_vec, niche_vectors)[0]
    return float(np.max(similarities))


def score_novelty(cluster: dict) -> float:
    num_items = cluster.get("num_items", 1)
    keywords = cluster.get("keywords", [])
    if num_items <= 15:
        size_score = 1.0
    elif num_items <= 30:
        size_score = 0.7
    else:
        size_score = 0.4
    avg_keyword_len = np.mean([len(k) for k in keywords]) if keywords else 0
    keyword_score = min(avg_keyword_len / 10.0, 1.0)
    return 0.6 * size_score + 0.4 * keyword_score


def classify_content_type(cluster: dict) -> str:
    title = cluster.get("representative_title", "").lower()
    keywords = " ".join(cluster.get("keywords", [])).lower()
    sample_titles = " ".join(
        item.get("title", "").lower() for item in cluster.get("items", [])[:10]
    )
    text = f"{title} {keywords} {sample_titles}"

    howto_signals = [
        "how to", "tutorial", "step by step", "guide", "tips",
        "hack", "hacks", "trick", "tricks", "let me show you",
        "here's how", "walkthrough", "setup", "set up", "workflow",
        "prompt", "prompts for", "use case", "use cases",
        "beginner", "learn how", "teach you",
    ]
    howto_count = sum(1 for s in howto_signals if s in text)

    roundup_signals = [
        "best ", "top ", " tools", " apps", "free ai",
        "roundup", "compared", "comparison", "vs ",
        "you need", "must have", "essential", "worth",
    ]
    roundup_count = sum(1 for s in roundup_signals if s in text)
    number_list = len(re.findall(r'\b\d+\s+(ai|tool|app|way|tip|hack|course|platform|skill)', text))
    roundup_count += number_list

    news_signals = [
        "launch", "announce", "release", "drop", "unveil",
        "acquire", "deal", "funding", "raise", "ipo",
        "earning", "report", "billion", "million",
        "ban", "sue", "fire", "resign", "deadline",
    ]
    news_count = sum(1 for s in news_signals if s in text)

    opinion_signals = [
        "opinion", "debate", "overblown", "controversial",
        "think", "believe", "predict", "warn", "fear",
        "destroy", "kill", "end of", "death of",
    ]
    opinion_count = sum(1 for s in opinion_signals if s in text)

    scores = {
        "HOW_TO": howto_count * 1.2,
        "ROUNDUP": roundup_count * 1.1,
        "NEWS": news_count,
        "OPINION": opinion_count,
    }
    best_type = max(scores, key=scores.get)
    if scores[best_type] == 0:
        return "NEWS"
    return best_type


def main():
    parser = argparse.ArgumentParser(description="Score and rank topics (lightweight)")
    parser.add_argument("--top", type=int, default=20, help="Number of top topics to output")
    parser.add_argument("--relevance-threshold", type=float, default=0.15,
                        help="Minimum relevance score to keep")
    args = parser.parse_args()

    print("Loading clusters...")
    clusters = load_clusters()
    print(f"  {len(clusters)} clusters loaded")

    # Build TF-IDF vectorizer from all cluster texts + niche keywords
    all_texts = []
    for c in clusters:
        title = c.get("representative_title", "")
        kw = " ".join(c.get("keywords", []))
        samples = " ".join(item["title"] for item in c.get("items", [])[:5])
        all_texts.append(f"{title} {kw} {samples}")
    all_texts.extend(NICHE_KEYWORDS)

    print("Building TF-IDF model for relevance scoring...")
    vectorizer = TfidfVectorizer(
        max_features=5000, stop_words="english",
        ngram_range=(1, 2), min_df=1,
    )
    vectorizer.fit(all_texts)
    niche_vectors = vectorizer.transform(NICHE_KEYWORDS)

    max_engagement = max(c.get("total_engagement", 0) for c in clusters) if clusters else 1

    print("Scoring topics...\n")
    scored = []
    for cluster in clusters:
        v = score_velocity(cluster)
        e = score_engagement(cluster, max_engagement)
        r = score_relevance_tfidf(cluster, vectorizer, niche_vectors)
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

    before = len(scored)
    scored = [s for s in scored if s["scores"]["relevance"] >= args.relevance_threshold]
    filtered_out = before - len(scored)
    print(f"  Relevance filter: {before} -> {len(scored)} topics (removed {filtered_out} off-niche)")

    scored.sort(key=lambda s: s["scores"]["composite"], reverse=True)
    top_topics = scored[:args.top]

    for rank, topic in enumerate(top_topics, 1):
        topic["rank"] = rank

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
