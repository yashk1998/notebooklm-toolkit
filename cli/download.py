#!/usr/bin/env python3
"""Download all Audio/Video Overviews from a NotebookLM notebook."""

import argparse
import sys

from notebooklm.download import download_all_media


def main():
    parser = argparse.ArgumentParser(description="Download Audio/Video Overviews from NotebookLM")
    parser.add_argument("--notebook-url", required=True, help="NotebookLM notebook URL")
    parser.add_argument("--output-dir", required=True, help="Directory to save files")
    parser.add_argument("--show-browser", action="store_true", help="Show browser window")
    args = parser.parse_args()

    print(f"\nNotebookLM Media Downloader")
    print(f"  Notebook : {args.notebook_url}")
    print(f"  Save to  : {args.output_dir}\n")

    files = download_all_media(
        notebook_url=args.notebook_url,
        output_dir=args.output_dir,
        headless=not args.show_browser,
    )

    if files:
        print(f"\nDownloaded {len(files)} file(s):")
        for f in files:
            print(f"  {f}")
    else:
        print("\nNo files downloaded. Try --show-browser to debug.")
        sys.exit(1)


if __name__ == "__main__":
    main()
