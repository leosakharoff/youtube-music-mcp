"""
Remote MCP Server for YouTube Music (HTTP/SSE transport)
For deployment to Railway, Fly.io, etc.
"""
import os
import json
import base64
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from .ytmusic_client import YouTubeMusicClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("youtube-music-mcp")

# Global client instance
ytmusic_client: YouTubeMusicClient = None


def init_youtube_client():
    """Initialize YouTube client from environment variables"""
    global ytmusic_client

    # Get credentials from environment (supports base64 or raw JSON)
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    token_b64 = os.environ.get("YOUTUBE_TOKEN_B64")

    if token_b64:
        # Base64 encoded token (preferred - avoids escaping issues)
        token_json = base64.b64decode(token_b64).decode("utf-8")

    if not token_json:
        raise RuntimeError("YOUTUBE_TOKEN_JSON or YOUTUBE_TOKEN_B64 environment variable not set")

    try:
        # Clean any whitespace/newlines that might have snuck in
        token_json = token_json.strip().replace('\n', '').replace('\r', '')
        token_data = json.loads(token_json)
        credentials = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes", ["https://www.googleapis.com/auth/youtube"]),
        )

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        youtube = build("youtube", "v3", credentials=credentials)
        ytmusic_client = YouTubeMusicClient(youtube)
        logger.info("YouTube client initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize YouTube client: {e}")
        raise


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools for YouTube Music."""
    return [
        Tool(
            name="search_youtube_music",
            description="Search for music on YouTube. Returns track info including videoId for playlists.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'Neu! Hallogallo')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (1-50)",
                        "default": 20,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="create_playlist",
            description="Create a new YouTube playlist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Playlist title"},
                    "description": {"type": "string", "description": "Playlist description", "default": ""},
                    "privacy_status": {
                        "type": "string",
                        "enum": ["private", "public", "unlisted"],
                        "default": "private",
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="add_to_playlist",
            description="Add videos to an existing playlist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "Target playlist ID"},
                    "video_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Video IDs to add",
                    },
                },
                "required": ["playlist_id", "video_ids"],
            },
        ),
        Tool(
            name="get_my_playlists",
            description="Get your YouTube playlists.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 25},
                },
            },
        ),
        Tool(
            name="search_and_add",
            description="Search for songs and add top results to a playlist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "Target playlist ID"},
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Search queries (e.g., ['Artist - Song'])",
                    },
                },
                "required": ["playlist_id", "queries"],
            },
        ),
        Tool(
            name="get_playlist_details",
            description="Get details and all tracks from a YouTube playlist. Returns all tracks by default (no limit).",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "Playlist ID to retrieve"},
                },
                "required": ["playlist_id"],
            },
        ),
        Tool(
            name="delete_playlist",
            description="Delete a YouTube playlist. This action cannot be undone.",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "Playlist ID to delete"},
                },
                "required": ["playlist_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""
    try:
        if name == "search_youtube_music":
            results = await ytmusic_client.search_tracks(
                query=arguments["query"],
                limit=arguments.get("limit", 20),
            )
            if not results:
                return [TextContent(type="text", text="No results found.")]

            lines = [f"Found {len(results)} results:\n"]
            for r in results:
                artist = r["artists"][0]["name"] if r["artists"] else "Unknown"
                lines.append(f"- {r['title']} by {artist}\n  videoId: {r['videoId']}")
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "create_playlist":
            result = await ytmusic_client.create_playlist(
                title=arguments["title"],
                description=arguments.get("description", ""),
                privacy_status=arguments.get("privacy_status", "private"),
            )
            return [TextContent(
                type="text",
                text=f"Created: {result['title']}\nID: {result['playlistId']}\nURL: {result['url']}"
            )]

        elif name == "add_to_playlist":
            result = await ytmusic_client.add_playlist_items(
                playlist_id=arguments["playlist_id"],
                video_ids=arguments["video_ids"],
            )
            return [TextContent(
                type="text",
                text=f"Added {result['addedCount']} tracks to playlist"
            )]

        elif name == "get_my_playlists":
            playlists = await ytmusic_client.get_library_playlists(
                limit=arguments.get("limit", 25)
            )
            if not playlists:
                return [TextContent(type="text", text="No playlists found.")]

            lines = [f"Your playlists ({len(playlists)}):\n"]
            for p in playlists:
                lines.append(f"- {p['title']} ({p['count']} tracks)\n  ID: {p['playlistId']}")
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "search_and_add":
            result = await ytmusic_client.search_and_add_to_playlist(
                playlist_id=arguments["playlist_id"],
                search_queries=arguments["queries"],
            )
            lines = [f"Added {result['addedCount']} tracks:\n"]
            for t in result["addedTracks"]:
                lines.append(f"  ✓ {t['query']} → {t['matched']}")
            if result["failedQueries"]:
                lines.append(f"\nFailed: {', '.join(result['failedQueries'])}")
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "get_playlist_details":
            result = await ytmusic_client.get_playlist(
                playlist_id=arguments["playlist_id"],
            )
            lines = [
                f"Playlist: {result['title']}",
                f"Description: {result['description'] or 'No description'}",
                f"Tracks ({result['trackCount']}):\n",
            ]
            for t in result["tracks"]:
                artist = t["artists"][0]["name"] if t.get("artists") else "Unknown"
                lines.append(f"  - {t['title']} - {artist}")
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "delete_playlist":
            result = await ytmusic_client.delete_playlist(
                playlist_id=arguments["playlist_id"],
            )
            return [TextContent(type="text", text=f"Deleted playlist: {result['playlistId']}")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# SSE transport for MCP
sse = SseServerTransport("/messages/")


async def handle_sse(request):
    """Handle SSE connection for MCP"""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app.run(
            streams[0], streams[1], app.create_initialization_options()
        )


async def handle_messages(request):
    """Handle POST messages for MCP"""
    await sse.handle_post_message(request.scope, request.receive, request._send)


async def health(request):
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "service": "youtube-music-mcp"})


# Starlette app with routes
starlette_app = Starlette(
    debug=False,
    routes=[
        Route("/health", health),
        Route("/sse", handle_sse),
        Route("/messages/", handle_messages, methods=["POST"]),
    ],
)


def main():
    """Run the HTTP server"""
    init_youtube_client()

    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on port {port}")

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
