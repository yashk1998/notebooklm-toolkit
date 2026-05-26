#!/usr/bin/env python3
"""Add a notebook to the local library."""

import argparse
import json
import sys

from notebooklm.library import NotebookLibrary


def main():
    parser = argparse.ArgumentParser(description="Add a notebook to the local library")
    parser.add_argument("--url", required=True, help="NotebookLM notebook URL")
    parser.add_argument("--name", required=True, help="Display name")
    parser.add_argument("--description", required=True, help="What is in this notebook")
    parser.add_argument("--topics", required=True, help="Comma-separated topics")
    parser.add_argument("--use-cases", help="Comma-separated use cases")
    parser.add_argument("--tags", help="Comma-separated tags")
    args = parser.parse_args()

    lib = NotebookLibrary()

    topics = [t.strip() for t in args.topics.split(",")]
    use_cases = [u.strip() for u in args.use_cases.split(",")] if args.use_cases else None
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None

    try:
        notebook = lib.add_notebook(
            url=args.url,
            name=args.name,
            description=args.description,
            topics=topics,
            use_cases=use_cases,
            tags=tags,
        )
        print(json.dumps(notebook, indent=2))
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
