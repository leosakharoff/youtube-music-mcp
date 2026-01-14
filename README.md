# YouTube Music MCP Server

Model Context Protocol server for YouTube Music integration. Allows AI assistants to search for music and create/manage playlists.

## Features

- Search for tracks, albums, artists, and playlists
- Create new playlists
- Add tracks to existing playlists
- Batch operations (search and add multiple tracks at once)
- Get library playlists
- OAuth 2.0 authentication

## Prerequisites

- Python 3.10+
- YouTube Music account (free or premium)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/youtube-music-mcp.git
   cd youtube-music-mcp
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. Set up OAuth authentication:
   ```bash
   python -m src.auth
   ```

   Follow the prompts to authenticate with your YouTube Music account. You'll be given a URL to visit, where you'll sign in with Google and authorize the application.

## Usage with Claude Desktop

Add to your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "youtube-music": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/youtube-music-mcp"
    }
  }
}
```

Or run the install helper:
```bash
python install.py
```

## Usage with Claude Code

```bash
claude mcp add youtube-music "python -m src.server" --cwd /path/to/youtube-music-mcp
```

## Example Usage

Once connected to Claude, you can:

**Search for music:**
> "Search YouTube Music for 'Manuel Göttsching E2-E4'"

**Create a playlist:**
> "Create a YouTube Music playlist called 'Motorik Meditation' with description 'Hypnotic krautrock and ambient jazz'"

**Add tracks:**
> "Search for 'Neu! Hallogallo' and add the top result to playlist [playlist_id]"

**Batch add tracks:**
> "Add these tracks to my playlist: 'Alice Coltrane Journey in Satchidananda', 'Pharoah Sanders Harvest Time', 'Popol Vuh In Den Gärten Pharaos'"

**List your playlists:**
> "Show me my YouTube Music playlists"

## Available Tools

### search_youtube_music
Search for music on YouTube Music.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search query |
| limit | integer | No | Max results (1-100, default 20) |
| filter | string | No | "songs", "videos", "albums", "artists", or "playlists" |

### create_youtube_music_playlist
Create a new playlist.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| title | string | Yes | Playlist name |
| description | string | No | Playlist description |
| privacy_status | string | No | "PRIVATE", "PUBLIC", or "UNLISTED" |
| video_ids | array | No | Initial tracks to add |

### add_tracks_to_playlist
Add tracks to an existing playlist.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| playlist_id | string | Yes | Target playlist ID |
| video_ids | array | Yes | Video IDs to add |

### search_and_add_to_playlist
Search for tracks and add top results to a playlist.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| playlist_id | string | Yes | Target playlist ID |
| search_queries | array | Yes | List of search queries |

### get_playlist_details
Get playlist information and tracks.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| playlist_id | string | Yes | Playlist ID |
| limit | integer | No | Max tracks to return (default 100) |

### get_library_playlists
Get your library playlists.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | No | Max playlists to return (default 25) |

## Development

### Running Tests
```bash
pip install -e ".[dev]"
pytest tests/ -v
```

### Code Formatting
```bash
black src/ tests/
ruff check src/ tests/
```

## Troubleshooting

### OAuth Issues
If authentication fails:
1. Delete `oauth.json`
2. Run `python -m src.auth` again
3. Make sure you're using the correct Google account

### "No module named 'mcp'" Error
```bash
pip install mcp
```

### Rate Limiting
YouTube Music API has rate limits. If you hit limits:
- Add delays between bulk operations
- Reduce batch sizes
- Wait before retrying

## License

MIT License

## Acknowledgments

- Built with [ytmusicapi](https://github.com/sigma67/ytmusicapi)
- Uses [Model Context Protocol](https://modelcontextprotocol.io/)
