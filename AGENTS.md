# Movie Moments Production Pipeline — Complete Blueprint

## Quick Start

Run all three in separate terminals:
```bash
cd C:\Users\neilh\youtube-tool\assets
python mm_par.py          # 8 parallel builders
python mm_watch.py        # Auto-upload watcher (every 5 min)
python mm_status_server.py # Live dashboard at http://127.0.0.1:8790/
```

---

## Project Structure

```
C:\Users\neilh\youtube-tool\
├── youtube_api.py           # Google OAuth auth & project switching
├── upload.py                # Generic single-video uploader
├── assets\
│   ├── mm_factory.py        # Production queue (sequential)
│   ├── mm_par.py            # Parallel factory (8 workers)
│   ├── mm_watch.py          # Folder watcher, auto-upload every 5 min
│   ├── mm_upload.py         # Batch uploader with duration guard
│   ├── mm_status_server.py  # Live dashboard
│   ├── build_video.py       # Core rendering (build_clean_montage)
│   ├── movie_pipeline.py    # Concat, score, final mix
│   ├── polish.py            # Cinematic grading
│   ├── make_edit.py         # Energy-window selection
│   └── trailers_dl\         # Source trailers (KEEP THIS)
C:\Users\neilh\Downloads\
├── MOVIE_MOMENTS\           # Staging folder for auto-upload
└── NELLO_ARCHIVE\           # Nello Gem backup (safe zone)
```

---

## Technology Stack

- Python 3.12
- FFmpeg 9.1 with Intel Quick Sync (`h264_qsv`)
- yt-dlp for trailer downloads
- Whisper (`ggml-tiny.en.bin`) for phrase-boundary transcription
- Google Cloud (3 projects with YouTube Data API v3)
- OAuth 2.0 desktop application flow

---

## OAuth Setup (3 Projects)

| Project | Credential Files | Channel | Status |
|---|---|---|---|
| Project 1 | `client_secret.json` + `token.json` | Nello Gem | Quota exhausted |
| Project 2 | `client_secret2.json` + `token2.json` | Nello Gem (backup) | Quota exhausted |
| Project 3 | `client_secret3.json` + `token3.json` | Movie Moments Edits | Active |

**Movie Moments channel:**
- Handle: `@MovieMomentsEdits-c`
- Channel ID: `UCmqEKpMeGmnE_27-a7MxuXQ`

**To recreate OAuth (if tokens lost):**
1. console.cloud.google.com → New Project
2. APIs & Services → Library → enable "YouTube Data API v3"
3. APIs & Services → OAuth consent screen → External → fill app name → Save
4. Credentials → Create OAuth client ID → Desktop app → Download JSON as `client_secret*.json`
5. Add test user email to OAuth consent screen (or publish app to production)
6. Run OAuth flow via `youtube_api.py` to generate `token*.json`

---

## Production Pipeline

```
1. Download trailer → assets/trailers_dl/ (via yt-dlp in mm_factory.py)
2. Speech detection:
   - Dialogue-rich → speech_cuts (30 clips, 8.5s max, phrase boundaries via Whisper)
   - Dialogue-poor → energy_windows (26 clips, 5s, visual/energy peaks)
3. Render → build_clean_montage (hard cuts, no fades, full audio volume)
4. Grade → polish.py (teal/orange, vignette, grain, sharpen)
5. Thumbnail → gradient/cinematic style
6. Duration check → MUST be ≥100s (1:40 minimum)
7. Copy to MOVIE_MOMENTS\ (only if duration passes)
8. Watcher (mm_watch.py) detects file → uploads to YouTube (public)
9. Delete local MP4 after upload confirmation
```

---

## Key Configurations

**Duration guard (1:40 minimum):**
- `mm_upload.py` line 97: `if dur < 100:`
- `mm_replace_short.py` line 30: `if dur < 100:`

**Encoder (Intel Quick Sync):**
- `build_video.py`: `-c:v h264_qsv -preset veryfast -global_quality 20`
- Much faster and cooler than CPU `libx264`

**Grading (polish.py):**
```
eq=contrast=1.08:saturation=1.18:brightness=-0.01
colorbalance=rs=-0.04:gs=-0.02:bs=0.06:rm=0.05:gm=0.01:bm=-0.05
curves=master='0/0.02 0.5/0.52 1/0.97'
vignette=PI/5:mode=forward
noise=alls=4:allf=t+u
unsharp=5:5:0.4:5:5:0.0
```

**Parallel workers:**
- `mm_par.py` line 11: `WORKERS = 8` — max practical limit for CPU

---

## Critical Gotchas

1. **Build cache** — `build_clean_montage` skips if output exists ("already rendered"). For true rebuilds, delete all intermediates:
   - `mm_{slug}.mp4`
   - `mm_{slug}_base.mp4`
   - `mm_{slug}_polished.mp4`
   - `mm_{slug}_score.wav`
   - `concat_mm_{slug}.txt`

