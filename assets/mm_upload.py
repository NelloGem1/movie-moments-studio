"""Upload all MOVIE_MOMENTS videos to the Movie Moments Edits channel."""
import os, sys, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from youtube_api import get_service_mm

MM_DIR = os.path.expanduser("~/Downloads/MOVIE_MOMENTS")
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)))
DONE_FILE = os.path.join(ASSETS, "mm_uploaded.txt")

THUMBS = {
    "die hard": "mm_die_hard.jpg",
    "elf": "mm_elf.jpg",
    "home alone": "mm_home_alone.jpg",
    "terrifier": "mm_terrifier3.jpg",
    "red one": "mm_red_one.jpg",
    "violent night": "mm_violent_night.jpg",
}

DESC = (
    "The most unforgettable Christmas movie moments, cut into one cinematic edit.\n\n"
    "Movie Moments Edits — holiday specials, seasonal edits, and the scenes everyone's talking about.\n\n"
    "#MovieMoments #ChristmasMovies #MovieEdit #TrailerEdit"
)

TAGS = ["movie edit", "trailer edit", "christmas movie", "movie moments",
        "film edit", "cinematic edit", "holiday movie"]


def thumb_for(title):
    t = title.lower()
    for key, jpg in THUMBS.items():
        if key in t:
            p = os.path.join(ASSETS, jpg)
            if os.path.exists(p):
                return p
    return None


def upload_one(svc, path, title):
    body = {
        "snippet": {
            "title": title,
            "description": DESC,
            "tags": TAGS,
            "categoryId": "24",  # Entertainment
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(path, chunksize=-1, resumable=True)
    req = svc.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    tp = thumb_for(title)
    if tp:
        try:
            svc.thumbnails().set(videoId=vid,
                                 media_body=MediaIoBaseUpload(open(tp, "rb"), mimetype="image/jpeg")
                                 ).execute()
        except Exception as e:
            print("  thumb fail:", repr(e)[:120])
    return vid


def main():
    import fcntl
    lock_path = os.path.join(ASSETS, "mm_upload.lock")
    lock_f = open(lock_path, "w")
    try:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another uploader is running — exiting", flush=True)
        return
    svc = get_service_mm()
    done = set()
    if os.path.exists(DONE_FILE):
        done = set(open(DONE_FILE, encoding="utf-8").read().splitlines())
    files = sorted(f for f in os.listdir(MM_DIR) if f.lower().endswith(".mp4"))
    print(f"{len(files)} videos in MOVIE_MOMENTS", flush=True)
    for f in files:
        if f in done:
            print("skip (done):", f, flush=True)
            continue
        path = os.path.join(MM_DIR, f)
        title = os.path.splitext(f)[0]
        if time.time() - os.path.getmtime(path) < 90:
            print("skip (still copying):", f, flush=True)
            continue
        try:
            import build_video as _b
            dur = _b.probe_duration(path)
            if dur < 100:
                print(f"SKIP too short ({dur:.0f}s < 100s):", f, flush=True)
                continue
        except Exception:
            pass
        print("uploading:", title, flush=True)
        try:
            vid = upload_one(svc, path, title)
            url = f"https://youtu.be/{vid}"
            with open(DONE_FILE, "a", encoding="utf-8") as fh:
                fh.write(f + "\n")
            print("  OK:", url, flush=True)
            try:
                os.remove(path)
                print("  local copy deleted:", f, flush=True)
            except OSError as e:
                print("  delete fail:", repr(e)[:100], flush=True)
        except Exception as e:
            print("  ERR:", repr(e)[:200], flush=True)
            if "quotaExceeded" in repr(e) or "quota" in repr(e).lower():
                print("API quota exhausted — stopping until tomorrow", flush=True)
                return
        time.sleep(5)
    print("=== mm upload done ===", flush=True)


if __name__ == "__main__":
    main()
