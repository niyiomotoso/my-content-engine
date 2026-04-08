---
paths:
  - "pipelines/**/*.py"
---

# Pipeline Conventions

- All pipeline scripts save output as JSON to the `data/` directory
- Every JSON output uses a consistent schema with these common fields: title, text, score, source, timestamp, engagement
- Scripts should handle errors gracefully -- if a source is down, log the error and return an empty list
- Never hardcode API credentials -- use environment variables if needed
- Reddit uses public JSON endpoints (no auth required)
- Print progress to stdout (e.g., "Collected 150 posts from r/artificial")
