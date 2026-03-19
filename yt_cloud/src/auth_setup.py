"""
auth_setup.py — One-time setup. Run this ONCE on your laptop.
It opens your browser, you log into YouTube, and it saves your token.
After this, everything runs on GitHub Actions — your laptop stays off.

Usage: python src/auth_setup.py
"""

import base64
import os
import pickle
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.oauth2.credentials

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

def main():
    print("\n" + "="*60)
    print("  YOUTUBE AUTHENTICATION SETUP")
    print("  This runs ONCE on your laptop. After this,")
    print("  GitHub Actions handles everything automatically.")
    print("="*60 + "\n")

    # Find client_secrets.json
    secrets_path = Path("client_secrets.json")
    if not secrets_path.exists():
        secrets_path = Path("src/client_secrets.json")
    if not secrets_path.exists():
        print("ERROR: client_secrets.json not found!")
        print("Download it from Google Cloud Console → APIs → Credentials")
        sys.exit(1)

    print(f"Using credentials from: {secrets_path}")
    print("\nStep 1: A browser window will open.")
    print("Step 2: Log in with your YouTube channel's Google account.")
    print("Step 3: Click 'Allow' to grant upload access.")
    print("\nPress Enter to open browser...")
    input()

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")

    # Save token.pickle
    token_path = Path("token.pickle")
    with open(token_path, "wb") as f:
        pickle.dump(creds, f)
    print(f"\n✅ Token saved to: {token_path}")

    # Encode both files to base64 for GitHub Secrets
    with open(secrets_path, "rb") as f:
        creds_b64 = base64.b64encode(f.read()).decode()

    with open(token_path, "rb") as f:
        token_b64 = base64.b64encode(f.read()).decode()

    # Save encoded strings to files
    Path("YOUTUBE_CREDS_B64.txt").write_text(creds_b64)
    Path("YOUTUBE_TOKEN_B64.txt").write_text(token_b64)

    print("\n" + "="*60)
    print("  SETUP COMPLETE! Now add these as GitHub Secrets:")
    print("="*60)
    print("\n1. Go to your GitHub repo → Settings → Secrets → Actions")
    print("2. Click 'New repository secret' and add:")
    print("\n   Name: YOUTUBE_CREDS_B64")
    print("   Value: (copy entire content of YOUTUBE_CREDS_B64.txt)")
    print("\n   Name: YOUTUBE_TOKEN_B64")
    print("   Value: (copy entire content of YOUTUBE_TOKEN_B64.txt)")
    print("\n3. Also add your other secrets:")
    print("   GROQ_API_KEY = (from console.groq.com)")
    print("   PEXELS_API_KEY = (from pexels.com/api)")
    print("\n" + "="*60)
    print("  After adding secrets, push your code to GitHub.")
    print("  GitHub Actions will handle EVERYTHING automatically!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
