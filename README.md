# notebooklm-toolkit

A Python toolkit for automating [Google NotebookLM](https://notebooklm.google.com) via browser automation ([patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright)). Authenticate once, then list notebooks, query them with questions, and download Audio/Video Overviews — all headlessly.

## Features

- **Authenticate once** — Google login in a visible browser; all future operations are headless
- **List notebooks** — scrape your NotebookLM homepage to get all notebooks with titles and URLs
- **Local library** — maintain a JSON-based notebook catalogue with metadata (topics, tags, use-cases)
- **Ask questions** — send a question to any notebook and get Gemini's answer from your documents
- **Download media** — download Audio Overviews (.m4a) and Video Overviews (.mp4) headlessly via CDP
- **Claude Code skill** — designed to integrate with the `/notebooklm` Claude Code skill

---

## Prerequisites

- **Python 3.11+** (3.13 recommended — use conda or pyenv)
- **Google Chrome** installed (patchright drives real Chrome for anti-detection)
- **A Google account** with NotebookLM access ([notebooklm.google.com](https://notebooklm.google.com))
- **`gh` CLI** for GitHub operations (optional)

---

## Setup

### Option A: conda (recommended)

```bash
conda create -n notebooklm python=3.13 -y
conda activate notebooklm
pip install -r requirements.txt
python -m patchright install chromium
```

### Option B: venv

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m patchright install chromium
```

### Environment variables (optional)

Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data` | Where auth state and library.json are stored |
| `HEADLESS` | `true` | Run browser headlessly after initial auth |
| `SHOW_BROWSER` | `false` | Alias for headless=false |

---

## Authentication

First-time setup requires a **visible browser** so you can complete Google's login flow. After that, the session (cookies + Chrome profile) is persisted to `data/browser_state/` and all operations run headlessly.

```bash
# First-time setup — opens Chrome, complete Google login
python cli/auth.py setup

# Check status
python cli/auth.py status

# Verify the saved session actually works
python cli/auth.py validate

# Re-authenticate when session expires (~7 days)
python cli/auth.py reauth

# Clear all auth data
python cli/auth.py clear
```

> **Why visible browser?** Google's login flow detects automation. Patchright patches many signals, but the initial login still needs to be completed by a human. After the first login, the persistent Chrome profile + injected cookies keep you authenticated for days.

---

## Connecting to Claude Code (the /notebooklm skill)

This repo is designed to work as a Claude Code skill. Claude Code's built-in `/notebooklm` command uses the same browser automation under the hood.

**Install as a skill:**

```bash
# Clone to the Claude Code skills directory
git clone https://github.com/yashk1998/notebooklm-toolkit ~/.claude/skills/notebooklm-toolkit

# Or symlink an existing clone
ln -s /path/to/notebooklm-toolkit ~/.claude/skills/notebooklm
```

The conda env `notebooklm` is the recommended environment — Claude Code's skill runner auto-detects it. Once installed, type `/notebooklm` in Claude Code to query your notebooks directly from the chat interface.

---

## Usage

### List all your notebooks

Scrapes the NotebookLM homepage and prints all notebooks with their URLs.

```bash
python cli/list.py

# Show browser window (useful for debugging)
python cli/list.py --show-browser

# JSON output for scripting
python cli/list.py --json
```

### Add a notebook to the local library

Saves notebook metadata locally so you can reference it by ID instead of URL.

```bash
python cli/add.py \
  --url "https://notebooklm.google.com/notebook/your-id" \
  --name "My Research Notebook" \
  --description "Papers on AI agents" \
  --topics "ai,agents,research" \
  --tags "weekly,papers"
```

### Ask a question

Navigates to the notebook and submits your question, then returns the Gemini-generated answer.

```bash
# Ask the active notebook (first added = active by default)
python cli/ask.py --question "What are the key findings about tool-use in LLMs?"

# Target a specific notebook by URL
python cli/ask.py \
  --notebook-url "https://notebooklm.google.com/notebook/your-id" \
  --question "Summarize the main papers"

# Target by library ID
python cli/ask.py --notebook-id my-research-notebook --question "..."

# Debug with visible browser
python cli/ask.py --notebook-url "..." --question "..." --show-browser
```

### Download Audio & Video Overviews

Downloads all generated Audio (.m4a) and Video (.mp4) Overviews headlessly.

```bash
python cli/download.py \
  --notebook-url "https://notebooklm.google.com/notebook/your-id" \
  --output-dir "./downloads"

# Debug with visible browser
python cli/download.py \
  --notebook-url "..." \
  --output-dir "./downloads" \
  --show-browser
```

Typical file sizes: Audio ~35-40 MB, Video ~48 MB.

---

## Weekly AI Paper Video Workflow

A common use case: you maintain a NotebookLM notebook tracking weekly AI papers. Each week, you add new papers, NotebookLM auto-generates Audio/Video Overviews, and you run this script to:

1. Ask the notebook for this week's papers and their key findings
2. Download all Audio/Video Overviews to a dated folder

```bash
python examples/weekly_workflow.py \
  --notebook-url "https://notebooklm.google.com/notebook/your-id" \
  --output-dir "./weekly_videos"
```

Output is organized by ISO week: `./weekly_videos/2025-W22/`

Each run saves:
- `summary.txt` — Gemini's answer listing papers and findings
- `*.m4a` and `*.mp4` — the downloaded overviews

---

## How it works

### Browser automation
Uses [patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright) — an anti-detection fork of Playwright that patches `navigator.webdriver` and other automation signals that Google checks.

### Session persistence
A hybrid approach is used to keep the session alive across runs:

1. **Persistent Chrome profile** (`data/browser_state/browser_profile/`) — preserves fingerprint consistency and localStorage
2. **Manual cookie injection** — session cookies (with `expires=-1`) don't survive in the profile due to [Playwright bug #36139](https://github.com/microsoft/playwright/issues/36139). These are saved separately to `data/browser_state/state.json` and injected at browser launch.

### Download mechanism
Downloads work by:
1. Expanding the Studio panel (Audio Overview + Video Overview sections)
2. Finding each "Play" button and its adjacent "More" button
3. Clicking More → Download
4. Using a CDP `Browser.setDownloadBehavior` command to redirect the download to the output directory without any save dialog

---

## Data storage

All local data lives in `./data/` (gitignored by default):

| Path | Contents |
|------|----------|
| `data/library.json` | Notebook metadata (name, URL, topics, use counts) |
| `data/auth_info.json` | Auth timestamps |
| `data/browser_state/state.json` | Cookies/session (injected workaround for Playwright bug) |
| `data/browser_state/browser_profile/` | Persistent Chrome profile |

Set `DATA_DIR` in `.env` to store data elsewhere.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Not authenticated` | Run `python cli/auth.py reauth` |
| No playable items found | Audio/Video Overview not generated yet — go to NotebookLM and wait for generation |
| Download stuck | Add `--show-browser` to see what's happening |
| Login loop after reauth | Delete `data/` entirely and run `python cli/auth.py setup` |
| Rate limit / no answer | NotebookLM free tier: ~50 queries/day; wait and try again |
| Session expired | Run `python cli/auth.py reauth` |
| `channel="chrome"` error | Google Chrome must be installed; patchright uses real Chrome, not Chromium |
| Selector not found | NotebookLM UI may have changed; open an issue with `--show-browser` screenshot |

---

## Project structure

```
notebooklm-toolkit/
├── notebooklm/          # Main package
│   ├── __init__.py      # Public API exports
│   ├── config.py        # Paths, selectors, browser args
│   ├── auth.py          # AuthManager — Google login + session persistence
│   ├── browser.py       # BrowserFactory, StealthUtils
│   ├── library.py       # NotebookLibrary — local CRUD
│   ├── query.py         # ask_notebooklm()
│   ├── discovery.py     # list_notebooks_from_web()
│   └── download.py      # download_all_media()
├── cli/                 # Thin CLI wrappers
│   ├── auth.py
│   ├── ask.py
│   ├── list.py
│   ├── add.py
│   └── download.py
├── examples/
│   └── weekly_workflow.py
├── requirements.txt
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## License

MIT
