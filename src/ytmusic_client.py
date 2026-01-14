"""
YouTube Music API client using official YouTube Data API v3
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class YouTubeMusicClient:
    """Wrapper around YouTube Data API for music operations"""

    def __init__(self, youtube):
        """
        Initialize with authenticated YouTube API client.

        Args:
            youtube: Authenticated googleapiclient YouTube resource
        """
        self.youtube = youtube

    async def search_tracks(
        self, query: str, limit: int = 20, filter: str = "songs"
    ) -> List[Dict[str, Any]]:
        """
        Search for tracks on YouTube/YouTube Music

        Args:
            query: Search query string
            limit: Maximum number of results (1-50)
            filter: Type of content ("songs", "videos", "playlists")

        Returns:
            List of search results with videoId, title, channel info
        """
        try:
            # Map filter to YouTube API type
            type_map = {
                "songs": "video",
                "videos": "video",
                "playlists": "playlist",
            }
            search_type = type_map.get(filter, "video")

            # For music, add "music" to query if searching for songs
            search_query = query
            if filter == "songs" and "music" not in query.lower():
                search_query = f"{query} music"

            request = self.youtube.search().list(
                part="snippet",
                q=search_query,
                type=search_type,
                maxResults=min(limit, 50),
                videoCategoryId="10" if filter == "songs" else None,  # Music category
            )
            response = request.execute()

            results = []
            for item in response.get("items", []):
                snippet = item.get("snippet", {})

                if search_type == "video":
                    video_id = item.get("id", {}).get("videoId")
                else:
                    video_id = item.get("id", {}).get("playlistId")

                results.append({
                    "videoId": video_id,
                    "title": snippet.get("title"),
                    "artists": [{"name": snippet.get("channelTitle"), "id": snippet.get("channelId")}],
                    "description": snippet.get("description", "")[:200],
                    "thumbnails": snippet.get("thumbnails", {}),
                    "publishedAt": snippet.get("publishedAt"),
                })

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RuntimeError(f"Search failed: {str(e)}")

    async def create_playlist(
        self,
        title: str,
        description: str = "",
        privacy_status: str = "private",
        video_ids: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Create a new playlist

        Args:
            title: Playlist name
            description: Playlist description
            privacy_status: "private", "public", or "unlisted"
            video_ids: Optional list of video IDs to add initially

        Returns:
            Dict with playlistId and status
        """
        try:
            # Create the playlist
            request = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                    },
                    "status": {
                        "privacyStatus": privacy_status.lower(),
                    },
                },
            )
            response = request.execute()
            playlist_id = response["id"]

            # Add initial videos if provided
            if video_ids:
                for video_id in video_ids:
                    await self._add_video_to_playlist(playlist_id, video_id)

            return {
                "playlistId": playlist_id,
                "title": title,
                "status": "created",
                "url": f"https://www.youtube.com/playlist?list={playlist_id}",
            }

        except Exception as e:
            logger.error(f"Playlist creation failed: {e}")
            raise RuntimeError(f"Failed to create playlist: {str(e)}")

    async def _add_video_to_playlist(self, playlist_id: str, video_id: str) -> Dict:
        """Add a single video to a playlist"""
        request = self.youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                },
            },
        )
        return request.execute()

    async def add_playlist_items(
        self, playlist_id: str, video_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Add tracks to an existing playlist

        Args:
            playlist_id: Target playlist ID
            video_ids: List of video IDs to add

        Returns:
            Status information
        """
        try:
            added = 0
            for video_id in video_ids:
                try:
                    await self._add_video_to_playlist(playlist_id, video_id)
                    added += 1
                except Exception as e:
                    logger.warning(f"Failed to add video {video_id}: {e}")

            return {
                "status": "success",
                "playlistId": playlist_id,
                "addedCount": added,
                "requestedCount": len(video_ids),
            }

        except Exception as e:
            logger.error(f"Failed to add items to playlist: {e}")
            raise RuntimeError(f"Failed to add tracks: {str(e)}")

    async def get_playlist(
        self, playlist_id: str, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get playlist details and all tracks (paginated)"""
        try:
            # Get playlist metadata
            playlist_request = self.youtube.playlists().list(
                part="snippet,contentDetails",
                id=playlist_id,
            )
            playlist_response = playlist_request.execute()

            if not playlist_response.get("items"):
                raise RuntimeError(f"Playlist not found: {playlist_id}")

            playlist_info = playlist_response["items"][0]
            snippet = playlist_info.get("snippet", {})
            total_tracks = playlist_info.get("contentDetails", {}).get("itemCount", 0)

            # Get all playlist items with pagination
            tracks = []
            next_page_token = None

            while True:
                items_request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )
                items_response = items_request.execute()

                for item in items_response.get("items", []):
                    item_snippet = item.get("snippet", {})
                    resource_id = item_snippet.get("resourceId", {})
                    tracks.append({
                        "title": item_snippet.get("title"),
                        "videoId": resource_id.get("videoId"),
                        "artists": [{"name": item_snippet.get("videoOwnerChannelTitle", "")}],
                        "position": item_snippet.get("position"),
                    })

                    # Stop if we've reached the limit
                    if limit and len(tracks) >= limit:
                        break

                next_page_token = items_response.get("nextPageToken")
                if not next_page_token or (limit and len(tracks) >= limit):
                    break

            return {
                "id": playlist_id,
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "trackCount": total_tracks,
                "tracks": tracks,
            }

        except Exception as e:
            logger.error(f"Failed to get playlist: {e}")
            raise RuntimeError(f"Failed to retrieve playlist: {str(e)}")

    async def delete_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Delete a playlist"""
        try:
            self.youtube.playlists().delete(id=playlist_id).execute()
            return {"status": "deleted", "playlistId": playlist_id}
        except Exception as e:
            logger.error(f"Failed to delete playlist: {e}")
            raise RuntimeError(f"Failed to delete playlist: {str(e)}")

    async def update_playlist(
        self, playlist_id: str, title: Optional[str] = None, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update playlist title and/or description"""
        try:
            # First get current playlist info
            current = self.youtube.playlists().list(
                part="snippet,status",
                id=playlist_id,
            ).execute()

            if not current.get("items"):
                raise RuntimeError(f"Playlist not found: {playlist_id}")

            playlist = current["items"][0]
            snippet = playlist["snippet"]

            # Update fields if provided
            if title:
                snippet["title"] = title
            if description is not None:
                snippet["description"] = description

            # Send update
            result = self.youtube.playlists().update(
                part="snippet,status",
                body={
                    "id": playlist_id,
                    "snippet": snippet,
                    "status": playlist.get("status", {}),
                },
            ).execute()

            return {
                "status": "updated",
                "playlistId": playlist_id,
                "title": result["snippet"]["title"],
                "description": result["snippet"]["description"],
            }
        except Exception as e:
            logger.error(f"Failed to update playlist: {e}")
            raise RuntimeError(f"Failed to update playlist: {str(e)}")

    async def get_library_playlists(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get user's playlists"""
        try:
            request = self.youtube.playlists().list(
                part="snippet,contentDetails",
                mine=True,
                maxResults=min(limit, 50),
            )
            response = request.execute()

            playlists = []
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                content_details = item.get("contentDetails", {})
                playlists.append({
                    "playlistId": item.get("id"),
                    "title": snippet.get("title"),
                    "description": snippet.get("description", ""),
                    "count": content_details.get("itemCount", 0),
                })

            return playlists

        except Exception as e:
            logger.error(f"Failed to get library playlists: {e}")
            raise RuntimeError(f"Failed to get library playlists: {str(e)}")

    async def search_and_add_to_playlist(
        self, playlist_id: str, search_queries: List[str]
    ) -> Dict[str, Any]:
        """
        Search for tracks and add the top result of each to a playlist.

        Args:
            playlist_id: Target playlist ID
            search_queries: List of search queries

        Returns:
            Status with added tracks info
        """
        video_ids = []
        added_tracks = []
        failed_queries = []

        for query in search_queries:
            try:
                results = await self.search_tracks(query, limit=1, filter="songs")
                if results and results[0].get("videoId"):
                    video_id = results[0]["videoId"]
                    video_ids.append(video_id)
                    added_tracks.append({
                        "query": query,
                        "matched": results[0]["title"],
                        "artists": [a["name"] for a in results[0].get("artists", [])],
                        "videoId": video_id,
                    })
                else:
                    failed_queries.append(query)
            except Exception as e:
                logger.warning(f"Search failed for '{query}': {e}")
                failed_queries.append(query)

        if video_ids:
            await self.add_playlist_items(playlist_id, video_ids)

        return {
            "status": "completed",
            "addedCount": len(video_ids),
            "addedTracks": added_tracks,
            "failedQueries": failed_queries,
        }
