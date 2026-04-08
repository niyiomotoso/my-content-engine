---
name: discover-trends
description: Collect trending AI/tech/finance topics from Reddit, Hacker News, YouTube, and Google Trends over the past 7 days. Use when asked to find what's trending or gather fresh content ideas.
argument-hint: "[days]"
allowed-tools: Bash(python *), Read, Write, Grep
---

Run the trend discovery pipeline to collect data from all sources.

1. Execute `python pipelines/ingest_reddit.py` to collect from Reddit
2. Execute `python pipelines/ingest_hn.py` to collect from Hacker News
3. Execute `python pipelines/ingest_youtube.py` to collect from YouTube
4. Execute `python pipelines/ingest_trends.py` to collect from Google Trends
5. If any source fails, report the error but continue with the remaining sources
6. Read the outputs in `data/` and report how many posts were collected from each source
7. Summarize the top 20 most-discussed topics across all sources
