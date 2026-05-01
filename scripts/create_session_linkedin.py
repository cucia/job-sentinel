#!/usr/bin/env python3
"""
LinkedIn Session Creator - Manual Method
Creates session by exporting cookies from your real browser
"""

import json
import os
import sys
import webbrowser
from pathlib import Path

# Project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

PLATFORM = "linkedin"
PLATFORM_NAME = "LinkedIn"
LOGIN_URL = "https://www.linkedin.com/login"
VERIFY_URL = "https://www.linkedin.com/feed/"
REQUIRED_COOKIES = ["li_at", "JSESSIONID"]


def print_instructions():
    """Print step-by-step instructions and open browser."""
    print(f"\n{'='*70}")
    print(f"  {PLATFORM_NAME.upper()} SESSION CREATOR")
    print(f"{'='*70}\n")

    print("Opening browser for login...")
    print(f"URL: {LOGIN_URL}\n")

    # Open default browser
    webbrowser.open(LOGIN_URL)

    print("STEP 1: Log In")
    print(f"  - Log in to {PLATFORM_NAME} in the browser window")
    print(f"  - Complete Cloudflare verification")
    print(f"  - Complete 2FA if required")
    print(f"  - Verify you see your dashboard: {VERIFY_URL}")
    print()
    print("STEP 2: Export Cookies")
    print("  - Install EditThisCookie extension if not installed:")
    print("    Chrome/Edge: https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg")
    print("  - Click the cookie extension icon")
    print("  - Click 'Export' button")
    print("  - Cookies copied to clipboard!")
    print()
    print("STEP 3: Save Session")
    print(f"  - When ready, press Enter in the terminal")
    print(f"  - Paste cookies and press Enter twice")
    print(f"\n{'='*70}\n")


def save_cookies():
    """Save cookies from input to session file."""
    print(f"\n{'='*70}")
    print(f"  SAVING {PLATFORM_NAME.upper()} SESSION")
    print(f"{'='*70}\n")
    print("Paste your exported cookies below and press Enter twice:")
    print()

    # Read multi-line input
    lines = []
    empty_count = 0
    while empty_count < 2:
        try:
            line = input()
            if line.strip():
                lines.append(line)
                empty_count = 0
            else:
                empty_count += 1
        except EOFError:
            break

    cookie_text = '\n'.join(lines).strip()

    if not cookie_text:
        print("\n[ERROR] No cookies provided!")
        return False

    try:
        # Parse JSON
        cookies = json.loads(cookie_text)

        if not isinstance(cookies, list):
            print("\n[ERROR] Cookies must be a JSON array!")
            return False

        # Fix sameSite values for Playwright compatibility
        for cookie in cookies:
            if 'sameSite' in cookie:
                # Playwright only accepts: Strict, Lax, None
                # EditThisCookie might export: no_restriction, unspecified, etc.
                same_site = cookie['sameSite']
                if same_site not in ['Strict', 'Lax', 'None']:
                    # Default to Lax for compatibility
                    cookie['sameSite'] = 'Lax'

        # Check for required cookies
        cookie_names = [c.get('name', '') for c in cookies]
        missing = [req for req in REQUIRED_COOKIES if req not in cookie_names]

        if missing:
            print(f"\n[WARNING] Missing expected cookies: {', '.join(missing)}")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False

        # Create session data
        session_data = {
            "cookies": cookies,
            "origins": []
        }

        # Save to session file
        session_dir = project_root / "sessions"
        session_dir.mkdir(exist_ok=True)
        session_path = session_dir / f"{PLATFORM}.json"

        with open(session_path, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"\n{'='*70}")
        print(f"  SUCCESS!")
        print(f"{'='*70}\n")
        print(f"Session saved to: {session_path}")
        print(f"Cookies saved: {len(cookies)}")
        print(f"\nRun Docker: docker-compose up -d")
        print(f"\n{'='*70}\n")

        return True

    except json.JSONDecodeError as e:
        print(f"\n[ERROR] Invalid JSON: {e}")
        print("\nMake sure you:")
        print("1. Used EditThisCookie extension")
        print("2. Clicked the Export button")
        print("3. Pasted the entire JSON array")
        return False


def main():
    # Open browser and show instructions
    print_instructions()

    # Wait a moment for user to log in
    print("\nWaiting for you to log in and export cookies...")
    print("When ready, press Enter to continue...")
    input()

    # Now save the cookies
    success = save_cookies()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
