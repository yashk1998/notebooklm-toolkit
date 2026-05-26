#!/usr/bin/env python3
"""
Weekly AI paper video workflow.

Each week: ask the notebook for this week's papers and findings,
then download all Audio/Video Overviews to a local folder.

Usage:
    python examples/weekly_workflow.py \
        --notebook-url "https://notebooklm.google.com/notebook/your-id" \
        --output-dir "./weekly_videos"
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

from notebooklm.query import ask_notebooklm
from notebooklm.download import download_all_media


WEEKLY_QUESTION = (
    "List all papers added this week with their key findings. "
    "For each paper, include: title, authors (if available), one-sentence summary, "
    "and the 2-3 most important takeaways."
)


def main():
    parser = argparse.ArgumentParser(description="Weekly AI paper video workflow")
    parser.add_argument("--notebook-url", required=True, help="NotebookLM notebook URL")
    parser.add_argument("--output-dir", default="./weekly_videos", help="Directory to save downloads")
    parser.add_argument("--show-browser", action="store_true", help="Show browser window")
    args = parser.parse_args()

    week_label = datetime.now().strftime("%Y-W%W")
    output_path = Path(args.output_dir) / week_label
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\nWeekly NotebookLM Workflow")
    print(f"  Week      : {week_label}")
    print(f"  Notebook  : {args.notebook_url}")
    print(f"  Output    : {output_path}\n")
    print("=" * 60)

    # Step 1: Ask for this week's papers
    print("\nStep 1: Querying notebook for this week's papers...\n")
    answer = ask_notebooklm(
        question=WEEKLY_QUESTION,
        notebook_url=args.notebook_url,
        headless=not args.show_browser,
    )

    if answer:
        print("\nNotebookLM Summary:")
        print("-" * 60)
        # Strip the FOLLOW_UP_REMINDER appended by ask_notebooklm
        clean_answer = answer.split("\n\nEXTREMELY IMPORTANT")[0]
        print(clean_answer)
        print("-" * 60)

        # Save summary to file
        summary_file = output_path / "summary.txt"
        summary_file.write_text(
            f"Week: {week_label}\nNotebook: {args.notebook_url}\n\n{clean_answer}\n"
        )
        print(f"\nSummary saved to: {summary_file}")
    else:
        print("Could not retrieve notebook summary. Continuing to download...")

    # Step 2: Download Audio/Video Overviews
    print(f"\nStep 2: Downloading Audio/Video Overviews to {output_path}...\n")
    files = download_all_media(
        notebook_url=args.notebook_url,
        output_dir=str(output_path),
        headless=not args.show_browser,
    )

    # Report
    print("\n" + "=" * 60)
    print(f"Workflow complete for {week_label}")
    print(f"  Summary     : {'saved' if answer else 'failed'}")
    print(f"  Media files : {len(files)} downloaded")
    if files:
        for f in files:
            size_mb = Path(f).stat().st_size / (1024 * 1024)
            print(f"    - {Path(f).name} ({size_mb:.1f} MB)")
    print(f"  Output dir  : {output_path}")
    print("=" * 60)

    return 0 if files or answer else 1


if __name__ == "__main__":
    sys.exit(main())
