#!/usr/bin/env python3
"""
Authentication helper for Spotify Queue Box.
Guides users through getting their refresh token.
"""

import os
import webbrowser
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# Required scopes for the application
SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
]

def main():
    print("=" * 70)
    print("Spotify Queue Box - Authentication Setup")
    print("=" * 70)
    print()

    # Check for existing credentials
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    if not client_id or not client_secret:
        print("⚠️  Missing Spotify App Credentials!")
        print()
        print("You need to create a Spotify app first:")
        print()
        print("1. Go to: https://developer.spotify.com/dashboard")
        print("2. Log in with your Spotify account")
        print("3. Click 'Create app'")
        print("4. Fill in the form:")
        print("   - App name: Spotify Queue Box (or any name)")
        print("   - App description: Personal queue manager")
        print("   - Redirect URI: http://127.0.0.1:8888/callback")
        print("   - API: Select 'Web API'")
        print("5. After creating, copy the Client ID and Client Secret")
        print()
        print("6. Create a .env file with:")
        print()
        print("   SPOTIFY_CLIENT_ID=your_client_id")
        print("   SPOTIFY_CLIENT_SECRET=your_client_secret")
        print("   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback")
        print()
        print("7. Run this script again")
        print()
        return

    print("✓ Found Client ID and Secret")
    print()
    print("Starting OAuth flow to get your refresh token...")
    print()

    # Build authorization URL
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "show_dialog": "true",
    }

    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(auth_params)}"

    print("=" * 70)
    print("INSTRUCTIONS:")
    print("=" * 70)
    print()
    print("1. Make sure the Flask app is running:")
    print("   python3 app.py")
    print()
    print("2. Your browser will open to Spotify's authorization page")
    print()
    print("3. Log in and click 'Agree' to authorize the app")
    print()
    print("4. You'll be redirected to a page showing your refresh token")
    print()
    print("5. Copy the refresh token and add it to your .env file:")
    print("   SPOTIFY_REFRESH_TOKEN=your_refresh_token_here")
    print()
    print("6. Restart the Flask app")
    print()
    print("=" * 70)
    print()

    input("Press ENTER to open your browser...")

    print()
    print("Opening browser...")
    webbrowser.open(auth_url)

    print()
    print("If your browser didn't open, go to this URL manually:")
    print()
    print(auth_url)
    print()
    print("After authorization, copy the refresh token to your .env file.")
    print()


if __name__ == "__main__":
    main()
