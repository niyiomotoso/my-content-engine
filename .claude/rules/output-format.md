---
paths:
  - "outputs/**/*"
---

# Output Format Rules

- Weekly outputs go in `outputs/YYYY-WNN/` (e.g., `outputs/2026-W09/`)
- Each week folder contains:
  - `trends.json` -- All scored topics
  - `scripts.json` -- Generated scripts with hooks, captions, comment prompts
  - `summary.md` -- Human-readable summary for quick review
- Also maintain `outputs/latest/` pointing to the most recent week
- Scripts in scripts.json follow this structure per entry:
  - topic, angle, hooks (array of 3), script, caption, comment_prompts (array of 3), trend_score, scriptability_score
