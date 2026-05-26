import json
import time
import re
import shutil
from typing import Any, Dict

from patchright.sync_api import sync_playwright, BrowserContext

from notebooklm.config import BROWSER_STATE_DIR, STATE_FILE, AUTH_INFO_FILE, DATA_DIR
from notebooklm.browser import BrowserFactory


class AuthManager:
    """
    Manages authentication and browser state for NotebookLM.

    Uses a hybrid approach: persistent browser profile for fingerprint consistency
    plus manual cookie injection from state.json (workaround for Playwright bug #36139).
    See: https://github.com/microsoft/playwright/issues/36139
    """

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        BROWSER_STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.state_file = STATE_FILE
        self.auth_info_file = AUTH_INFO_FILE
        self.browser_state_dir = BROWSER_STATE_DIR

    def is_authenticated(self) -> bool:
        if not self.state_file.exists():
            return False
        age_days = (time.time() - self.state_file.stat().st_mtime) / 86400
        if age_days > 7:
            print(f"Warning: Browser state is {age_days:.1f} days old, may need re-authentication")
        return True

    def get_auth_info(self) -> Dict[str, Any]:
        info = {
            "authenticated": self.is_authenticated(),
            "state_file": str(self.state_file),
            "state_exists": self.state_file.exists(),
        }
        if self.auth_info_file.exists():
            try:
                with open(self.auth_info_file, "r") as f:
                    info.update(json.load(f))
            except Exception:
                pass
        if info["state_exists"]:
            info["state_age_hours"] = (time.time() - self.state_file.stat().st_mtime) / 3600
        return info

    def setup_auth(self, headless: bool = False, timeout_minutes: int = 10) -> bool:
        print(f"Starting authentication setup (timeout: {timeout_minutes} minutes)...")
        playwright = context = None
        try:
            playwright = sync_playwright().start()
            context = BrowserFactory.launch_persistent_context(playwright, headless=headless)
            page = context.new_page()
            page.goto("https://notebooklm.google.com", wait_until="domcontentloaded")

            if "notebooklm.google.com" in page.url and "accounts.google.com" not in page.url:
                print("Already authenticated!")
                self._save_browser_state(context)
                return True

            print(f"\nPlease log in to your Google account in the browser window...")
            print(f"Waiting up to {timeout_minutes} minutes for login...")

            try:
                page.wait_for_url(
                    re.compile(r"^https://notebooklm\.google\.com/"),
                    timeout=int(timeout_minutes * 60 * 1000),
                )
                print("Login successful!")
                self._save_browser_state(context)
                self._save_auth_info()
                return True
            except Exception as e:
                print(f"Authentication timeout: {e}")
                return False
        except Exception as e:
            print(f"Error: {e}")
            return False
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

    def _save_browser_state(self, context: BrowserContext):
        try:
            context.storage_state(path=str(self.state_file))
            print(f"Saved browser state to: {self.state_file}")
        except Exception as e:
            print(f"Failed to save browser state: {e}")
            raise

    def _save_auth_info(self):
        try:
            info = {
                "authenticated_at": time.time(),
                "authenticated_at_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(self.auth_info_file, "w") as f:
                json.dump(info, f, indent=2)
        except Exception:
            pass

    def clear_auth(self) -> bool:
        print("Clearing authentication data...")
        try:
            if self.state_file.exists():
                self.state_file.unlink()
                print("Removed browser state")
            if self.auth_info_file.exists():
                self.auth_info_file.unlink()
                print("Removed auth info")
            if self.browser_state_dir.exists():
                shutil.rmtree(self.browser_state_dir)
                self.browser_state_dir.mkdir(parents=True, exist_ok=True)
                print("Cleared browser data")
            return True
        except Exception as e:
            print(f"Error clearing auth: {e}")
            return False

    def re_auth(self, headless: bool = False, timeout_minutes: int = 10) -> bool:
        print("Starting re-authentication...")
        self.clear_auth()
        return self.setup_auth(headless, timeout_minutes)

    def validate_auth(self) -> bool:
        if not self.is_authenticated():
            return False
        print("Validating authentication...")
        playwright = context = None
        try:
            playwright = sync_playwright().start()
            context = BrowserFactory.launch_persistent_context(playwright, headless=True)
            page = context.new_page()
            page.goto("https://notebooklm.google.com", wait_until="domcontentloaded", timeout=30000)
            if "notebooklm.google.com" in page.url and "accounts.google.com" not in page.url:
                print("Authentication is valid")
                return True
            else:
                print("Authentication is invalid (redirected to login)")
                return False
        except Exception as e:
            print(f"Validation failed: {e}")
            return False
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
