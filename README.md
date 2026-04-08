# My Content Engine

A weekly content pipeline that finds trending topics, scores them, and generates ready-to-shoot 60-second video scripts -- in **your** voice, not generic AI.

Built to run with **Claude Code** or **OpenAI Codex CLI**. You type one command, and it delivers 10-14 polished scripts with hooks, captions, and engagement prompts.

---

## What It Does

Every week, the engine:

1. **Collects** 2,000+ trending posts from Reddit, Hacker News, YouTube, and Google Trends
2. **Clusters** them into ~140 unique topic groups (removes duplicates across sources)
3. **Scores** each topic on velocity, engagement, relevance to your niche, and novelty
4. **Generates 4 angles** per topic (Agree, Disagree, Contrarian, Practical)
5. **Writes scripts** (~150-200 words each) matched to your personal voice using RAG (retrieval-augmented generation) against your past content

You also get an on-demand mode: paste any topic, article, or idea, and it generates 2-3 script variations instantly.

---

## What You Need Before Starting

### Required

| Tool | What It Is | How to Get It |
|------|-----------|---------------|
| **Python 3.10+** | Runs the data collection and clustering scripts | See [Python install](#install-python) below |
| **Git** | Version control, needed to clone this repo | See [Git install](#install-git) below |
| **An AI coding agent** | Runs the skills/commands that orchestrate everything | See [AI agent setup](#set-up-your-ai-coding-agent) below |

### Supported AI Agents

| Agent | Skill Directory | Invoke Command | Project Config |
|-------|----------------|---------------|----------------|
| **Claude Code** | `.claude/skills/` | `/skill-name` | `CLAUDE.md` |
| **OpenAI Codex CLI** | `.agents/skills/` | `$skill-name` | `AGENTS.md` |

This repo ships with skills in `.claude/skills/`. If you use **Codex CLI**, see [Platform Setup for Codex Users](#platform-setup-for-codex-users) to rename the folder.

---

## Step-by-Step Setup

### Install Python

You need Python 3.10 or higher. Check if you already have it:

```bash
python3 --version
```

If you see `Python 3.10` or higher, you're good. If not:

**macOS:**
```bash
# Install Homebrew first if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install Python
brew install python@3.11
```

**Windows:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the latest Python 3.11+ installer
3. **Important:** Check the box that says "Add Python to PATH" during installation
4. Open a new Command Prompt or PowerShell and verify: `python --version`

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

### Install Git

Check if you have it:
```bash
git --version
```

If not:

**macOS:** `brew install git` (or it installs automatically when you use it)

**Windows:** Download from [git-scm.com](https://git-scm.com/download/win). Use the default installer options.

**Linux:** `sudo apt install git`

### Set Up Your AI Coding Agent

You need **one** of these. Pick whichever you prefer.

#### Option A: Claude Code (by Anthropic)

1. You need Node.js 18+ first:
   - **macOS:** `brew install node`
   - **Windows:** Download from [nodejs.org](https://nodejs.org/)
   - **Linux:** `sudo apt install nodejs npm`

2. Install Claude Code:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

3. Launch it once to sign in:
   ```bash
   claude
   ```
   Follow the prompts to authenticate with your Anthropic account. You need a Claude Pro ($20/month) or Max subscription.

4. For full documentation: [code.claude.com/docs](https://code.claude.com/docs)

#### Option B: OpenAI Codex CLI

1. You need Node.js 22+ first (see links above).

2. Install Codex:
   ```bash
   npm install -g @openai/codex
   ```

3. Set your OpenAI API key:
   ```bash
   # macOS/Linux
   export OPENAI_API_KEY="your-key-here"

   # Windows (PowerShell)
   $env:OPENAI_API_KEY = "your-key-here"
   ```
   Get your API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

4. Launch it:
   ```bash
   codex
   ```

5. For full documentation: [developers.openai.com/codex](https://developers.openai.com/codex)

---

### Clone This Repo

```bash
git clone https://github.com/niyiomotoso/my-content-engine.git
cd my-content-engine
```

### Install Python Dependencies

Create a virtual environment (keeps things clean) and install:

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> **If you get errors with `bertopic` or `sentence-transformers`** (they require PyTorch, which is large), the engine includes lightweight alternatives that use scikit-learn instead. These run automatically if the heavier libraries aren't available. You can skip the errors and continue.

### Verify the Setup

Run a quick test to make sure data collection works:

```bash
python3 pipelines/ingest_hn.py
```

You should see output like:
```
Collecting Hacker News stories...
  topstories: 200 IDs
  ...
Saved 459 stories to data/raw_hn.json
```

If that works, your Python environment is ready.

### Run the Interactive Setup Assistant (Recommended)

The easiest way to complete the rest of the setup is to use the built-in setup skill. It walks you through everything interactively -- checking prerequisites, configuring your niche, setting up voice samples, and running your first batch.

Open your AI agent in the project directory and run:

**Claude Code:**
```bash
cd my-content-engine
claude
```
Then type: `/my-content-engine`

The assistant will guide you through each step, check what's already done, and help you fix anything that's missing. If you prefer to do it manually, follow the steps below.

---

## Customize It: Make It Yours

This is where the engine becomes **your** content engine, not a generic tool.

### Step 1: Add Your Voice Samples

The engine learns your voice from your past content. You need **30-50 of your best past scripts** (the words you actually said on camera or in a podcast).

Create one `.txt` file per script in `voice/samples/`:

```
voice/samples/
├── 01_topic_of_first_script.txt
├── 02_topic_of_second_script.txt
├── 03_topic_of_third_script.txt
...
```

**Each file should contain:**
```
Topic: [Short title of the content]

[The full script text -- exactly what you said or would say on camera]

#hashtag1 #hashtag2 #hashtag3
```

**Tips for picking good samples:**
- Choose scripts that represent your **best** and most **typical** content
- Include a mix of content types: tutorials, news reactions, tool reviews, opinion pieces
- Include scripts that show your unique personality, humor, or phrases
- 30 is the minimum. 50 is ideal. More than 100 works too.

**If you have your scripts in a spreadsheet:** You can bulk-import them. Create a CSV file with three columns -- `topic`, `script`, `hashtags` -- and place it in the project root as `scripts_master.csv`. See `scripts_master_sample.csv` in this repo for the exact format with 3 example scripts. Then run:

```bash
python3 pipelines/prep_voice_samples.py
```

This parses the CSV and creates individual `.txt` files in `voice/samples/` automatically.

**If you don't have past scripts:** Start with 10-15. Write them the way you naturally talk. Record yourself riffing on topics and transcribe it. The engine gets better as you add more samples over time.

### Step 2: Build Your Voice Pack

Open your AI agent in the project directory:

**Claude Code:**
```bash
cd my-content-engine
claude
```
Then type: `/build-voice-pack`

**Codex CLI:**
```bash
cd my-content-engine
codex
```
Then type: `$build-voice-pack`

This analyzes all your voice samples and generates three files:
- `voice/STYLE_GUIDE.md` -- Your tone, personality, language patterns, signature phrases
- `voice/HOOK_PATTERNS.md` -- How you typically open your content (extracted from your samples)
- `voice/CTA_PATTERNS.md` -- How you typically close your content (extracted from your samples)

**You only need to run this once**, unless you add significantly more voice samples later.

### Step 3: Configure Your Niche

The engine needs to know what topics are relevant to **your** audience. Open the scoring script and update the relevance keywords:

**File:** `pipelines/score_topics_lite.py` (or `score_topics.py`)

Find the section with relevance keywords and update them to match your niche. For example:

- **AI/Tech creator:** `ai, chatgpt, llm, openai, google, tech, software, coding, startup`
- **Finance creator:** `finance, investing, stocks, crypto, economy, market, trading, wealth`
- **Fitness creator:** `fitness, workout, nutrition, health, gym, protein, weight loss, muscle`
- **Business creator:** `business, startup, entrepreneur, revenue, marketing, saas, growth`

### Step 4: Configure Your Sources (Optional)

The default sources (Reddit, HN, YouTube, Google Trends) work well for tech/AI content. To change which subreddits are scraped:

**File:** `pipelines/ingest_reddit.py`

Find the `SUBREDDITS` list and replace with subreddits relevant to your niche.

**File:** `pipelines/ingest_youtube.py`

Find the search queries list and update to match your content area.

---

## How to Use It

### Weekly Batch (Your Main Workflow)

This is the one command you run every week. It does everything:

**Claude Code:** `/weekly-batch`

**Codex CLI:** `$weekly-batch`

The engine will:
1. Collect ~2,000 trending items from all sources
2. Cluster them into unique topics
3. Score and rank by relevance to your niche
4. Generate angles for the top topics
5. Write 10-14 full scripts in your voice
6. Save everything to `outputs/YYYY-WNN/`

**Output files:**
```
outputs/2026-W15/
├── scripts.md      # Human-readable scripts (this is what you read)
├── scripts.json    # Structured data (for automation)
├── summary.md      # Pipeline stats and script list
├── trends.json     # All scored topics
└── angles.json     # Angles for each topic
```

Open `scripts.md` to see your scripts. Each one includes:
- 3 hook options (different opening patterns to A/B test)
- The full script (~150-200 words, ~60 seconds spoken)
- A social media caption with hashtags
- 3 comment prompts to drive engagement
- Source URLs for fact-checking

### On-Demand Script Writing

Have a specific topic, brand deal, or idea? Use this instead:

**Claude Code:** `/write-script Your topic or idea here`

**Codex CLI:** `$write-script Your topic or idea here`

You can paste:
- A raw idea: `/write-script Why AI agents are overhyped`
- An article URL: `/write-script https://example.com/article`
- A brand brief: `/write-script [paste the brand email]`
- A rant: `/write-script I'm frustrated that ChatGPT keeps getting worse and I want to talk about it`

It generates 3 script variations:
1. **Rant/Story structure** -- personal take + facts + reality check
2. **List/Steps structure** -- numbered points + standout insight
3. **Question/Answer structure** -- hook as a question + exploration + what most miss

Saved to `outputs/custom/YYYY-MM-DD_topic-slug.md`.

### Running Individual Steps

You can also run each step separately if you want more control:

| Command | What It Does |
|---------|-------------|
| `/discover-trends` or `$discover-trends` | Just collect trending data |
| `/score-topics` or `$score-topics` | Cluster and score (run after discover) |
| `/extract-angles` or `$extract-angles` | Generate angles (run after score) |
| `/generate-scripts` or `$generate-scripts` | Write scripts (run after angles) |
| `/build-voice-pack` or `$build-voice-pack` | Rebuild voice analysis from samples |

---

### Platform Setup for Codex Users

If you are using **OpenAI Codex CLI** instead of Claude Code, you need to rename the skills folder so Codex can find it:

**macOS / Linux:**
```bash
mkdir -p .agents
cp -r .claude/skills .agents/skills
```

**Windows (PowerShell):**
```powershell
mkdir .agents
Copy-Item -Recurse .claude\skills .agents\skills
```

Codex reads `AGENTS.md` for project instructions (already included). Invoke skills with `$skill-name` instead of `/skill-name`.

---

## How It Works Under the Hood

```
┌──────────────────────────────────────────────────────────────┐
│  DATA COLLECTION (Python)                                     │
│  Reddit (1,400+) + HN (480) + YouTube (170) + Trends (40)   │
│  → raw_reddit.json, raw_hn.json, raw_youtube.json, etc.     │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  CLUSTERING (Python: TF-IDF + Agglomerative Clustering)      │
│  2,000+ items → ~140 unique topic clusters                   │
│  Groups duplicates across sources                            │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  SCORING (AI reasoning)                                       │
│  Velocity (0.35) + Engagement (0.25) + Relevance (0.25)     │
│  + Novelty (0.15) = composite score                          │
│  Filters to top 10-15 on-niche topics                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  ANGLE GENERATION (AI + web search)                           │
│  4 angles per topic: AGREE, DISAGREE, CONTRARIAN, PRACTICAL  │
│  Scriptability scoring. Content mix enforcement (30% HOW_TO) │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  SCRIPT WRITING (AI + RAG + web search)                       │
│  1. Retrieve 3 similar past scripts from voice database      │
│  2. Web search for current facts and examples                │
│  3. Generate: hooks + script + caption + comment prompts     │
│  Voice-matched against YOUR style guide                      │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  OUTPUT                                                       │
│  outputs/YYYY-WNN/scripts.md  (human-readable)               │
│  outputs/YYYY-WNN/scripts.json (structured)                  │
│  outputs/custom/   (on-demand scripts)                       │
└──────────────────────────────────────────────────────────────┘
```

### The Voice System (RAG)

This is what makes the engine different from "ask ChatGPT to write a script."

Your past scripts are embedded into a local vector database (ChromaDB). When the engine writes a new script about, say, "AI tools being expensive," it first retrieves the 3 most similar scripts you've written before. Those become the voice reference -- the AI sees exactly how **you** talked about similar topics and matches that style.

On top of that, the `/build-voice-pack` skill extracts patterns from all your scripts:
- **Style guide:** Your tone, word choices, sentence structure, signature phrases
- **Hook patterns:** How you open content (questions, bold claims, stories, etc.)
- **CTA patterns:** How you close content (comment prompts, follow asks, etc.)

The result: scripts that sound like you wrote them, not like a robot.

---

## Project Structure

```
my-content-engine/
├── README.md                    # This file
├── CLAUDE.md                    # Project instructions (Claude Code)
├── AGENTS.md                    # Project instructions (Codex CLI)
├── requirements.txt             # Python dependencies
├── .gitignore
│
├── .claude/                     # Agent skills (Codex users: copy to .agents/)
│   ├── skills/
│   │   ├── my-content-engine/SKILL.md   # Interactive setup assistant
│   │   ├── weekly-batch/SKILL.md        # Full pipeline in one command
│   │   ├── write-script/SKILL.md        # On-demand script from any topic
│   │   ├── discover-trends/SKILL.md     # Collect trending data
│   │   ├── score-topics/SKILL.md        # Cluster and rank topics
│   │   ├── extract-angles/SKILL.md      # Generate 4 angles per topic
│   │   ├── generate-scripts/SKILL.md    # Write voice-matched scripts
│   │   └── build-voice-pack/SKILL.md    # Analyze samples, generate style guide
│   └── rules/
│       ├── output-format.md
│       └── pipeline-rules.md
│
├── pipelines/                   # Python data scripts
│   ├── ingest_reddit.py         # Scrape Reddit (no API key needed)
│   ├── ingest_hn.py             # Scrape Hacker News
│   ├── ingest_youtube.py        # Search YouTube via yt-dlp
│   ├── ingest_trends.py         # Google Trends RSS feeds
│   ├── cluster_topics.py        # BERTopic clustering (heavy)
│   ├── cluster_topics_lite.py   # TF-IDF clustering (lightweight)
│   ├── score_topics.py          # Embedding-based scoring (heavy)
│   ├── score_topics_lite.py     # TF-IDF scoring (lightweight)
│   ├── index_voice.py           # Index voice samples into ChromaDB
│   ├── retrieve_similar.py      # RAG: find similar past scripts
│   └── prep_voice_samples.py    # (Optional) Parse CSV into .txt files
│
├── voice/                       # Your voice identity
│   ├── samples/                 # YOUR past scripts (add 30-50 .txt files)
│   ├── STYLE_GUIDE.md           # Auto-generated by /build-voice-pack
│   ├── HOOK_PATTERNS.md         # Auto-generated by /build-voice-pack
│   └── CTA_PATTERNS.md          # Auto-generated by /build-voice-pack
│
├── voice_db/                    # ChromaDB vector store (auto-generated)
│
├── data/                        # Intermediate pipeline data (auto-generated)
│   ├── raw_reddit.json
│   ├── raw_hn.json
│   ├── raw_youtube.json
│   ├── raw_trends.json
│   ├── clustered_topics.json
│   ├── scored_topics.json
│   └── angles.json
│
└── outputs/                     # Generated scripts (auto-generated)
    ├── 2026-W15/                # Weekly output folders
    │   ├── scripts.md
    │   ├── scripts.json
    │   └── summary.md
    ├── custom/                  # On-demand script outputs
    │   └── 2026-04-08_topic.md
    └── latest/                  # Copy of most recent week
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'yt_dlp'"

Install the missing package:
```bash
pip install yt-dlp
```

### "ModuleNotFoundError: No module named 'trendspyg'"

```bash
pip install trendspyg
```

### numpy / scikit-learn architecture errors (Apple Silicon Mac)

If you see "incompatible architecture (have 'x86_64', need 'arm64')":
```bash
pip install --force-reinstall numpy scikit-learn
```

### BERTopic or sentence-transformers won't install

These are large packages that require PyTorch. The engine includes lightweight alternatives (`cluster_topics_lite.py`, `score_topics_lite.py`) that use scikit-learn instead. The pipeline automatically falls back to these. You can safely ignore BERTopic installation errors.

### Reddit returns 404 for some subreddits

Some subreddits go private or get banned. The pipeline skips failed subreddits and continues. You can update the subreddit list in `pipelines/ingest_reddit.py`.

### "python" runs Python 2

On some systems, `python` points to Python 2. Use `python3` instead. If the pipeline scripts fail, check that your AI agent is calling `python3`, not `python`.

### ChromaDB errors when building voice pack

Make sure you have at least 10 voice samples in `voice/samples/` before running `/build-voice-pack`. Empty or very few samples will cause indexing errors.

---

## FAQ

**Q: What niche does this work for?**
Any niche where you create short-form content about trending topics. The default configuration targets AI/tech, but you can adapt it to finance, fitness, business, education, or anything else by changing the relevance keywords and source subreddits/queries.

**Q: Do I need to pay for API keys?**
No API keys are needed for data collection -- Reddit, HN, YouTube, and Google Trends are all scraped using free public endpoints. You do need a subscription to your AI coding agent (Claude Pro/Max or OpenAI API credits).

**Q: How many voice samples do I need?**
30 is the minimum for decent voice matching. 50 is ideal. The engine works with as few as 10, but the voice matching will be less accurate.

**Q: Can I use this with Cursor, Windsurf, or other AI editors?**
The Python pipeline scripts work with anything. The skill/command system is specific to Claude Code and Codex CLI. If your editor supports custom commands or agent workflows, you can adapt the `SKILL.md` files.

**Q: How long does a full weekly run take?**
Typically 5-15 minutes depending on your internet speed and AI model response times. Data collection (1-3 min) + clustering (30 sec) + scoring + angle generation + script writing (3-10 min).

**Q: Can I edit the generated scripts?**
Absolutely. The scripts are starting points. Most creators use them as 80% drafts and add their own tweaks, current examples, or personal stories before filming.

---

## Credits

Built by [Niyi Omotoso](https://github.com/niyiomotoso) using Claude Code by Anthropic. The agent skills follow the open [Agent Skills](https://agentskills.io) standard.

---

## License

MIT License. Use it, modify it, make it yours.
