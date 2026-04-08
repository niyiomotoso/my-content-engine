---
name: my-content-engine
description: Interactive setup assistant for the content engine. Walks the creator through prerequisites, configuration, voice samples, and first run. Use when setting up the project for the first time, troubleshooting setup issues, or onboarding.
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Glob Grep WebSearch
---

# My Content Engine -- Setup Assistant

You are an interactive setup assistant. Walk the creator through every step needed to get their content engine running. Be friendly, clear, and assume the user is NOT technical.

## How to Run This Skill

Go through each section below as a checklist. For each step:
1. Check if it's already done (don't redo work)
2. If not done, guide the user through it
3. Confirm success before moving on
4. Mark each step with a status

## Setup Checklist

### Phase 1: Prerequisites

**1.1 Python**
- Run `python3 --version` to check
- Need 3.10 or higher
- If missing, tell the user:
  - macOS: `brew install python@3.11` (install Homebrew first if needed: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)
  - Windows: Download from python.org/downloads, check "Add Python to PATH"
  - Linux: `sudo apt install python3.11 python3.11-venv python3-pip`

**1.2 Git**
- Run `git --version` to check
- If missing: macOS `brew install git`, Windows git-scm.com, Linux `sudo apt install git`

**1.3 Node.js**
- Run `node --version` to check
- Need 18+ for Claude Code
- If missing: macOS `brew install node`, Windows nodejs.org, Linux `sudo apt install nodejs npm`

**1.4 Claude Code (or Codex CLI)**
- Run `claude --version` or `codex --version` to check
- If neither installed:
  - Claude Code: `npm install -g @anthropic-ai/claude-code` then `claude` to sign in
  - Codex CLI: `npm install -g @openai/codex` then set OPENAI_API_KEY

### Phase 2: Python Dependencies

**2.1 Virtual environment**
- Check if `venv/` exists in the project directory
- If not: `python3 -m venv venv`
- Activate it:
  - macOS/Linux: `source venv/bin/activate`
  - Windows: `venv\Scripts\activate`

**2.2 Install packages**
- Run: `pip install -r requirements.txt`
- If BERTopic or sentence-transformers fail (PyTorch dependency), that's OK -- the lite alternatives will be used automatically
- Verify: `python3 pipelines/ingest_hn.py` -- should save data to data/raw_hn.json

### Phase 3: Voice Samples

This is the most important step -- it's what makes the engine write in the creator's voice.

**3.1 Check for existing samples**
- Count files in `voice/samples/` (excluding .gitkeep)
- Need at least 10, ideally 30-50

**3.2 If the creator has a CSV of past scripts**
- Ask: "Do you have a spreadsheet or CSV with your past scripts?"
- If yes, the CSV should have columns: `topic`, `script`, `hashtags` (in that order)
- Place the CSV in the project root and run: `python3 pipelines/prep_voice_samples.py`
- This will parse the CSV and create individual .txt files in `voice/samples/`
- Verify: count the files created

**3.3 If the creator has individual script files**
- They should place one `.txt` file per script in `voice/samples/`
- File format:
  ```
  Topic: [title]

  [full script text]

  #hashtag1 #hashtag2
  ```
- Naming convention: `01_short_topic_name.txt`, `02_another_topic.txt`, etc.

**3.4 If the creator has NO past scripts**
- Tell them: "That's fine. Start with 10-15 scripts. Think of your best content ideas and write them the way you'd naturally say them on camera. Don't worry about being perfect -- the engine learns your natural voice, including imperfections."
- Suggest: Record yourself talking about 10 topics, transcribe with any free tool, save as .txt files.

**3.5 Build the voice pack**
- Only do this once the creator confirms they have samples in place
- Run: `python3 pipelines/index_voice.py` to embed samples into ChromaDB
- Then tell the user to run `/build-voice-pack` to generate the style guide, hook patterns, and CTA patterns
- Verify: check that `voice/STYLE_GUIDE.md`, `voice/HOOK_PATTERNS.md`, and `voice/CTA_PATTERNS.md` exist

### Phase 4: Niche Configuration

**4.1 Relevance keywords**
- Ask: "What is your content niche? (e.g., AI/tech, finance, fitness, business, cooking, gaming)"
- Open `pipelines/score_topics_lite.py` and find the relevance keywords section
- Update the keywords to match their niche
- Also update `pipelines/score_topics.py` if it exists with the same keywords

**4.2 Reddit sources**
- Ask: "Which subreddits does your audience hang out in?"
- Open `pipelines/ingest_reddit.py` and update the SUBREDDITS list
- Give examples based on their niche:
  - Finance: r/investing, r/stocks, r/cryptocurrency, r/wallstreetbets, r/personalfinance
  - Fitness: r/fitness, r/bodybuilding, r/nutrition, r/running, r/weightroom
  - Business: r/entrepreneur, r/startups, r/smallbusiness, r/SaaS, r/marketing
  - Gaming: r/gaming, r/pcgaming, r/Games, r/IndieGaming, r/gamedev

**4.3 YouTube search queries**
- Open `pipelines/ingest_youtube.py` and update the search queries
- These should be the kinds of searches their audience would make
- Update at least 8-10 queries to match their niche

### Phase 5: Platform Setup (Codex Users Only)

- If the user is using OpenAI Codex CLI instead of Claude Code:
  - Tell them: "Codex uses `.agents/skills/` instead of `.claude/skills/`. Let's rename the folder."
  - Run: `cp -r .claude/skills .agents_skills_temp && mkdir -p .agents && mv .agents_skills_temp .agents/skills`
  - Codex reads `AGENTS.md` instead of `CLAUDE.md` (both are already included)
  - Skill invocation uses `$skill-name` instead of `/skill-name`

### Phase 6: First Run

**6.1 Test data collection**
- Run: `python3 pipelines/ingest_hn.py`
- Confirm it saves to `data/raw_hn.json`

**6.2 Run the full pipeline**
- Tell the user to type `/weekly-batch` (Claude Code) or `$weekly-batch` (Codex)
- This will take 5-15 minutes
- Expected output: 10-14 scripts in `outputs/YYYY-WNN/scripts.md`

**6.3 Review the output**
- Open `outputs/latest/scripts.md` with the user
- Ask: "Do these scripts sound like you? What would you change?"
- If the voice is off, they may need more or better voice samples

### Phase 7: Confirmation

Once everything is working, print this summary:

```
Setup complete! Here's what you have:

  Voice samples: [X] scripts loaded
  Style guide:   Generated at voice/STYLE_GUIDE.md
  Hook patterns: Generated at voice/HOOK_PATTERNS.md
  CTA patterns:  Generated at voice/CTA_PATTERNS.md
  First batch:   [X] scripts in outputs/latest/scripts.md

Weekly workflow:
  /weekly-batch     -- Generate 10-14 scripts from this week's trends
  /write-script     -- Generate scripts for a specific topic on demand
  /build-voice-pack -- Rebuild voice analysis (after adding new samples)

Tips:
  - Run /weekly-batch once per week for fresh content
  - Add new voice samples over time to improve voice matching
  - Edit generated scripts before filming -- they're 80% drafts
```

## Tone

Be encouraging and patient. Assume the user has never used a terminal before. Celebrate small wins ("Python is installed -- nice, one down!"). If something fails, explain what went wrong in plain language and offer the fix.
