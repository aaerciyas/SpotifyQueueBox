"""
Spotify API client for managing playback queue.
"""

import os
import base64
import time
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv

load_dotenv()

# Environment variables
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

# API endpoints
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"

# Token cache
_access_token = None
_access_token_expires_at = 0


class SpotifyAPIError(Exception):
    """Custom exception for Spotify API errors."""
    pass


def _get_basic_auth_header():
    """Generate Basic Auth header for token requests."""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise SpotifyAPIError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env")

    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    return {"Authorization": f"Basic {b64_auth}"}


def refresh_access_token():
    """Get a new access token using the refresh token."""
    global _access_token, _access_token_expires_at

    if not REFRESH_TOKEN:
        raise SpotifyAPIError(
            "SPOTIFY_REFRESH_TOKEN is not set. Run auth_helper.py to get one."
        )

    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }

    headers = _get_basic_auth_header()

    try:
        resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 400:
            raise SpotifyAPIError(
                "Invalid refresh token. Run auth_helper.py to get a new one."
            ) from e
        raise SpotifyAPIError(f"Failed to refresh token: {e}") from e
    except requests.exceptions.RequestException as e:
        raise SpotifyAPIError(f"Network error while refreshing token: {e}") from e

    token_info = resp.json()
    _access_token = token_info["access_token"]
    expires_in = token_info.get("expires_in", 3600)
    # Refresh 60 seconds early to avoid expiration issues
    _access_token_expires_at = int(time.time()) + expires_in - 60

    return _access_token


def get_access_token():
    """Get a valid access token, refreshing if necessary."""
    global _access_token, _access_token_expires_at

    now = int(time.time())
    if _access_token is None or now >= _access_token_expires_at:
        return refresh_access_token()

    return _access_token


def extract_track_id_from_url(track_url: str) -> str | None:
    """
    Extract Spotify track ID from various URL formats.

    Supported formats:
    - https://open.spotify.com/track/<TRACK_ID>
    - https://open.spotify.com/track/<TRACK_ID>?si=...
    - spotify:track:<TRACK_ID>
    - Just the track ID itself

    Args:
        track_url: Spotify track URL or URI

    Returns:
        Track ID string or None if invalid
    """
    if not track_url:
        return None

    track_url = track_url.strip()

    # Handle direct track IDs (22 character alphanumeric strings)
    if len(track_url) == 22 and track_url.isalnum():
        return track_url

    # Handle open.spotify.com URLs
    if "open.spotify.com/track/" in track_url:
        try:
            path = urlparse(track_url).path
            parts = path.strip("/").split("/")
            if len(parts) >= 2 and parts[0] == "track":
                return parts[1]
        except Exception:
            return None

    # Handle spotify:track: URIs
    elif track_url.startswith("spotify:track:"):
        return track_url.split(":")[-1]

    return None


def add_track_to_queue(track_id: str) -> dict:
    """
    Add a track to the user's playback queue.

    Args:
        track_id: Spotify track ID

    Returns:
        dict with success status

    Raises:
        SpotifyAPIError: If the request fails
    """
    access_token = get_access_token()
    url = f"{API_BASE_URL}/me/player/queue"

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    params = {
        "uri": f"spotify:track:{track_id}"
    }

    try:
        resp = requests.post(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return {"success": True, "message": "Track added to queue"}

    except requests.exceptions.HTTPError as e:
        if resp.status_code == 404:
            raise SpotifyAPIError(
                "No active device found. Please open Spotify on a device and start playing something."
            ) from e
        elif resp.status_code == 403:
            raise SpotifyAPIError(
                "Insufficient permissions. Make sure your token has the 'user-modify-playback-state' scope."
            ) from e
        else:
            raise SpotifyAPIError(f"Spotify API error: {resp.status_code} - {resp.text}") from e

    except requests.exceptions.RequestException as e:
        raise SpotifyAPIError(f"Network error: {e}") from e


def get_current_playback():
    """
    Get information about the user's current playback.

    Returns:
        dict with playback information or None if nothing is playing
    """
    access_token = get_access_token()
    url = f"{API_BASE_URL}/me/player"

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 204:  # No content - nothing playing
            return None

        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.RequestException as e:
        raise SpotifyAPIError(f"Failed to get playback info: {e}") from e
