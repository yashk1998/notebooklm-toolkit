import sys
import time
import shutil
from pathlib import Path
from typing import List

from patchright.sync_api import sync_playwright

from notebooklm.browser import BrowserFactory


def close_overlays(page):
    """Dismiss any open Material Design overlays."""
    page.evaluate("""
        () => {
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.click());
        }
    """)
    time.sleep(0.5)


def get_play_items(page):
    """Return list of dicts with {name, idx, moreIdx} for each playable item."""
    return page.evaluate("""
        () => {
            const results = [];
            const btns = Array.from(document.querySelectorAll('button,[role="button"]'));

            for (let i = 0; i < btns.length; i++) {
                const aria = btns[i].getAttribute('aria-label') || '';
                if (aria !== 'Play') continue;
                if (!btns[i].offsetParent) continue;

                let name = '';
                let el = btns[i].parentElement;
                for (let depth = 0; depth < 8 && el; depth++) {
                    const title = el.querySelector('[class*="title"],[class*="name"],h1,h2,h3,h4');
                    if (title) { name = title.textContent.trim().slice(0, 60); break; }
                    for (const child of el.children) {
                        const t = child.textContent.trim();
                        if (t && t.length > 3 && !/^[a-z_]+$/.test(t) && !['Play','More','Download','Share'].includes(t)) {
                            name = t.slice(0, 60);
                            break;
                        }
                    }
                    if (name) break;
                    el = el.parentElement;
                }

                let moreIdx = -1;
                for (let j = i + 1; j < Math.min(i + 4, btns.length); j++) {
                    const a = btns[j].getAttribute('aria-label') || '';
                    if (a === 'More') { moreIdx = j; break; }
                }

                results.push({ idx: i, moreIdx, name: name || `item_${results.length + 1}` });
            }
            return results;
        }
    """)


def download_all_media(notebook_url: str, output_dir: str, headless: bool = True) -> List[str]:
    """
    Download all Audio and Video Overviews from a NotebookLM notebook.

    Clicks More -> Download for each playable item found in the Studio panel.
    Uses CDP to redirect downloads to output_dir.

    Args:
        notebook_url: Full NotebookLM notebook URL
        output_dir: Directory to save downloaded files
        headless: Run browser in headless mode

    Returns:
        List of paths to saved files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    saved_files = []

    with sync_playwright() as p:
        ctx = BrowserFactory.launch_persistent_context(p, headless=headless)
        page = ctx.new_page()
        page.set_viewport_size({"width": 1600, "height": 900})

        # CDP redirect: downloads go to output_path without browser save dialog
        cdp = ctx.new_cdp_session(page)
        cdp.send("Browser.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": str(output_path),
        })

        try:
            print(f"  Opening notebook...")
            page.goto(notebook_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)

            if "accounts.google.com" in page.url:
                print("Not authenticated.")
                return []

            print("  Expanding Studio sections...")
            for aria_label in ["Audio Overview", "Video Overview"]:
                for btn in page.query_selector_all("button,[role='button']"):
                    if btn.get_attribute("aria-label") == aria_label and btn.is_visible():
                        btn.click()
                        time.sleep(2)
                        break

            time.sleep(2)
            items = get_play_items(page)
            print(f"  Found {len(items)} playable item(s)\n")

            if not items:
                print("  No playable items found.")
                page.screenshot(path="/tmp/notebooklm_debug.png")
                return []

            for item in items:
                name = item["name"]
                more_idx = item["moreIdx"]
                print(f"  Downloading: '{name}'")

                if more_idx == -1:
                    print(f"     No More button found, skipping")
                    continue

                close_overlays(page)
                time.sleep(0.5)

                all_btns = page.query_selector_all("button,[role='button']")
                visible_btns = [b for b in all_btns if b.is_visible()]

                play_count = 0
                target_more = None
                for b in visible_btns:
                    aria = b.get_attribute("aria-label") or ""
                    if aria == "Play":
                        if play_count == items.index(item):
                            btn_idx = visible_btns.index(b)
                            for j in range(btn_idx + 1, min(btn_idx + 5, len(visible_btns))):
                                if (visible_btns[j].get_attribute("aria-label") or "") == "More":
                                    target_more = visible_btns[j]
                                    break
                            break
                        play_count += 1

                if not target_more:
                    print(f"     Could not find More button, skipping")
                    continue

                try:
                    target_more.click(timeout=5000)
                except Exception as e:
                    print(f"     More button click failed: {e}")
                    close_overlays(page)
                    continue

                time.sleep(1.5)

                downloaded = False
                for menu_item in page.query_selector_all('[role="menuitem"],[role="option"],.mat-menu-item'):
                    text = (menu_item.text_content() or "").strip().lower()
                    if "download" in text and menu_item.is_visible():
                        print(f"     Clicking Download...")
                        menu_item.click()
                        downloaded = True
                        time.sleep(1)
                        break

                if not downloaded:
                    print(f"     Download option not found in menu")
                    close_overlays(page)
                    continue

                print(f"     Waiting for download (up to 30s)...")
                deadline = time.time() + 30
                found_file = None
                while time.time() < deadline:
                    time.sleep(1)
                    candidates = sorted(output_path.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
                    complete = [f for f in candidates if not f.name.endswith(".crdownload") and f.is_file()]
                    if complete and (time.time() - complete[0].stat().st_mtime) < 60:
                        found_file = complete[0]
                        time.sleep(1.5)
                        break

                if found_file:
                    safe_name = "".join(c if c.isalnum() or c in " _-." else "_" for c in name)
                    ext = found_file.suffix or ".mp4"
                    dest = output_path / f"{safe_name}{ext}"
                    if found_file != dest and not dest.exists():
                        shutil.move(str(found_file), str(dest))
                    elif found_file != dest:
                        dest = found_file
                    size_mb = dest.stat().st_size / (1024 * 1024)
                    print(f"     Saved: {dest.name} ({size_mb:.1f} MB)")
                    saved_files.append(str(dest))
                else:
                    print(f"     No downloaded file detected in {output_path}")

                time.sleep(1)

        finally:
            ctx.close()

    return saved_files
