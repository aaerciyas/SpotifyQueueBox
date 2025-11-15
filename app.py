"""
Flask API for adding tracks to Spotify queue.
"""

import os
import base64
import requests
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from spotify_client import (
    extract_track_id_from_url,
    add_track_to_queue,
    get_current_playback,
    SpotifyAPIError
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')


@app.route("/", methods=["GET"])
def index():
    """Serve the web UI."""
    return send_from_directory('static', 'index.html')


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "Spotify Queue API"})


@app.route("/add_track", methods=["POST"])
def add_track():
    """
    Add a track to the Spotify queue.

    Request body:
        {
            "track_url": "https://open.spotify.com/track/..." or "spotify:track:..." or track ID
        }

    Returns:
        200: {"status": "queued", "track_id": "..."}
        400: {"error": "error message"}
        500: {"error": "error message"}
    """
    data = request.get_json(silent=True) or {}
    track_url = data.get("track_url")

    if not track_url:
        return jsonify({"error": "track_url is required"}), 400

    track_id = extract_track_id_from_url(track_url)
    if not track_id:
        return jsonify({
            "error": "Invalid track_url. Use format: https://open.spotify.com/track/... or spotify:track:..."
        }), 400

    try:
        result = add_track_to_queue(track_id)
        return jsonify({
            "status": "queued",
            "track_id": track_id,
            "message": result.get("message", "Track added to queue")
        }), 200

    except SpotifyAPIError as e:
        # Return specific error messages from SpotifyAPIError
        error_msg = str(e)
        status_code = 500

        # Map specific errors to appropriate status codes
        if "No active device" in error_msg:
            status_code = 404
        elif "Insufficient permissions" in error_msg or "Invalid refresh token" in error_msg:
            status_code = 401

        return jsonify({"error": error_msg}), status_code

    except Exception as e:
        # Catch-all for unexpected errors
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/callback", methods=["GET"])
def callback():
    """
    OAuth callback endpoint for Spotify authorization.
    This receives the authorization code and exchanges it for a refresh token.
    """
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authorization Error</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    .error { background: #ffebee; border: 2px solid #f44336; padding: 20px; border-radius: 8px; }
                    h1 { color: #f44336; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>❌ Authorization Error</h1>
                    <p>Error: {{ error }}</p>
                    <p>Please try again or check your Spotify app settings.</p>
                </div>
            </body>
            </html>
        """, error=error)

    if not code:
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Missing Code</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    .error { background: #fff3cd; border: 2px solid #ffc107; padding: 20px; border-radius: 8px; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>⚠️ No Authorization Code</h1>
                    <p>No authorization code was received from Spotify.</p>
                </div>
            </body>
            </html>
        """)

    # Exchange code for tokens
    try:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

        auth_str = f"{client_id}:{client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }

        response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data, timeout=10)
        response.raise_for_status()
        tokens = response.json()

        refresh_token = tokens.get("refresh_token")

        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authorization Successful</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    .success { background: #e8f5e9; border: 2px solid #4caf50; padding: 20px; border-radius: 8px; }
                    .token-box { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 20px 0; font-family: monospace; word-break: break-all; }
                    .copy-btn { background: #1DB954; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; }
                    .copy-btn:hover { background: #1ed760; }
                    .instructions { background: #fff9c4; padding: 15px; border-radius: 4px; margin: 20px 0; }
                    h1 { color: #4caf50; }
                </style>
            </head>
            <body>
                <div class="success">
                    <h1>✅ Authorization Successful!</h1>
                    <p>Your refresh token has been generated. Follow these steps:</p>

                    <div class="instructions">
                        <strong>Step 1:</strong> Copy the refresh token below
                    </div>

                    <div class="token-box" id="token">{{ refresh_token }}</div>

                    <button class="copy-btn" onclick="copyToken()">📋 Copy Token</button>

                    <div class="instructions" style="margin-top: 20px;">
                        <strong>Step 2:</strong> Add this line to your <code>.env</code> file:<br>
                        <code>SPOTIFY_REFRESH_TOKEN={{ refresh_token }}</code>
                    </div>

                    <div class="instructions">
                        <strong>Step 3:</strong> Restart the Flask app for changes to take effect
                    </div>

                    <p style="color: #666; font-size: 14px; margin-top: 30px;">
                        You can close this window once you've copied the token.
                    </p>
                </div>

                <script>
                    function copyToken() {
                        const token = document.getElementById('token').textContent;
                        navigator.clipboard.writeText(token).then(() => {
                            const btn = document.querySelector('.copy-btn');
                            btn.textContent = '✓ Copied!';
                            btn.style.background = '#4caf50';
                            setTimeout(() => {
                                btn.textContent = '📋 Copy Token';
                                btn.style.background = '#1DB954';
                            }, 2000);
                        });
                    }
                </script>
            </body>
            </html>
        """, refresh_token=refresh_token)

    except Exception as e:
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Token Exchange Error</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    .error { background: #ffebee; border: 2px solid #f44336; padding: 20px; border-radius: 8px; }
                    h1 { color: #f44336; }
                    code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>❌ Error Exchanging Token</h1>
                    <p>Failed to exchange authorization code for refresh token.</p>
                    <p><strong>Error:</strong> <code>{{ error }}</code></p>
                    <p>The authorization code may have expired. Please try again.</p>
                </div>
            </body>
            </html>
        """, error=str(e))


@app.route("/playback", methods=["GET"])
def playback():
    """
    Get current playback information.

    Returns:
        200: Playback information
        204: Nothing currently playing
        500: Error message
    """
    try:
        info = get_current_playback()

        if info is None:
            return jsonify({"status": "no_playback", "message": "Nothing is currently playing"}), 200

        # Extract useful information
        track = info.get("item", {})
        return jsonify({
            "is_playing": info.get("is_playing"),
            "device": {
                "name": info.get("device", {}).get("name"),
                "type": info.get("device", {}).get("type"),
            },
            "track": {
                "name": track.get("name"),
                "artist": ", ".join([artist.get("name") for artist in track.get("artists", [])]),
                "album": track.get("album", {}).get("name"),
                "duration_ms": track.get("duration_ms"),
            },
            "progress_ms": info.get("progress_ms"),
        }), 200

    except SpotifyAPIError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.errorhandler(404)
def not_found(_):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(_):
    """Handle 405 errors."""
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)
