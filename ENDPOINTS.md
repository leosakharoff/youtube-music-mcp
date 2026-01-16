# YouTube Music MCP - Endpoints Reference

**Server URL:** `https://youtube-music-mcp.onrender.com/sse`

## ⚠️ QUOTA WARNING

YouTube Data API har **BEGRÆNSET quota**.

**REGLER:**
- Brug KUN til at gemme playlist EFTER research er færdig
- Aldrig mere end 25-30 tracks per session
- Brug `search_and_add` til batch - IKKE enkelte `add_to_playlist`
- Hvis quota fejl: giv brugeren track-liste til manuel tilføjelse

---

## Endpoints

### search_youtube_music
Søg efter tracks.

```json
{
  "query": "Kraftwerk Autobahn",
  "limit": 5
}
```

**Returnerer:** videoId, title, artist, album, duration.

**Brug til:** Find videoId før tilføjelse til playlist. Brug PRÆCISE søgninger.

**Tip:** Søg "Artist - Track" for bedste match.

---

### create_playlist
Opret ny playlist.

```json
{
  "title": "Berlin-Tokyo Kosmische 1978-1984",
  "description": "Krautrock til japansk ambient",
  "privacy": "private|public|unlisted"
}
```

**Returnerer:** playlistId

**Brug til:** Opret ÉN playlist per session. Brug beskrivende navne!

---

### add_to_playlist
Tilføj enkelt video.

```json
{
  "playlist_id": "PLxxxxxxx",
  "video_id": "dQw4w9WgXcQ"
}
```

**⚠️ UNDGÅ!** Brug `search_and_add` i stedet for at spare quota.

---

### search_and_add ⭐ PRIMÆR
Søg og tilføj flere tracks på én gang.

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

**Brug til:** PRIMÆR METODE! Saml alle tracks først, tilføj samlet.

---

### get_my_playlists
List brugerens playlists.

```json
{
  "max_results": 25
}
```

**Brug til:** Find eksisterende playlists, undgå dubletter.

---

### get_playlist_details
Hent tracks fra playlist.

```json
{
  "playlist_id": "PLxxxxxxx"
}
```

**Brug til:** Se hvad der allerede er i en playlist.

---

### update_playlist
Opdater playlist metadata.

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

```json
{
  "playlist_id": "PLxxxxxxx"
}
```

**⚠️ Kan ikke fortrydes!**

---

## Workflow

### RIGTIGT ✅
```
1. Research færdig med Discogs + Bandcamp
2. Liste med 15-20 tracks klar
3. create_playlist(title="Beskrivende navn")
4. search_and_add(queries=[alle tracks])
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

For bedste match, søg:
```
"Artist - Track Title"
"Artist Track Title album:Album Name"
```

Undgå:
```
"that one song about driving" (for vag)
"kraftwerk" (for bred)
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
   ...
   ```
3. Foreslå at prøve igen næste dag

---

## Playlist Navngivning

❌ **Generisk:**
- "Mix"
- "Chill"
- "Electronic"

✅ **Beskrivende:**
- "Conny Plank Production Tree 1974-1982"
- "Fra Düsseldorf til Tokyo: Kosmische"
- "Post-Punk → Ambient Evolution"
- "Label Deep Dive: ECM 1970s"
