---
name: weekly-batch
description: Run the full weekly content pipeline end-to-end. Collects trends, scores topics, generates angles, and writes scripts. Use this for your weekly content planning session.
allowed-tools: Bash(python *), Read, Write, Glob, Grep, WebSearch
---

Run the complete weekly content pipeline.

## Voice Context (loaded automatically)
!`cat voice/STYLE_GUIDE.md 2>/dev/null || echo "No voice pack. Run /build-voice-pack first."`

## Pipeline Steps

### Step 1: Collect trending data
Run all ingest scripts. If any source fails, report the error but continue.
- `python pipelines/ingest_reddit.py`
- `python pipelines/ingest_hn.py`
- `python pipelines/ingest_youtube.py`
- `python pipelines/ingest_trends.py`

Report: how many posts collected from each source.

### Step 2: Cluster and deduplicate
- `python pipelines/cluster_topics.py`

Report: how many unique topic clusters found.

### Step 3: Score and rank topics
- `python pipelines/score_topics.py --top 30`

Report top 10 scored topics.

### Step 4: Generate angles
For the top 15 topics:
- Note each topic's `content_type` (NEWS, HOW_TO, ROUNDUP, OPINION)
- **Web search** each topic to understand the current conversation
- Generate 4 angles each (AGREE, DISAGREE, CONTRARIAN, PRACTICAL)
- Score scriptability. Filter to topics scoring above 0.6
- Save to `data/angles.json`

### Step 5: Generate scripts
For the top 10-14 scriptable topics:
- **Enforce content mix:** at least 30% of scripts must be HOW_TO or ROUNDUP type (tutorials, tool walkthroughs, step-by-step guides, tool roundups). If not enough HOW_TO/ROUNDUP topics exist, look further down the scored list or reframe a topic as a tutorial.
- Retrieve similar past scripts: `cd pipelines && python retrieve_similar.py "TOPIC" -n 3`
- **Web search** for fresh facts and examples
- Generate: 3 hook options, full script (~150-200 words), caption, 3 comment prompts, traceable source URLs (2-4 per script, pulled from the original Reddit/HN/YouTube links in `data/scored_topics.json`)
- For HOW_TO scripts: use Hook → Problem → Steps (3-5) → Result → CTA structure
- For ROUNDUP scripts: use Hook → Numbered list → Standout pick → CTA structure
- Match the creator's voice from style guide and retrieved examples
- Save to `outputs/YYYY-WNN/scripts.json` and `outputs/latest/scripts.json`

### Step 6: Save outputs
Create output folder: `outputs/YYYY-WNN/` (current year and week number).
Also copy to `outputs/latest/`.
Save: `trends.json`, `scripts.json`, `scripts.md`, `summary.md`.

### Step 7: Present results
Show the summary: how many topics found, how many scripts generated, and list each script's topic + hook.
