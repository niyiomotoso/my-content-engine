---
name: extract-angles
description: Generate 4 content angles for each top trending topic. Use after score-topics has been run.
allowed-tools: Bash(python *), Read, Write, WebSearch
---

Generate content angles for the top scored topics.

1. Read `data/scored_topics.json`
2. Note each topic's `content_type` field (NEWS, HOW_TO, ROUNDUP, OPINION). Ensure the final selection includes a good mix — **at least 30% should be HOW_TO or ROUNDUP type** (tutorial/practical content). If needed, pull in lower-ranked HOW_TO/ROUNDUP topics to meet this threshold.
3. For each of the top 15 topics:
   a. **Web search** the topic to understand what people are actually saying about it — find the main opinions, controversies, and practical implications
   b. Generate exactly 4 angles:
      - **AGREE**: Side with the majority opinion but add unique insight
      - **DISAGREE**: Push back on the consensus with a credible counter-argument
      - **CONTRARIAN**: Take a surprising, counterintuitive position
      - **PRACTICAL**: Skip the debate entirely, give actionable advice

3. For each angle, provide:
   - A compelling hook (first sentence of the script)
   - A one-sentence thesis
   - The target emotion (excitement, outrage, curiosity, fear, empowerment, etc.)
   - Risk level: "safe", "moderate", or "spicy"
   - Key facts or references discovered from web search

5. Also score each topic's scriptability (0-1):
   - Emotional charge
   - Controversy level
   - Practical takeaway potential
   - Can it be explained in 60 seconds?

6. Filter out topics with scriptability below 0.6
7. Include each topic's `content_type` in the output
8. Save to `data/angles.json`
9. Present the top 10-14 topics with their best angles, noting the content type mix