2. **File locks** — FFmpeg holds files during encoding. Delete operations fail while encoding. Wait for ffmpeg to finish or kill the process.

3. **Duplicate uploads** — `mm_upload.lock` prevents race conditions. If stuck, delete the lock file.

4. **API quota** — Each project gets ~10,000 units/day (~6 uploads). When exhausted, uploads pause; builds continue automatically.

5. **Unicode errors** — Windows console cp1252 can't print Unicode chars. Avoid emojis in print statements or force UTF-8.

6. **Short videos** — Dialogue-poor trailers can't always reach 100s via phrase cuts. The energy-window fallback fixes this. If still under 100s, skip and move to next movie.

---

## Channels

**Nello Gem:**
- Old trailer edits (2008-2026)
- Archived to `NELLO_ARCHIVE\` (69 videos safe locally)
- User may delete some short videos from YouTube

**Movie Moments Edits:**
- Seasonal/holiday movie edits
- Automatic public publishing via mm_upload.py
- Duration guard: 1:40 minimum (100s)
- Preferred range: 1:50–3:00

---

## Recovery from Scratch

If the entire `youtube-tool` folder is lost:

1. **Reinstall dependencies:**
   - Python 3.12
   - FFmpeg 9.1 (with QSV support)
   - yt-dlp
   - `google-auth`, `google-auth-oauthlib`, `google-api-python-client`

2. **Recreate folder structure** (see "Project Structure" above)

3. **Restore OAuth credentials:**
   - Keep `client_secret*.json` files safe (project-specific, can't be regenerated)
   - Re-run OAuth flows to regenerate `token*.json` files

4. **Copy scripts from git or backup** (all logic is in `.py` files)

5. **Keep `trailers_dl\`** — it's 3.1GB of source trailers, expensive to re-download

6. **Verify pipeline** — run `mm_par.py` + `mm_watch.py` + `mm_status_server.py`

---

## Live Dashboard

URL: http://127.0.0.1:8790/
- Auto-refreshes every 10s
- Shows: pending files, durations, published feed, process count
- Color-coded status: READY (green), under-length (amber), QUEUED (dim)

---

## Factory Queue

Located in `mm_factory.py` starting at line 18. Each entry:
```python
("slug", "search query", "Movie Name", "Year")
```

Factory skips movies already in `mm_uploaded.txt` or existing in `MOVIE_MOMENTS\`.

---

## Duration Policy Evolution

- Originally: 2-3 min preferred
- Current minimum: 100s (1:40) — anything under rejected
- Reason: 1:00-1:15 edits "unacceptable" per user
- Energy-window fallback ensures dialogue-poor trailers can reach the minimum

---

## CPU Stability History

User experienced shutdowns during heavy CPU encoding:
- Switched from `libx264` to `h264_qsv` (Intel Quick Sync)
- Reduced CPU maximum processor state to 99% (disables turbo boost)
- Installed LibreHardwareMonitor for temp tracking
- Result: stable since

---

## Backup and Cleanup

To reclaim space:
- Delete `mm_*_base.mp4`, `mm_*_polished.mp4`, `mm_*_score.wav`, `concat_mm_*.txt` after final renders
- Keep `trailers_dl\` — source files
- Keep `client_secret*.json` — OAuth credentials
- Archive completed uploads locally before deleting from YouTube
- **MOVIE MOMENTS IS LOCKED** — never delete `mm_*` files, `MOVIE_MOMENTS\` staging, `mm_uploaded.txt`, or `mm_*.py` scripts without explicit user approval

---

## Approved Shorts Caption Style — KINETIC TYPOGRAPHY (rated 10/10)

Script: `assets/make_progressive_caption.py` — tested on Everything Everywhere All At Once, approved by user.

**Specs:**
- Font: **Anton** (bold blocky sans-serif), ALL CAPS, 72pt
- Letter spacing: wide (+2) for cinematic feel
- Position: center / slightly below center (MarginV ~180)
- Phrase length: 1–3 words, broken at punctuation/pauses (phrase-by-phrase, dynamic replacement)
- Animation: quick 30ms fade + pop-in scale 105–110% → 100%, ease-out
- Timing: Whisper **word-level** timestamps, synced to speech, never reveal before spoken
- Emotion-based colors (not random):
  - Red = emphasis/intensity (!, ?, short punchy)
  - Yellow = attention/key info (long phrases)
  - Blue = contrast/explanatory
  - Green = questions/variation
  - Purple = statements/distinction
- Each style has matching colored glow/outline + subtle black shadow
- Optional top hook header for first ~5s (e.g. "POV: ..." with eye icon)

**Rules:**
- Never show full sentence before it's spoken (user rejected this twice)
- No blanket time offsets — use word-level timing
- Test on dialogue-heavy clips (two characters talking) before batch production
