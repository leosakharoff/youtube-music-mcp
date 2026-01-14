"""
Tests for YouTube Music client wrapper
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.ytmusic_client import YouTubeMusicClient


@pytest.fixture
def mock_ytmusic():
    """Mock YTMusic instance"""
    mock = Mock()
    return mock


@pytest.fixture
def client(mock_ytmusic):
    """Create client with mocked YTMusic"""
    return YouTubeMusicClient(mock_ytmusic)


@pytest.mark.asyncio
async def test_search_tracks_returns_normalized_results(client, mock_ytmusic):
    """Test that search returns properly normalized results"""
    mock_ytmusic.search.return_value = [
        {
            "videoId": "test123",
            "title": "Test Song",
            "artists": [{"name": "Test Artist", "id": "artist123"}],
            "album": {"name": "Test Album"},
            "duration": "3:45",
            "thumbnails": [{"url": "http://example.com/thumb.jpg"}],
        }
    ]

    results = await client.search_tracks("test query")

    assert len(results) == 1
    assert results[0]["videoId"] == "test123"
    assert results[0]["title"] == "Test Song"
    assert results[0]["artists"][0]["name"] == "Test Artist"
    assert results[0]["album"] == "Test Album"
    assert results[0]["duration"] == "3:45"
    mock_ytmusic.search.assert_called_once_with("test query", filter="songs", limit=20)


@pytest.mark.asyncio
async def test_search_tracks_with_custom_limit_and_filter(client, mock_ytmusic):
    """Test search with custom parameters"""
    mock_ytmusic.search.return_value = []

    await client.search_tracks("query", limit=5, filter="albums")

    mock_ytmusic.search.assert_called_once_with("query", filter="albums", limit=5)


@pytest.mark.asyncio
async def test_search_tracks_handles_missing_fields(client, mock_ytmusic):
    """Test that search handles items with missing optional fields"""
    mock_ytmusic.search.return_value = [
        {
            "videoId": "vid1",
            "title": "Song Without Album",
            "artists": [],
            # No album, duration, or thumbnails
        }
    ]

    results = await client.search_tracks("query")

    assert len(results) == 1
    assert results[0]["album"] is None
    assert results[0]["artists"] == []


@pytest.mark.asyncio
async def test_search_tracks_raises_on_error(client, mock_ytmusic):
    """Test that search raises RuntimeError on API failure"""
    mock_ytmusic.search.side_effect = Exception("API Error")

    with pytest.raises(RuntimeError, match="Search failed"):
        await client.search_tracks("query")


@pytest.mark.asyncio
async def test_create_playlist_success(client, mock_ytmusic):
    """Test successful playlist creation"""
    mock_ytmusic.create_playlist.return_value = "PL_test123"

    result = await client.create_playlist(
        title="Test Playlist", description="Test Description"
    )

    assert result["playlistId"] == "PL_test123"
    assert result["title"] == "Test Playlist"
    assert result["status"] == "created"
    assert "youtube.com" in result["url"]
    assert "PL_test123" in result["url"]


@pytest.mark.asyncio
async def test_create_playlist_with_initial_tracks(client, mock_ytmusic):
    """Test playlist creation with initial video IDs"""
    mock_ytmusic.create_playlist.return_value = "PL_new"

    await client.create_playlist(
        title="My Playlist",
        video_ids=["vid1", "vid2"],
        privacy_status="PUBLIC",
    )

    mock_ytmusic.create_playlist.assert_called_once_with(
        title="My Playlist",
        description="",
        privacy_status="PUBLIC",
        video_ids=["vid1", "vid2"],
    )


@pytest.mark.asyncio
async def test_create_playlist_raises_on_error(client, mock_ytmusic):
    """Test that playlist creation raises RuntimeError on failure"""
    mock_ytmusic.create_playlist.side_effect = Exception("Creation failed")

    with pytest.raises(RuntimeError, match="Failed to create playlist"):
        await client.create_playlist(title="Test")


@pytest.mark.asyncio
async def test_add_playlist_items_success(client, mock_ytmusic):
    """Test adding items to playlist"""
    mock_ytmusic.add_playlist_items.return_value = {"status": "ok"}

    result = await client.add_playlist_items(
        playlist_id="PL_test123", video_ids=["video1", "video2"]
    )

    assert result["status"] == "success"
    assert result["addedCount"] == 2
    assert result["playlistId"] == "PL_test123"


@pytest.mark.asyncio
async def test_add_playlist_items_raises_on_error(client, mock_ytmusic):
    """Test that adding items raises RuntimeError on failure"""
    mock_ytmusic.add_playlist_items.side_effect = Exception("Add failed")

    with pytest.raises(RuntimeError, match="Failed to add tracks"):
        await client.add_playlist_items("PL_test", ["vid1"])


@pytest.mark.asyncio
async def test_get_playlist_success(client, mock_ytmusic):
    """Test getting playlist details"""
    mock_ytmusic.get_playlist.return_value = {
        "title": "My Playlist",
        "description": "A cool playlist",
        "trackCount": 10,
        "tracks": [{"title": "Track 1"}, {"title": "Track 2"}],
    }

    result = await client.get_playlist("PL_test123")

    assert result["id"] == "PL_test123"
    assert result["title"] == "My Playlist"
    assert result["trackCount"] == 10
    assert len(result["tracks"]) == 2


@pytest.mark.asyncio
async def test_get_library_playlists_success(client, mock_ytmusic):
    """Test getting library playlists"""
    mock_ytmusic.get_library_playlists.return_value = [
        {"playlistId": "PL1", "title": "Playlist 1", "count": 5},
        {"playlistId": "PL2", "title": "Playlist 2", "count": 10},
    ]

    result = await client.get_library_playlists()

    assert len(result) == 2
    assert result[0]["playlistId"] == "PL1"
    assert result[1]["title"] == "Playlist 2"


@pytest.mark.asyncio
async def test_search_and_add_to_playlist_success(client, mock_ytmusic):
    """Test the combined search and add operation"""
    # Mock search results
    mock_ytmusic.search.side_effect = [
        [{"videoId": "vid1", "title": "Song 1", "artists": [{"name": "Artist 1", "id": "a1"}]}],
        [{"videoId": "vid2", "title": "Song 2", "artists": [{"name": "Artist 2", "id": "a2"}]}],
    ]
    mock_ytmusic.add_playlist_items.return_value = {"status": "ok"}

    result = await client.search_and_add_to_playlist(
        playlist_id="PL_test", search_queries=["query1", "query2"]
    )

    assert result["status"] == "completed"
    assert result["addedCount"] == 2
    assert len(result["addedTracks"]) == 2
    assert result["failedQueries"] == []


@pytest.mark.asyncio
async def test_search_and_add_handles_failed_searches(client, mock_ytmusic):
    """Test that failed searches are tracked properly"""
    mock_ytmusic.search.side_effect = [
        [{"videoId": "vid1", "title": "Found Song", "artists": []}],
        [],  # No results for second query
    ]
    mock_ytmusic.add_playlist_items.return_value = {"status": "ok"}

    result = await client.search_and_add_to_playlist(
        playlist_id="PL_test", search_queries=["found", "not found"]
    )

    assert result["addedCount"] == 1
    assert len(result["addedTracks"]) == 1
    assert "not found" in result["failedQueries"]
