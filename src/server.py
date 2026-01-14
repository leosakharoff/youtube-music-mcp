"""
MCP Server for YouTube Music
"""
import asyncio
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server

from .auth import AuthManager
from .ytmusic_client import YouTubeMusicClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
app = Server("youtube-music-mcp")

# Global client instance
ytmusic_client: YouTubeMusicClient = None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available MCP tools for YouTube Music.
    """
    return [
        Tool(
            name="search_youtube_music",
            description="""
Search for music on YouTube Music. Returns track information including
videoId (needed for adding to playlists), title, artists, album, and duration.

Use this to find songs before adding them to playlists.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'Manuel Göttsching E2-E4', 'Neu! Hallogallo')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (1-100)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "filter": {
                        "type": "string",
                        "description": "Filter results by type",
                        "enum": ["songs", "videos", "albums", "artists", "playlists"],
                        "default": "songs",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="create_youtube_music_playlist",
            description="""
Create a new playlist on YouTube Music. Can optionally add tracks immediately.
Returns the playlist ID and URL.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Playlist title",
                    },
                    "description": {
                        "type": "string",
                        "description": "Playlist description",
                        "default": "",
                    },
                    "privacy_status": {
                        "type": "string",
                        "description": "Playlist visibility",
                        "enum": ["PRIVATE", "PUBLIC", "UNLISTED"],
                        "default": "PRIVATE",
                    },
                    "video_ids": {
                        "type": "array",
                        "description": "Optional list of video IDs to add to playlist on creation",
                        "items": {"type": "string"},
                        "default": [],
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="add_tracks_to_playlist",
            description="""
Add tracks to an existing YouTube Music playlist using video IDs.
Get video IDs using the search_youtube_music tool first.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Target playlist ID",
                    },
                    "video_ids": {
                        "type": "array",
                        "description": "List of video IDs to add",
                        "items": {"type": "string"},
                    },
                },
                "required": ["playlist_id", "video_ids"],
            },
        ),
        Tool(
            name="search_and_add_to_playlist",
            description="""
Convenience tool that searches for tracks and adds the top result of each
to a playlist in one operation. Useful for quickly building playlists from
a list of song names.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Target playlist ID",
                    },
                    "search_queries": {
                        "type": "array",
                        "description": "List of search queries (e.g., ['Artist - Song', 'Another Song'])",
                        "items": {"type": "string"},
                    },
                },
                "required": ["playlist_id", "search_queries"],
            },
        ),
        Tool(
            name="get_playlist_details",
            description="""
Retrieve details about a YouTube Music playlist including all tracks.
Returns all tracks by default (no limit).
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {
                        "type": "string",
                        "description": "Playlist ID to retrieve",
                    },
                },
                "required": ["playlist_id"],
            },
        ),
        Tool(
            name="get_library_playlists",
            description="""
Get the user's library playlists from YouTube Music.
Returns a list of playlists with their IDs and titles.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of playlists to return",
                        "default": 25,
                        "minimum": 1,
                    },
                },
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """
    Handle tool calls from the MCP client.
    """
    try:
        if name == "search_youtube_music":
            results = await ytmusic_client.search_tracks(
                query=arguments["query"],
                limit=arguments.get("limit", 20),
                filter=arguments.get("filter", "songs"),
            )

            if not results:
                return [TextContent(type="text", text="No results found.")]

            output_lines = [f"Found {len(results)} results:\n"]
            for r in results:
                artists = ", ".join([a["name"] for a in r["artists"]]) if r["artists"] else "Unknown Artist"
                album_info = f" [{r['album']}]" if r.get("album") else ""
                duration_info = f" ({r['duration']})" if r.get("duration") else ""
                output_lines.append(
                    f"- {r['title']} - {artists}{album_info}{duration_info}\n"
                    f"  videoId: {r['videoId']}"
                )

            return [TextContent(type="text", text="\n".join(output_lines))]

        elif name == "create_youtube_music_playlist":
            result = await ytmusic_client.create_playlist(
                title=arguments["title"],
                description=arguments.get("description", ""),
                privacy_status=arguments.get("privacy_status", "PRIVATE"),
                video_ids=arguments.get("video_ids", []),
            )
            return [
                TextContent(
                    type="text",
                    text=f"Created playlist: {result['title']}\n"
                    f"Playlist ID: {result['playlistId']}\n"
                    f"URL: {result['url']}",
                )
            ]

        elif name == "add_tracks_to_playlist":
            result = await ytmusic_client.add_playlist_items(
                playlist_id=arguments["playlist_id"],
                video_ids=arguments["video_ids"],
            )
            return [
                TextContent(
                    type="text",
                    text=f"Successfully added {result['addedCount']} tracks to playlist {result['playlistId']}",
                )
            ]

        elif name == "search_and_add_to_playlist":
            result = await ytmusic_client.search_and_add_to_playlist(
                playlist_id=arguments["playlist_id"],
                search_queries=arguments["search_queries"],
            )

            response_lines = [f"Added {result['addedCount']} tracks to playlist:\n"]
            for track in result["addedTracks"]:
                artists = ", ".join(track.get("artists", []))
                response_lines.append(f"  {track['query']} -> {track['matched']} by {artists}")

            if result["failedQueries"]:
                response_lines.append(f"\nFailed to find: {', '.join(result['failedQueries'])}")

            return [TextContent(type="text", text="\n".join(response_lines))]

        elif name == "get_playlist_details":
            result = await ytmusic_client.get_playlist(
                playlist_id=arguments["playlist_id"],
            )

            output_lines = [
                f"Playlist: {result['title']}",
                f"Description: {result['description'] or 'No description'}",
                f"Track Count: {result['trackCount']}",
                "",
                "Tracks:",
            ]

            for t in result["tracks"]:
                artists = ", ".join([a.get("name", "") for a in t.get("artists", [])])
                output_lines.append(f"  - {t.get('title', 'Unknown')} - {artists}")

            return [TextContent(type="text", text="\n".join(output_lines))]

        elif name == "get_library_playlists":
            result = await ytmusic_client.get_library_playlists(
                limit=arguments.get("limit", 25)
            )

            if not result:
                return [TextContent(type="text", text="No playlists found in your library.")]

            output_lines = [f"Found {len(result)} playlists:\n"]
            for p in result:
                count_info = f" ({p['count']} tracks)" if p.get("count") else ""
                output_lines.append(f"  - {p['title']}{count_info}\n    playlistId: {p['playlistId']}")

            return [TextContent(type="text", text="\n".join(output_lines))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Initialize and run the MCP server"""
    global ytmusic_client

    # Initialize authentication
    logger.info("Initializing YouTube Music authentication...")
    auth_manager = AuthManager()

    if not auth_manager.is_authenticated():
        logger.error("OAuth not configured. Run: python -m src.auth")
        print("Error: OAuth not configured.")
        print("Please run: python -m src.auth")
        return

    try:
        ytmusic = auth_manager.load_auth()
        ytmusic_client = YouTubeMusicClient(ytmusic)
        logger.info("YouTube Music client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        print(f"Error: {e}")
        return

    # Run MCP server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP server running on stdio")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
