---
name: generate-scripts
description: Generate ready-to-shoot 60-second video scripts in the creator's voice for top trending topics. Use after extract-angles has been run and voice pack exists.
allowed-tools: Bash(python *), Read, Write, WebSearch
---

Generate video scripts in the creator's voice.

## Context (loaded automatically)
- Voice guide: !`cat voice/STYLE_GUIDE.md 2>/dev/null || echo "Voice pack not built yet. Run /build-voice-pack first."`
- Hook patterns: !`cat voice/HOOK_PATTERNS.md 2>/dev/null || echo "No hook patterns yet."`
- CTA patterns: !`cat voice/CTA_PATTERNS.md 2>/dev/null || echo "No CTA patterns yet."`

## Instructions

1. Read `data/angles.json` for the scored topics and angles
2. Check the `content_type` of each topic. **Enforce content mix:** at least 30% of generated scripts (4+ out of 14) must be HOW_TO or ROUNDUP type — tutorial, how-to, step-by-step, or tool roundup content. If the top topics are all NEWS, look further down the list for HOW_TO/ROUNDUP topics. The creator is NOT a news reporter — he's a practical educator.
3. For each of the top 10-14 topics, retrieve similar past scripts for voice matching:
   - Run: `cd pipelines && python retrieve_similar.py "TOPIC TITLE" -n 3`
   - Read the output to see how the creator has written about similar subjects
4. **Web search** each topic to gather fresh facts, statistics, and real-world examples to include in the script
5. For each topic, using the best angle, generate:

   - **3 hook options** (each using a DIFFERENT pattern from the creator's hook patterns file — e.g., one Bold Claim, one "What if", one "Did you know". Use the FULL range of patterns including originals like Bold Claim, Personal Story, List Intro, Problem/Pain Point, Direct Challenge, and newer ones like Imagine, Did you know, If there is. Vary across all scripts in the batch so not every script leads with the same style.)
   - **Full script** (~150-200 words) following this structure:
     - **Hook**: Attention-grabbing first line
     - **Journey Line**: Why this matters to the viewer
     - **Story**: The core content with facts and examples
     - **Reality Check**: Honest take / nuance / what most people miss
     - **CTA**: Call to action using the creator's CTA patterns
   - **Social media caption** (platform-appropriate)
   - **3 comment prompts** (questions to drive engagement)
   - **Sources**: traceable URLs from the original trending items in `data/scored_topics.json` (the actual Reddit, HN, and YouTube links that surfaced the topic). Include 2-4 URLs per script.

6. For HOW_TO scripts, structure as: Hook → Problem → Step-by-step solution (3-5 steps) → Result/CTA. For ROUNDUP scripts, structure as: Hook → List (numbered items) → Standout pick → CTA.

7. Voice matching checklist for EVERY script:
   - Does it sound conversational, not formal?
   - Does it use "you" and "your" directly?
   - Does it include a practical takeaway?
   - Does it use analogies to explain complex ideas?
   - Would the creator actually say this out loud?
   - Is it 150-200 words? (Not too short, not too long)

8. Save all scripts to `outputs/latest/scripts.json` — include `content_type` field per script
9. Save a human-readable summary to `outputs/latest/summary.md`
10. Save a readable markdown version to `outputs/latest/scripts.md` with full scripts formatted for easy reading. Each script section should include a `### Sources` block with the traceable URLs as clickable links.
11. Present the scripts for review, noting the content mix (e.g., "8 NEWS, 4 HOW_TO, 2 ROUNDUP")
