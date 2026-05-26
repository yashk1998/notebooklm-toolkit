#!/usr/bin/env python3
"""Ask a question to NotebookLM and print the answer."""

import argparse
import sys

from notebooklm.query import ask_notebooklm
from notebooklm.library import NotebookLibrary


def main():
    parser = argparse.ArgumentParser(description="Ask NotebookLM a question")
    parser.add_argument("--question", required=True, help="Question to ask")
    parser.add_argument("--notebook-url", help="NotebookLM notebook URL")
    parser.add_argument("--notebook-id", help="Notebook ID from local library")
    parser.add_argument("--show-browser", action="store_true", help="Show browser window")
    args = parser.parse_args()

    notebook_url = args.notebook_url

    if not notebook_url and args.notebook_id:
        lib = NotebookLibrary()
        nb = lib.get_notebook(args.notebook_id)
        if nb:
            notebook_url = nb["url"]
        else:
            print(f"Notebook '{args.notebook_id}' not found in library.")
            sys.exit(1)

    if not notebook_url:
        lib = NotebookLibrary()
        active = lib.get_active_notebook()
        if active:
            notebook_url = active["url"]
            print(f"Using active notebook: {active['name']}")
        else:
            notebooks = lib.list_notebooks()
            if notebooks:
                print("\nAvailable notebooks:")
                for nb in notebooks:
                    mark = " [ACTIVE]" if nb.get("id") == lib.active_notebook_id else ""
                    print(f"  {nb['id']}: {nb['name']}{mark}")
                print("\nSpecify with --notebook-id or --notebook-url")
            else:
                print("No notebooks in library. Add one with: python cli/add.py")
            sys.exit(1)

    answer = ask_notebooklm(
        question=args.question,
        notebook_url=notebook_url,
        headless=not args.show_browser,
    )

    if answer:
        print("\n" + "=" * 60)
        print(f"Question: {args.question}")
        print("=" * 60)
        print()
        print(answer)
        print()
        print("=" * 60)
    else:
        print("\nFailed to get answer.")
        sys.exit(1)


if __name__ == "__main__":
    main()
