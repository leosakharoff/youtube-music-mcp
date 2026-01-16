# YouTube Music MCP - Endpoints Reference

**Server URL:** `https://youtube-music-mcp.onrender.com/sse`

## ⚠️ QUOTA WARNING

YouTube Data API har **BEGRÆNSET quota**.

**REGLER:**
- Brug KUN til at gemme playlist EFTER research er færdig
- Aldrig mere end 25-30 tracks per session
- Brug `search_and_add` til batch - IKKE enkelte søgninger
- Hvis quota fejl: giv brugeren track-liste til manuel tilføjelse

---

## Endpoints

### search_youtube_music
Søg efter tracks.

| Argument | Type | Required | Default | Beskrivelse |
|----------|------|----------|---------|-------------|
| `query` | string | ✅ | - | Søgeord (f.eks. "Kraftwerk Autobahn") |
| `limit` | integer | ❌ | 20 | Max resultater (1-50) |
| `filter` | string | ❌ | "songs" | Filter: `songs`, `videos`, `albums`, `artists`, `playlists` |

```json
{
  "query": "Neu! Hallogallo",
  "limit": 5,
  "filter": "songs"
}
```

**Returnerer:** videoId, title, artist, album, duration.

---

### create_playlist
Opret ny playlist.

| Argument | Type | Required | Default | Beskrivelse |
|----------|------|----------|---------|-------------|
| `title` | string | ✅ | - | Playlist navn |
| `description` | string | ❌ | "" | Beskrivelse |
| `privacy_status` | string | ❌ | "private" | `private`, `public`, `unlisted` |
| `video_ids` | array | ❌ | [] | Video IDs at tilføje ved oprettelse |

```json
{
  "title": "Berlin-Tokyo Kosmische 1978-1984",
  "description": "Krautrock til japansk ambient",
  "privacy_status": "private",
  "video_ids": ["dQw4w9WgXcQ", "abc123"]
}
```

**Returnerer:** playlistId

---

### add_to_playlist
Tilføj videoer til playlist.

| Argument | Type | Required | Default | Beskrivelse |
|----------|------|----------|---------|-------------|
| `playlist_id` | string | ✅ | - | Target playlist ID |
| `video_ids` | array | ✅ | - | Liste af video IDs |

```json
{
  "playlist_id": "PLxxxxxxx",
  "video_ids": ["dQw4w9WgXcQ", "abc123"]
}
```

**⚠️ Kræver at du allerede har videoId'er. Brug `search_and_add` i stedet!**

---

### search_and_add ⭐ ANBEFALET
Søg og tilføj flere tracks på én gang.

| Argument | Type | Required | Default | Beskrivelse |
|----------|------|----------|---------|-------------|
| `playlist_id` | string | ✅ | - | Target playlist ID |
| `queries` | array | ✅ | - | Liste af søgestrenge |

```json
{
  "playlist_id": "PLxxxxxxx",
  "queries": [
    "Neu! Hallogallo",
    "Cluster Zuckerzeit",
    "Harmonia Deluxe",
    "Michael Rother Flammende Herzen"
  ]
}
```

**PRIMÆR METODE! Saml alle tracks først, tilføj samlet.**

---

### get_my_playlists
List brugerens playlists.

| Argument | Type | Required | Default | Beskrivelse |
|----------|------|----------|---------|-------------|
| `limit` | integer | ❌ | 25 | Max antal playlists |

```json
{
  "limit": 50
}
```

---

### get_playlist_details
Hent alle tracks fra playlist.

| Argument | Type | Required | Default | Beskrivelse |
|----------|------|----------|---------|-------------|
| `playlist_id` | string | ✅ | - | Playlist ID |

```json
{
  "playlist_id": "PLxxxxxxx"
}
```

---

### update_playlist
Opdater playlist metadata.

| Argument | Type | Required | Default | Beskrivelse |
|----------|------|----------|---------|-------------|
| `playlist_id` | string | ✅ | - | Playlist ID |
| `title` | string | ❌ | - | Nyt navn |
| `description` | string | ❌ | - | Ny beskrivelse |

```json
{
  "playlist_id": "PLxxxxxxx",
  "title": "Nyt navn",
  "description": "Ny beskrivelse"
}
```

---

### delete_playlist
Slet playlist (PERMANENT).

| Argument | Type | Required | Default | Beskrivelse |
|----------|------|----------|---------|-------------|
| `playlist_id` | string | ✅ | - | Playlist ID |

```json
{
  "playlist_id": "PLxxxxxxx"
}
```

**⚠️ Kan IKKE fortrydes!**

---

## Workflow

### RIGTIGT ✅
```
1. Research færdig med Discogs + Bandcamp
2. Liste med 15-20 tracks klar
3. create_playlist(title="Beskrivende navn")
4. search_and_add(playlist_id, queries=[alle tracks])
5. Færdig!
```

### FORKERT ❌
```
1. search_youtube_music("track 1")
2. add_to_playlist(video_id)
3. search_youtube_music("track 2")
4. add_to_playlist(video_id)
... (quota opbrugt efter 10 tracks)
```

---

## Præcise Søgninger

For bedste match:
```
"Artist - Track Title"
"Kraftwerk Autobahn"
"Neu! Hallogallo"
```

Undgå:
```
"that one song about driving"
"electronic music"
```

---

## Quota Fejlhåndtering

Hvis du får quota-fejl:

1. Stop YouTube API kald
2. Giv brugeren track-liste:
   ```
   Kunne ikke tilføje alle tracks (quota limit).
   Her er resten til manuel tilføjelse:

   - Artist 1 - Track 1
   - Artist 2 - Track 2
   ```
3. Foreslå at prøve igen senere
