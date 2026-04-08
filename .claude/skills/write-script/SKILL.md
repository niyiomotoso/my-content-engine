---
name: write-script
description: Turn a raw idea, topic, or paragraph into 2-3 ready-to-shoot script variations in the creator's voice. Use when you have a specific topic you want to create content about.
argument-hint: "<your idea, topic, or paragraph>"
allowed-tools: Bash(python *), Read, Write, WebSearch
---

Turn a raw idea into polished script variations in the creator's voice.

## Voice Context (loaded automatically)
- Style guide: !`cat voice/STYLE_GUIDE.md 2>/dev/null || echo "Voice pack not built yet. Run /build-voice-pack first."`
- Hook patterns: !`cat voice/HOOK_PATTERNS.md 2>/dev/null || echo "No hook patterns yet."`
- CTA patterns: !`cat voice/CTA_PATTERNS.md 2>/dev/null || echo "No CTA patterns yet."`

## Instructions

### Step 1: Digest the input
Parse whatever the user gave — a full rant, a one-liner, bullet points, a theme. Extract:
- **Core topic/theme** (e.g., "ChatGPT Atlas hype vs reality")
- **User's stance/angle** — if they expressed an opinion, identify it (frustration, excitement, skepticism, etc.)
- **Phrases to preserve verbatim** — any raw phrasing with energy, personality, or strong opinion. These MUST appear in the final scripts. Do NOT sanitize, soften, or rephrase them.
- **Content type** — auto-detect: HOW_TO (tutorials, steps, tips), OPINION (takes, rants, debates), ROUNDUP (lists, comparisons), or NEWS (announcements, updates)

### Step 2: Research
Run 2-3 web searches to gather:
- Current facts, stats, and status of the topic
- What people are saying about it right now
- Any recent developments the script should reference
- Traceable source URLs to include in the output

### Step 3: Retrieve voice context
Run: `cd pipelines && python retrieve_similar.py "CORE TOPIC" -n 3`
Read the output to see how the creator has written about similar subjects before.

### Step 4: Generate 2-3 script variations
All variations use the **same angle** (the user's stance) but with **different structures**:

**Variation 1: Rant/Story structure**
Hook → Personal take → Build the argument with facts → Reality check → CTA

**Variation 2: List/Steps structure**
Hook → Numbered points (3-5) → Standout insight → CTA

**Variation 3: Question/Answer structure**
Hook (posed as a question) → Explore the answer → What most people miss → CTA

For each variation, generate:
- **3 hook options** (each using a DIFFERENT pattern from the hook patterns file — rotate through Bold Claim, Imagine, What If, Did You Know, If There Is, Direct Challenge, Personal Story, List Intro, Problem/Pain Point, If You Qualifier)
- **Full script** (~150-200 words)
- **Caption** (social media caption with hashtags)
- **3 comment prompts** (engagement questions)
- **Sources** (traceable URLs from web search, 2-4 per variation)

### Key Rules

1. **Preserve the user's exact phrasing.** If they said something with energy, personality, or strong emotion — keep it word for word. Build the polished script AROUND their raw voice, don't replace it.

2. **Voice matching checklist** (apply to EVERY variation):
   - Does it sound conversational, not formal?
   - Does it use "you" and "your" directly?
   - Does it include a practical takeaway?
   - Does it use analogies to explain complex ideas?
   - Would the creator actually say this out loud?
   - Is it 150-200 words?

3. **Structure rules by content type:**
   - HOW_TO: Hook → Problem → Steps (3-5) → Result → CTA
   - OPINION: Hook → Take → Evidence → Reality check → CTA
   - ROUNDUP: Hook → Numbered list → Standout pick → CTA
   - NEWS: Hook → What happened → Why it matters → What's next → CTA

### Step 5: Save outputs
Create output directory if needed: `mkdir -p outputs/custom`

Save two files:
- `outputs/custom/YYYY-MM-DD_[slug].json` — Full script data (see schema below)
- `outputs/custom/YYYY-MM-DD_[slug].md` — Human-readable markdown

The slug should be a short kebab-case version of the topic (e.g., `chatgpt-atlas`, `vibe-coding-beginners`).

### Step 6: Present results
Show all variations side by side. Note which phrases were preserved from the user's original input.

## Output JSON Schema
```json
{
  "generated_at": "ISO8601 timestamp",
  "input": "the raw user input (full text)",
  "topic": "extracted core topic",
  "content_type": "OPINION|HOW_TO|ROUNDUP|NEWS",
  "angle": "the detected angle/stance",
  "preserved_phrases": ["phrase 1 kept verbatim", "phrase 2 kept verbatim"],
  "research_summary": "key facts found during web search",
  "variations": [
    {
      "id": 1,
      "structure": "rant|list|question",
      "hooks": ["hook 1", "hook 2", "hook 3"],
      "script": "full 150-200 word script",
      "caption": "social media caption with hashtags",
      "comment_prompts": ["question 1", "question 2", "question 3"],
      "sources": ["https://...", "https://..."]
    }
  ]
}
```

## Output Markdown Format
```
# Custom Script: [Topic]

> Generated from: "[first 100 chars of input]..."
> Type: [OPINION] | Angle: [CONTRARIAN/FRUSTRATION/etc.]
> Preserved phrases: "[phrase 1]", "[phrase 2]"

## Research Summary
[Key facts, stats, and current status found during web search]

---

## Variation 1: Rant/Story
### Hooks
1. ...
2. ...
3. ...

### Script
[Full script]

### Caption
[Caption with hashtags]

### Comment Prompts
- ...

### Sources
- https://...

---

## Variation 2: List/Steps
[Same format]

---

## Variation 3: Question/Answer
[Same format]
```
