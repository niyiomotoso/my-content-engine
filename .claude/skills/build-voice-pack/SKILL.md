---
name: build-voice-pack
description: Re-index voice samples and regenerate the style guide. Run this after adding new scripts to voice/samples/.
allowed-tools: Bash(python *), Read, Write, Glob
---

Build the voice pack from past scripts.

## Step 1: Index scripts into ChromaDB
Run `python pipelines/index_voice.py` to embed and store all scripts from `voice/samples/`.

## Step 2: Analyze writing style
Read all script files in `voice/samples/` and analyze them to extract:

1. **Opening/hook patterns**: How do scripts typically start? What makes the hooks work?
2. **Sentence rhythm**: Short punchy sentences? Long flowing ones? Mix?
3. **Vocabulary**: Casual or formal? Jargon usage? Slang?
4. **Tone**: Authoritative? Conversational? Humorous? Provocative?
5. **Structural patterns**: How are arguments built? What comes after the hook?
6. **Signature phrases**: Words or phrases that appear repeatedly
7. **Transition patterns**: How does the creator move between sections?
8. **CTA patterns**: How do scripts end? What actions are requested?
9. **Analogies and examples**: What kinds of comparisons are used?
10. **Emotional register**: Excited? Measured? Provocative? Empathetic?

## Step 3: Generate style files
Write the analysis to:
- `voice/STYLE_GUIDE.md` -- Complete tone and style rules
- `voice/HOOK_PATTERNS.md` -- Hook formulas with examples from the scripts
- `voice/CTA_PATTERNS.md` -- CTA formulas with examples from the scripts

## Step 4: Verify
Report how many scripts were indexed and summarize the key style characteristics found.
