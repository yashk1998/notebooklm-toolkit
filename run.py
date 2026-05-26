#!/usr/bin/env python3
"""
Universal runner — ensures CLI scripts execute in the correct Python environment.

Lookup order:
  1. conda env named 'notebooklm'  (preferred)
  2. .venv in this directory        (fallback)
  3. system python                  (last resort)

Usage:
  python run.py cli/auth.py status
  python run.py cli/ask.py --question "..."
  python run.py cli/list.py
  python run.py cli/download.py --notebook-url URL --output-dir DIR
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
CONDA_ENV_NAME = "notebooklm"

# Support non-standard conda install paths
_CONDA_ROOTS = [
    "/opt/anaconda3",
    "/opt/miniconda3",
    os.path.expanduser("~/anaconda3"),
    os.path.expanduser("~/miniconda3"),
    os.path.expanduser("~/mambaforge"),
]


def _find_python() -> Path:
    # 1. conda
    for root in _CONDA_ROOTS:
        candidate = Path(root) / "envs" / CONDA_ENV_NAME / "bin" / "python"
        if candidate.exists():
            return candidate

    # 2. .venv
    venv_py = PROJECT_DIR / ".venv" / ("Scripts" if os.name == "nt" else "bin") / "python"
    if venv_py.exists():
        return venv_py

    # 3. system python (current interpreter)
    return Path(sys.executable)


def _ensure_deps(python: Path):
    try:
        subprocess.run([str(python), "-c", "import patchright"], check=True,
                       capture_output=True)
    except subprocess.CalledProcessError:
        print("📦 Installing dependencies...")
        subprocess.run([str(python), "-m", "pip", "install", "-r",
                        str(PROJECT_DIR / "requirements.txt")], check=True)
        subprocess.run([str(python), "-m", "patchright", "install", "chromium"], check=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Available CLI scripts:")
        for f in sorted((PROJECT_DIR / "cli").glob("*.py")):
            print(f"  python run.py cli/{f.name}")
        sys.exit(0)

    script_arg = sys.argv[1]
    script_args = sys.argv[2:]

    # Accept both  "cli/auth.py"  and  "auth.py"  and  "auth"
    if not script_arg.startswith("cli/"):
        name = script_arg if script_arg.endswith(".py") else script_arg + ".py"
        script_path = PROJECT_DIR / "cli" / name
    else:
        script_path = PROJECT_DIR / script_arg

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        print("   Run  python run.py  for a list of available scripts.")
        sys.exit(1)

    python = _find_python()
    _ensure_deps(python)

    try:
        result = subprocess.run([str(python), str(script_path)] + script_args)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)


if __name__ == "__main__":
    main()
