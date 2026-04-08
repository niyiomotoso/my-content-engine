"""
One-time script to parse the master CSV and split into individual
voice sample files for the RAG pipeline.

Input:  scripts_master.csv
Output: voice/samples/01_topic_name.txt (one per script)
"""

import csv
import os
import re

INPUT_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts_master.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voice", "samples")


def slugify(text: str, max_len: int = 50) -> str:
    """Turn a topic title into a safe filename slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    return text[:max_len].rstrip("_")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        scripts = list(reader)

    print(f"Loaded {len(scripts)} scripts from CSV\n")

    for i, row in enumerate(scripts, 1):
        topic = row.get("topic", "").strip()
        script = row.get("script", "").strip()
        hashtags = row.get("hashtags", "").strip()

        if not topic or not script:
            print(f"  Skipping row {i}: empty topic or script")
            continue

        slug = slugify(topic)
        filename = f"{i:02d}_{slug}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Write in a clean format: topic header, blank line, script body, blank line, hashtags
        with open(filepath, "w", encoding="utf-8") as out:
            out.write(f"Topic: {topic}\n\n")
            out.write(script)
            if hashtags:
                out.write(f"\n\n{hashtags}")
            out.write("\n")

        word_count = len(script.split())
        print(f"  {filename} ({word_count} words)")

    print(f"\nDone. {len(scripts)} files written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
