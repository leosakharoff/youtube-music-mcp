# YouTube Music MCP

MCP server til YouTube Music integration. Søg efter musik og administrer playlists.

## Tools

### search_youtube_music
Søg efter tracks på YouTube Music.
- `query` (required): Søgeord
- `limit`: Max antal resultater (default 5)

Returnerer: videoId, titel, artist, album, duration.

### create_playlist
Opret ny playlist.
- `title` (required): Playlist navn
- `description`: Beskrivelse
- `privacy`: "private", "public", "unlisted" (default "private")

Returnerer: playlistId.

### add_to_playlist
Tilføj video til playlist.
- `playlist_id` (required): Playlist ID
- `video_id` (required): Video/track ID

### get_my_playlists
Hent brugerens playlists.
- `max_results`: Max antal (default 25)

### get_playlist_details
Hent alle tracks fra en playlist.
- `playlist_id` (required): Playlist ID

### search_and_add
Søg og tilføj tracks til playlist (batch operation).
- `playlist_id` (required): Playlist ID
- `queries` (required): Liste af søgeord

### update_playlist
Opdater playlist metadata.
- `playlist_id` (required)
- `title`: Nyt navn
- `description`: Ny beskrivelse

### delete_playlist
Slet en playlist (kan ikke fortrydes).
- `playlist_id` (required)

## Eksempler

```
# Søg efter track
search_youtube_music(query="Kraftwerk Autobahn")

# Opret playlist
create_playlist(title="Krautrock Classics", privacy="private")

# Tilføj flere tracks
search_and_add(playlist_id="PLxxx", queries=["Neu! Hallogallo", "Can Vitamin C", "Tangerine Dream Phaedra"])

# Se playlists
get_my_playlists()
```

## Authentication

Kræver Google OAuth med YouTube Data API v3 scope.
