import time
import json
import sys
from typing import List, Dict

from patchright.sync_api import sync_playwright

from notebooklm.browser import BrowserFactory


def list_notebooks_from_web(headless: bool = True) -> List[Dict]:
    """
    Scrape the NotebookLM homepage and return all notebooks as a list of dicts.

    Each dict contains: title, url, id
    """
    with sync_playwright() as p:
        context = BrowserFactory.launch_persistent_context(p, headless=headless)
        page = context.new_page()

        try:
            page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            if "accounts.google.com" in page.url or "signin" in page.url.lower():
                print("Not authenticated. Run: python cli/auth.py reauth")
                return []

            try:
                page.wait_for_selector("a[href*='/notebook/']", timeout=15000)
            except Exception:
                print("No notebooks found or page structure changed.")
                return []

            notebooks = page.evaluate("""
                () => {
                    const results = [];
                    const seen = new Set();
                    document.querySelectorAll("a[href*='/notebook/']").forEach(el => {
                        const href = el.href;
                        const notebookId = href.match(/\\/notebook\\/([^?#]+)/)?.[1];
                        if (!notebookId || seen.has(notebookId)) return;
                        seen.add(notebookId);

                        const card = el.closest('[class*="notebook"], [class*="card"], [class*="item"], mat-card, .project') || el;
                        const titleEl = card.querySelector('h1, h2, h3, h4, [class*="title"], [class*="name"]');
                        const title = titleEl?.textContent?.trim() || el.textContent?.trim() || "Untitled";

                        results.push({ title, url: href, id: notebookId });
                    });
                    return results;
                }
            """)

            return notebooks
        finally:
            context.close()
