# Spotify Queue API

A lightweight Flask API that lets you add tracks to your Spotify playback queue via HTTP requests.

## Overview

This API provides a simple interface to control your Spotify queue remotely. Perfect for building custom Spotify integrations, automation workflows, or remote control applications.

### Key Features

- **Simple REST API** - Add tracks with a single POST request
- **Multiple URL Formats** - Supports Spotify web URLs, URIs, and track IDs
- **Current Playback Info** - Check what's playing on your devices
- **Auto Token Refresh** - Handles Spotify OAuth automatically
- **Built-in Setup** - Integrated OAuth callback for easy configuration
- **Zero Dependencies\*** - Just Flask, requests, and python-dotenv

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/SpotifyQueueBox.git
cd SpotifyQueueBox
./spotify-queue.sh setup

# 2. Start the server
./spotify-queue.sh start

# 3. Add a track
./spotify-queue.sh add 'https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp'
```

## API Endpoints

| Endpoint     | Method | Description               |
| ------------ | ------ | ------------------------- |
| `/health`    | GET    | Check API health status   |
| `/add_track` | POST   | Add a track to your queue |
| `/playback`  | GET    | Get current playback info |
| `/callback`  | GET    | OAuth callback (internal) |

### Example Request

```bash
curl -X POST http://127.0.0.1:8888/add_track \
  -H "Content-Type: application/json" \
  -d '{"track_url": "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"}'
```

**Response:**

```json
{
  "status": "queued",
  "track_id": "3n3Ppam7vgaVa1iaRUc9Lp",
  "message": "Track added to queue"
}
```

## Requirements

- Python 3.8+
- Spotify Premium account
- Spotify Developer App (free)

## How It Works

1. Users send HTTP requests to add tracks
2. API uses your Spotify refresh token for authentication
3. Tracks are added to your active Spotify device's queue
4. Automatic token refresh keeps the session alive

## Project Structure

```
SpotifyQueueBox/
├── app.py               # Main Flask application
├── spotify_client.py    # Spotify API client
├── spotify-queue.sh     # CLI helper script
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README.md          # This file
```

## Configuration

Required environment variables in `.env`:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
SPOTIFY_REFRESH_TOKEN=your_refresh_token
```

## Security Notes

- **Never commit `.env`** - It contains sensitive credentials
- **Refresh tokens don't expire** - Treat them like passwords
- **Use HTTPS in production** - For public deployments
- **Rate limiting** - Consider adding if publicly exposed

## Contributing

Contributions are welcome! Some ideas:

- Add support for playlists and albums
- Implement playback controls (play, pause, skip)
- Add queue management (view, reorder, remove tracks)
- Create a web UI
- Add authentication/authorization
- Docker support

## Troubleshooting

**No active device found?**
Make sure Spotify is open and playing on at least one device.

**Connection refused?**
Ensure the server is running: `./spotify-queue.sh start`

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with:

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) - Music control
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Environment management

---
