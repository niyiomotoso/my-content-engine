---
name: score-topics
description: Score and rank collected trending topics by velocity, engagement, relevance to AI/tech/finance, and novelty. Use after discover-trends has been run.
allowed-tools: Bash(python *), Read, Write
---

Score and rank the collected topics.

1. Execute `python pipelines/cluster_topics.py` to deduplicate and cluster raw data
2. Read `data/clustered_topics.json`
3. For each topic, evaluate:
   - **Velocity**: Is it accelerating (rising fast) or already peaked?
   - **Engagement**: Total upvotes, comments, shares across sources
   - **Relevance**: How closely does it relate to AI, tech, or finance?
   - **Novelty**: Is this genuinely new, or a rehash of old news?
   - **Scriptability**: Can this be explained in 60 seconds with a clear hook?
4. Assign scores (0-1) for each dimension
5. Compute overall score: velocity*0.35 + engagement*0.25 + relevance*0.25 + novelty*0.15
6. Save the ranked list to `data/scored_topics.json`
7. Present the top 10 topics with scores and reasoning
