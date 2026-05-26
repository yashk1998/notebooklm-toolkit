#!/usr/bin/env python3
"""List all NotebookLM notebooks from the web."""

import argparse
import json
import sys

from notebooklm.discovery import list_notebooks_from_web


def main():
    parser = argparse.ArgumentParser(description="List notebooks from NotebookLM")
    parser.add_argument("--show-browser", action="store_true", help="Show browser window")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON")
    args = parser.parse_args()

    notebooks = list_notebooks_from_web(headless=not args.show_browser)

    if not notebooks:
        print("No notebooks found.")
        sys.exit(1)

    if args.as_json:
        print(json.dumps(notebooks, indent=2))
        return

    print(f"\nYour NotebookLM Notebooks ({len(notebooks)} found):\n")
    for i, nb in enumerate(notebooks, 1):
        print(f"  {i}. {nb['title']}")
        print(f"     URL: {nb['url']}\n")


if __name__ == "__main__":
    main()
