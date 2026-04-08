"""
Index creator's past scripts into ChromaDB for RAG-based voice matching.

Reads all .txt files from voice/samples/, embeds them, and stores in a
persistent ChromaDB collection. Also provides a retrieval function for
finding similar past scripts given a new topic.

Usage:
    python pipelines/index_voice.py

Output:
    voice_db/ (ChromaDB persistent store)
"""

import os
import re
import sys

import chromadb
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SAMPLES_DIR = os.path.join(PROJECT_ROOT, "voice", "samples")
DB_DIR = os.path.join(PROJECT_ROOT, "voice_db")
COLLECTION_NAME = "voice_scripts"


def load_scripts() -> list[dict]:
    """Load all script files from voice/samples/."""
    scripts = []
    for fname in sorted(os.listdir(SAMPLES_DIR)):
        if not fname.endswith(".txt") or fname == ".gitkeep":
            continue
        filepath = os.path.join(SAMPLES_DIR, fname)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # Parse topic from first line
        lines = content.strip().split("\n")
        topic = ""
        body = content
        if lines and lines[0].startswith("Topic:"):
            topic = lines[0].replace("Topic:", "").strip()
            body = "\n".join(lines[1:]).strip()

        # Strip hashtags from body for cleaner embedding
        body_clean = re.sub(r"#\w+", "", body).strip()

        scripts.append({
            "id": fname.replace(".txt", ""),
            "filename": fname,
            "topic": topic,
            "body": body_clean,
            "full_text": content,
            "word_count": len(body_clean.split()),
        })

    return scripts


def index_scripts(scripts: list[dict]) -> None:
    """Embed and store scripts in ChromaDB."""
    client = chromadb.PersistentClient(path=DB_DIR)

    # Delete existing collection if it exists (full re-index)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = []
    documents = []
    metadatas = []

    for script in scripts:
        ids.append(script["id"])
        # Embed topic + body for richer matching
        documents.append(f"{script['topic']}\n\n{script['body']}")
        metadatas.append({
            "filename": script["filename"],
            "topic": script["topic"],
            "word_count": script["word_count"],
        })

    print(f"  Indexing {len(ids)} scripts into ChromaDB...", end=" ", flush=True)
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print("done")


def query_similar(topic: str, n_results: int = 5) -> list[dict]:
    """Retrieve the most similar past scripts for a given topic.

    This function is used by the script generation pipeline to find
    voice samples that match the current topic.
    """
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    results = collection.query(
        query_texts=[topic],
        n_results=n_results,
    )

    similar = []
    for i in range(len(results["ids"][0])):
        similar.append({
            "id": results["ids"][0][i],
            "topic": results["metadatas"][0][i]["topic"],
            "distance": results["distances"][0][i] if results.get("distances") else None,
            "text": results["documents"][0][i],
        })

    return similar


def main():
    print("Loading scripts from voice/samples/...")
    scripts = load_scripts()
    print(f"  Found {len(scripts)} scripts")

    if not scripts:
        print("No scripts found. Add .txt files to voice/samples/ first.")
        sys.exit(1)

    # Show stats
    word_counts = [s["word_count"] for s in scripts]
    print(f"  Word counts: min={min(word_counts)}, max={max(word_counts)}, avg={sum(word_counts)//len(word_counts)}")

    print("\nIndexing into ChromaDB...")
    index_scripts(scripts)

    # Test retrieval
    print("\nTesting retrieval...")
    test_queries = [
        "AI tools for productivity",
        "ChatGPT tips and tricks",
        "future of AI and jobs",
    ]
    for query in test_queries:
        results = query_similar(query, n_results=3)
        print(f"\n  Query: '{query}'")
        for r in results:
            dist = f"{r['distance']:.3f}" if r['distance'] is not None else "?"
            print(f"    [{dist}] {r['topic']}")

    print(f"\nVoice DB ready at {DB_DIR}/")


if __name__ == "__main__":
    main()
