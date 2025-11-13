#!/bin/bash

# Spotify Queue API - Command Line Helper
# Simple shell script for interacting with the Spotify Queue API

API_URL="http://127.0.0.1:8888"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions

show_help() {
    echo -e "${BLUE}Spotify Queue API - Command Line Helper${NC}"
    echo ""
    echo "Usage: ./spotify-queue.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start                Start the Flask API server"
    echo "  stop                 Stop the Flask API server"
    echo "  health               Check API health status"
    echo "  add <url>           Add a track to the queue"
    echo "  playing              Show what's currently playing"
    echo "  setup                Run initial setup (get refresh token)"
    echo "  help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./spotify-queue.sh add 'https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp'"
    echo "  ./spotify-queue.sh playing"
    echo "  ./spotify-queue.sh health"
}

start_server() {
    echo -e "${YELLOW}Starting Spotify Queue API...${NC}"

    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo -e "${RED}Error: Virtual environment not found. Run setup first.${NC}"
        exit 1
    fi

    # Check if .env exists
    if [ ! -f ".env" ]; then
        echo -e "${RED}Error: .env file not found. Run setup first.${NC}"
        exit 1
    fi

    # Activate venv and start server
    source venv/bin/activate
    python app.py &

    echo $! > .server.pid
    echo -e "${GREEN}Server started on http://127.0.0.1:8888${NC}"
    echo "PID: $(cat .server.pid)"
}

stop_server() {
    if [ -f ".server.pid" ]; then
        PID=$(cat .server.pid)
        echo -e "${YELLOW}Stopping server (PID: $PID)...${NC}"
        kill $PID 2>/dev/null
        rm .server.pid
        echo -e "${GREEN}Server stopped${NC}"
    else
        echo -e "${YELLOW}No server PID file found. Trying to kill by port...${NC}"
        lsof -ti:8888 | xargs kill -9 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Server stopped${NC}"
        else
            echo -e "${YELLOW}No server running on port 8888${NC}"
        fi
    fi
}

check_health() {
    echo -e "${YELLOW}Checking API health...${NC}"

    response=$(curl -s "$API_URL/health")

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}API is running!${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        echo -e "${RED}API is not responding${NC}"
        echo "Make sure the server is running: ./spotify-queue.sh start"
        exit 1
    fi
}

add_track() {
    local track_url="$1"

    if [ -z "$track_url" ]; then
        echo -e "${RED}Error: Track URL is required${NC}"
        echo "Usage: ./spotify-queue.sh add <track_url>"
        exit 1
    fi

    echo -e "${YELLOW}Adding track to queue...${NC}"

    response=$(curl -s -X POST "$API_URL/add_track" \
        -H "Content-Type: application/json" \
        -d "{\"track_url\": \"$track_url\"}")

    if echo "$response" | grep -q '"status":"queued"'; then
        echo -e "${GREEN}Track added successfully!${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        echo -e "${RED}Failed to add track${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    fi
}

show_playing() {
    echo -e "${YELLOW}Getting current playback...${NC}"

    response=$(curl -s "$API_URL/playback")

    if [ $? -eq 0 ]; then
        # Check if jq is available for pretty printing
        if command -v jq &> /dev/null; then
            echo "$response" | jq '.'

            # Extract and display track info nicely
            is_playing=$(echo "$response" | jq -r '.is_playing // false')
            if [ "$is_playing" = "true" ]; then
                track_name=$(echo "$response" | jq -r '.track.name')
                artist=$(echo "$response" | jq -r '.track.artist')
                echo ""
                echo -e "${GREEN}♪ Now Playing: $track_name - $artist${NC}"
            else
                echo -e "${YELLOW}Nothing is currently playing${NC}"
            fi
        else
            echo "$response"
        fi
    else
        echo -e "${RED}Failed to get playback info${NC}"
        exit 1
    fi
}

run_setup() {
    echo -e "${BLUE}=== Spotify Queue API Setup ===${NC}"
    echo ""

    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi

    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}Virtual environment created${NC}"
    fi

    # Install dependencies
    echo -e "${YELLOW}Installing dependencies...${NC}"
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null
    echo -e "${GREEN}Dependencies installed${NC}"

    # Create .env from example
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}.env file created${NC}"
            echo -e "${YELLOW}Please edit .env and add your Spotify credentials${NC}"
        fi
    else
        echo -e "${YELLOW}.env file already exists${NC}"
    fi

    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Edit .env and add your Spotify Client ID and Secret"
    echo "2. Run: ./spotify-queue.sh start"
    echo "3. Visit the authorization URL to get your refresh token"
    echo "4. Add the refresh token to .env"
    echo "5. Restart the server"
    echo ""
}

# Main script

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    health)
        check_health
        ;;
    add)
        add_track "$2"
        ;;
    playing)
        show_playing
        ;;
    setup)
        run_setup
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
