#!/usr/bin/env python3
"""Auth management CLI: setup | status | reauth | clear | validate"""

import argparse
import sys

from notebooklm.auth import AuthManager


def main():
    parser = argparse.ArgumentParser(description="Manage NotebookLM authentication")
    sub = parser.add_subparsers(dest="command")

    setup_p = sub.add_parser("setup", help="First-time authentication (opens browser)")
    setup_p.add_argument("--headless", action="store_true")
    setup_p.add_argument("--timeout", type=float, default=10, help="Minutes to wait for login")

    sub.add_parser("status", help="Show auth status")
    sub.add_parser("validate", help="Verify auth works by loading NotebookLM")
    sub.add_parser("clear", help="Delete all auth data")

    reauth_p = sub.add_parser("reauth", help="Clear and re-authenticate")
    reauth_p.add_argument("--timeout", type=float, default=10)

    args = parser.parse_args()
    auth = AuthManager()

    if args.command == "setup":
        ok = auth.setup_auth(headless=args.headless, timeout_minutes=args.timeout)
        if ok:
            print("\nAuthentication setup complete! You can now use the other CLI commands.")
        else:
            print("\nAuthentication setup failed.")
            sys.exit(1)

    elif args.command == "status":
        info = auth.get_auth_info()
        print("\nAuthentication Status:")
        print(f"  Authenticated : {'Yes' if info['authenticated'] else 'No'}")
        if info.get("state_age_hours"):
            print(f"  State age     : {info['state_age_hours']:.1f} hours")
        if info.get("authenticated_at_iso"):
            print(f"  Last auth     : {info['authenticated_at_iso']}")
        print(f"  State file    : {info['state_file']}")

    elif args.command == "validate":
        if auth.validate_auth():
            print("Authentication is valid and working.")
        else:
            print("Authentication is invalid or expired.")
            print("Run: python cli/auth.py reauth")
            sys.exit(1)

    elif args.command == "clear":
        if auth.clear_auth():
            print("Authentication cleared.")

    elif args.command == "reauth":
        ok = auth.re_auth(timeout_minutes=args.timeout)
        if ok:
            print("\nRe-authentication complete!")
        else:
            print("\nRe-authentication failed.")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
