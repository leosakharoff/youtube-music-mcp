# YouTube Music MCP Server

Model Context Protocol server for YouTube Music integration. Allows AI assistants to search for music and create/manage playlists on your YouTube account.

## Features

- Search for tracks on YouTube Music
- Create new playlists
- Add tracks to existing playlists
- Batch operations (search and add multiple tracks at once)
- List your library playlists
- OAuth 2.0 authentication with Google

## Prerequisites

- Python 3.10+
- Google account with YouTube access
- Google Cloud project with YouTube Data API enabled

## Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **YouTube Data API v3**:
   - Go to **APIs & Services** → **Library**
   - Search for "YouTube Data API v3"
   - Click **Enable**

### 2. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - Choose **External** user type
   - Fill in the required fields (app name, support email)
   - Add scope: `https://www.googleapis.com/auth/youtube`
   - Add your email as a **Test user** (required while in testing mode)
4. Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: `YouTube Music MCP` (or any name)
5. Download the JSON file and save it as `client_secret.json` in the project root

### 3. Install the Server

```bash
# Clone the repository
git clone https://github.com/leosakharoff/youtube-music-mcp.git
cd youtube-music-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 4. Authenticate with Google

```bash
python -m src.auth
```

This opens a browser window for Google sign-in. After authorizing, your credentials are saved to `token.json` (gitignored).

## Usage

### Local Usage with Claude Desktop

Add to your Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "youtube-music": {
      "command": "/path/to/youtube-music-mcp/venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/youtube-music-mcp"
    }
  }
}
```

### Local Usage with Claude Code

```bash
claude mcp add youtube-music "python -m src.server" --cwd /path/to/youtube-music-mcp
```

### Remote Deployment (Render)

Deploy to Render for use with Claude web/iOS without your computer running.

1. Fork this repository to your GitHub account

2. Create a new **Web Service** on [Render](https://render.com):
   - Connect your GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m src.server_remote`

3. Set environment variable:
   - Generate base64 token: `cat token.json | base64`
   - Add env var: `YOUTUBE_TOKEN_B64` = (your base64 string)

4. Deploy! Your server will be at `https://your-service.onrender.com`

5. In Claude, add custom connector with URL: `https://your-service.onrender.com/sse`

> **Note:** Render free tier sleeps after 15 min of inactivity. First request may take ~30s to wake up.

## Example Prompts

Once connected to Claude, try:

- *"Search YouTube Music for 'Neu! Hallogallo'"*
- *"Create a playlist called 'Krautrock Classics'"*
- *"Add these tracks to my playlist: 'Can Vitamin C', 'Kraftwerk Autobahn', 'Tangerine Dream Phaedra'"*
- *"Show me my YouTube playlists"*

## Available Tools

| Tool | Description |
|------|-------------|
| `search_youtube_music` | Search for tracks (returns videoId for adding to playlists) |
| `create_playlist` | Create a new playlist (private, public, or unlisted) |
| `add_to_playlist` | Add videos to an existing playlist |
| `get_my_playlists` | List your YouTube playlists |
| `search_and_add` | Search for songs and add top results to a playlist |

## Troubleshooting

### "Access blocked" during OAuth

Your Google Cloud app is in testing mode. Add your email as a test user:
1. Go to **APIs & Services** → **OAuth consent screen**
2. Under **Test users**, click **Add Users**
3. Add your Google account email

### Token refresh errors

Delete `token.json` and run `python -m src.auth` again.

### Rate limiting

YouTube Data API has quotas. If you hit limits:
- Reduce batch sizes
- Wait before retrying
- Check your [API quota](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black src/ tests/
ruff check src/ tests/
```

## Security Notes

- `client_secret.json` and `token.json` contain sensitive credentials
- Both are gitignored by default - **never commit them**
- For remote deployment, use environment variables (base64 encoded)

## License

MIT License

## Acknowledgments

- Uses [YouTube Data API v3](https://developers.google.com/youtube/v3)
- Built with [Model Context Protocol](https://modelcontextprotocol.io/)
