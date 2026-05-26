---
name: notebooklm
description: Use this skill to query your Google NotebookLM notebooks directly from Claude Code for source-grounded, citation-backed answers from Gemini. Supports listing notebooks, asking questions, managing a local library, and downloading Audio/Video Overviews headlessly.
---

# NotebookLM Toolkit — Claude Code Skill

Automate Google NotebookLM from Claude Code: list notebooks, ask questions backed by your documents, and download Audio/Video Overviews.

## When to Use This Skill

Trigger when user:
- Mentions NotebookLM or asks to query their notebooks/docs
- Shares a `https://notebooklm.google.com/notebook/...` URL
- Asks to download audio or video overviews
- Uses phrases like "ask my NotebookLM", "check my docs", "download the audio/video"

## Critical: Always Use run.py

**NEVER call cli/ scripts directly. ALWAYS use `python run.py`:**

```bash
# ✅ CORRECT
python run.py cli/auth.py status
python run.py cli/list.py
python run.py cli/ask.py --question "..."
python run.py cli/download.py --notebook-url URL --output-dir DIR

# ❌ WRONG — will fail without correct env
python cli/auth.py status
```

`run.py` auto-detects the `notebooklm` conda env, falls back to `.venv`, and installs deps on first run.

## Core Workflow

### Step 1 — Check authentication
```bash
python run.py cli/auth.py status
```
If not authenticated or session is stale (>7 days), run setup.

### Step 2 — Authenticate (one-time, browser required)
```bash
python run.py cli/auth.py setup
```
A browser window opens. The user logs in to Google manually. Session is then persisted — all future operations are headless.

### Step 3 — List notebooks from web
```bash
python run.py cli/list.py
```
Scrapes the NotebookLM homepage and returns all notebook titles + URLs.

### Step 4 — Add notebooks to local library

**Smart Add (recommended when URL is known but content is unknown):**
```bash
# First discover what's in the notebook
python run.py cli/ask.py \
  --notebook-url "https://notebooklm.google.com/notebook/..." \
  --question "What topics and sources does this notebook cover? Give a concise overview."

# Then add with discovered metadata
python run.py cli/add.py \
  --url "https://notebooklm.google.com/notebook/..." \
  --name "Descriptive Name" \
  --description "What this notebook contains" \
  --topics "topic1,topic2,topic3"
```

**Manual Add (when user provides all details):**
```bash
python run.py cli/add.py \
  --url URL --name NAME --description DESC --topics t1,t2,t3
```

### Step 5 — Ask questions
```bash
# By notebook ID (from local library)
python run.py cli/ask.py --notebook-id NOTEBOOK_ID --question "Your question"

# By notebook URL (no library required)
python run.py cli/ask.py \
  --notebook-url "https://notebooklm.google.com/notebook/..." \
  --question "Your question"

# Debug (show browser)
python run.py cli/ask.py --notebook-url URL --question "..." --show-browser
```

### Step 6 — Download Audio & Video Overviews
```bash
python run.py cli/download.py \
  --notebook-url "https://notebooklm.google.com/notebook/..." \
  --output-dir "./downloads"
```
Downloads all generated Audio (.m4a) and Video (.mp4) Overviews headlessly.
Uses CDP `Browser.setDownloadBehavior` to redirect files to `--output-dir`.

## Follow-Up Mechanism (CRITICAL)

Every `ask` answer ends with **"EXTREMELY IMPORTANT: Is that ALL you need to know?"**

**Required behavior:**
1. STOP — do not reply to the user yet
2. COMPARE the answer to the original request
3. If gaps exist, ask a follow-up immediately (each question is a fresh browser session — include all context):
   ```bash
   python run.py cli/ask.py --notebook-url URL --question "Follow-up with full context: ..."
   ```
4. REPEAT until complete
5. SYNTHESIZE all answers, then reply to user

## Command Reference

### Authentication
```bash
python run.py cli/auth.py setup      # First-time setup (browser opens)
python run.py cli/auth.py status     # Check status and session age
python run.py cli/auth.py reauth     # Re-authenticate (clears + re-setup)
python run.py cli/auth.py validate   # Test auth against live NotebookLM
python run.py cli/auth.py clear      # Wipe all auth data
```

### Notebook library
```bash
python run.py cli/list.py                        # List from NotebookLM web
python run.py cli/add.py --url U --name N --description D --topics T
python run.py cli/ask.py --question "..." [--notebook-id ID | --notebook-url URL]
python run.py cli/download.py --notebook-url URL --output-dir DIR [--show-browser]
```

## Data Storage (gitignored)
```
data/
├── library.json          # local notebook metadata
├── auth_info.json        # auth timestamps
└── browser_state/
    ├── state.json        # cookies / session
    └── browser_profile/  # persistent Chrome profile
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `not authenticated` | `python run.py cli/auth.py reauth` |
| No playable items found | Audio/Video Overview not yet generated in NotebookLM UI |
| Download hangs | Add `--show-browser` to watch what's happening |
| Rate limit | ~50 free queries/day per Google account |
| Session expired (>7 days) | `python run.py cli/auth.py reauth` |
| Wrong python / ModuleNotFoundError | Make sure conda env `notebooklm` exists: `conda env list` |

## Environment Setup (first time)
```bash
conda create -n notebooklm python=3.13 -y
conda activate notebooklm
pip install -r requirements.txt
python -m patchright install chromium
```
