"""
Retrieve similar past scripts from the voice DB for a given topic.

Used by the generate-scripts skill to find voice samples that match
the current topic for RAG-based script generation.

Usage:
    python pipelines/retrieve_similar.py "AI replacing office jobs"
    python pipelines/retrieve_similar.py --topics-file data/angles.json

Output:
    Prints similar scripts to stdout (for Claude to read)
    Optionally saves to data/voice_context.json
"""

import argparse
import json
import os
import sys

from index_voice import query_similar

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


def retrieve_for_topic(topic: str, n: int = 3) -> list[dict]:
    """Get similar past scripts for a single topic."""
    return query_similar(topic, n_results=n)


def retrieve_for_angles_file(filepath: str, n: int = 3) -> dict:
    """Get similar past scripts for all topics in an angles file."""
    with open(filepath) as f:
        data = json.load(f)

    results = {}
    topics = data.get("topics", [])
    for topic_entry in topics:
        title = topic_entry.get("representative_title", "")
        if not title:
            continue
        similar = query_similar(title, n_results=n)
        results[title] = similar
        print(f"\n--- Similar scripts for: {title} ---")
        for s in similar:
            dist = f"{s['distance']:.3f}" if s.get('distance') else "?"
            print(f"  [{dist}] {s['topic']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Retrieve similar voice samples")
    parser.add_argument("topic", nargs="?", help="Topic to search for")
    parser.add_argument("--topics-file", help="JSON file with topics to retrieve for")
    parser.add_argument("-n", type=int, default=3, help="Number of results (default: 3)")
    parser.add_argument("--save", help="Save results to this JSON file")
    args = parser.parse_args()

    if args.topics_file:
        results = retrieve_for_angles_file(args.topics_file, args.n)
    elif args.topic:
        results = retrieve_for_topic(args.topic, args.n)
        print(f"\nSimilar scripts for: '{args.topic}'\n")
        for r in results:
            dist = f"{r['distance']:.3f}" if r.get('distance') else "?"
            print(f"  [{dist}] {r['topic']}")
            # Print first 200 chars of the script body
            text = r.get("text", "")
            body_start = text.find("\n\n")
            if body_start > 0:
                body = text[body_start:].strip()[:200]
            else:
                body = text[:200]
            print(f"         {body}...")
            print()
    else:
        parser.print_help()
        sys.exit(1)

    if args.save:
        output_path = os.path.join(PROJECT_ROOT, args.save)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
