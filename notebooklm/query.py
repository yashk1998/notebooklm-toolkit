import re
import time
from typing import Optional

from patchright.sync_api import sync_playwright

from notebooklm.auth import AuthManager
from notebooklm.browser import BrowserFactory, StealthUtils
from notebooklm.config import QUERY_INPUT_SELECTORS, RESPONSE_SELECTORS

# Appended to answers so Claude knows it can ask follow-up questions
# (each call opens a fresh browser session, so context is not preserved)
FOLLOW_UP_REMINDER = (
    "\n\nEXTREMELY IMPORTANT: Is that ALL you need to know? "
    "You can always ask another question! Think about it carefully: "
    "before you reply to the user, review their original request and this answer. "
    "If anything is still unclear or missing, ask me another comprehensive question "
    "that includes all necessary context (since each question opens a new browser session)."
)


def ask_notebooklm(question: str, notebook_url: str, headless: bool = True) -> Optional[str]:
    """
    Ask a question to NotebookLM and return Gemini's answer.

    Args:
        question: Question to ask
        notebook_url: NotebookLM notebook URL
        headless: Run browser in headless mode

    Returns:
        Answer text, or None on failure
    """
    auth = AuthManager()
    if not auth.is_authenticated():
        print("Not authenticated. Run: python cli/auth.py setup")
        return None

    print(f"Asking: {question}")
    print(f"Notebook: {notebook_url}")

    playwright = context = None
    try:
        playwright = sync_playwright().start()
        context = BrowserFactory.launch_persistent_context(playwright, headless=headless)

        page = context.new_page()
        print("  Opening notebook...")
        page.goto(notebook_url, wait_until="domcontentloaded")
        page.wait_for_url(re.compile(r"^https://notebooklm\.google\.com/"), timeout=10000)

        print("  Waiting for query input...")
        query_element = None
        for selector in QUERY_INPUT_SELECTORS:
            try:
                query_element = page.wait_for_selector(selector, timeout=10000, state="visible")
                if query_element:
                    break
            except Exception:
                continue

        if not query_element:
            print("  Could not find query input")
            return None

        print("  Typing question...")
        StealthUtils.human_type(page, QUERY_INPUT_SELECTORS[0], question)

        print("  Submitting...")
        page.keyboard.press("Enter")
        StealthUtils.random_delay(500, 1500)

        print("  Waiting for answer...")
        answer = None
        stable_count = 0
        last_text = None
        deadline = time.time() + 120

        while time.time() < deadline:
            try:
                thinking = page.query_selector("div.thinking-message")
                if thinking and thinking.is_visible():
                    time.sleep(1)
                    continue
            except Exception:
                pass

            for selector in RESPONSE_SELECTORS:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        text = elements[-1].inner_text().strip()
                        if text:
                            if text == last_text:
                                stable_count += 1
                                if stable_count >= 3:
                                    answer = text
                                    break
                            else:
                                stable_count = 0
                                last_text = text
                except Exception:
                    continue

            if answer:
                break
            time.sleep(1)

        if not answer:
            print("  Timeout waiting for answer")
            return None

        print("  Got answer!")
        return answer + FOLLOW_UP_REMINDER

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if context:
            try:
                context.close()
            except Exception:
                pass
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass
