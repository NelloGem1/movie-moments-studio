"""Delete duplicate movie edits from the Nello Gem channel once API quota
resets. Keeps one edit per movie (the biggest/compiled version).

Delete list = the 10 videos removed from NELLO_ARCHIVE on 2026-11-23.
Waits for quota (retries every 10 min, up to 26h), then deletes matches.
Log: pending_delete.log
"""
import os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from youtube_api import get_service

ASSETS = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ASSETS, "pending_delete.log")

# titles to delete (normalized match against channel upload titles)
DELETE_TITLES = [
    "Avengers Doomsday (2026) — The Official Trailer Edit",
    "Avengers: Doomsday — Every Character Teaser Edit",
    "Avengers: Doomsday — The Steve Rogers Teaser Edit",
    "Avengers: Doomsday — The Thor Teaser Edit",
    "Avengers: Doomsday — X-Men & Wakanda Teaser Edit",
    "Dune Part Two — The Official Trailer Edit",
    "Dune Part Three (2026) — The Official Trailer Edit",
    "Dune Part Three — The Official Teaser Edit",
    "Dune — Every Teaser in One Epic Edit",
    "Dune — Every Version, One Epic Edit",
]

# sanity: never delete these keepers even if a pattern overlaps
KEEP_TITLES = [
    "Avengers: Doomsday — Every Reveal in One Epic Edit",
    "Dune 2021 (2021) — The Official Trailer Edit",
    "Dune Part Two (2024) — The Official Trailer Edit",
    "Dune Part Three — The Final Trailer Edit",
]


def log(*a):
    line = time.strftime("[%Y-%m-%d %H:%M:%S]") + " " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower().replace("：", ":"))


DEL_NORM = {norm(t): t for t in DELETE_TITLES}
KEEP_NORM = {norm(t) for t in KEEP_TITLES}


def get_svc():
    return get_service()


def channel_uploads(svc):
    ch = svc.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    out, pt = [], None
    while True:
        r = svc.playlistItems().list(part="snippet", playlistId=up,
                                     maxResults=50, pageToken=pt).execute()
        for it in r.get("items", []):
            out.append((it["snippet"]["resourceId"]["videoId"],
                        it["snippet"]["title"]))
        pt = r.get("nextPageToken")
        if not pt:
            return out


def main():
    log("=== pending_delete started — waiting for YouTube quota ===")
    svc = None
    for attempt in range(156):  # ~26h at 10min intervals
        try:
            svc = get_svc()
            channel_uploads(svc)
            break
        except Exception as e:
            if "quota" in repr(e).lower():
                if attempt % 6 == 0:
                    log("quota exhausted, retrying in 10min")
                time.sleep(600)
            else:
                log("ERR auth/api:", repr(e)[:200])
                time.sleep(600)
    else:
        log("gave up after 26h — quota never reset")
        return
    log("quota available — scanning uploads")
    uploads = channel_uploads(svc)
    log(f"{len(uploads)} uploads on channel")
    to_delete = []
    for vid, title in uploads:
        n = norm(title)
        if n in KEEP_NORM:
            log("KEEP  :", title)
            continue
        for dn, orig in DEL_NORM.items():
            if n == dn or n in dn or dn in n:
                to_delete.append((vid, title))
                break
    log(f"{len(to_delete)} videos marked for deletion")
    for vid, title in to_delete:
        try:
            svc.videos().delete(id=vid).execute()
            log("DELETED:", title)
            time.sleep(2)
        except Exception as e:
            log("ERR deleting:", title, repr(e)[:150])
            if "quota" in repr(e).lower():
                log("quota exhausted mid-delete — stopping")
                return
    log("=== pending_delete done ===")


if __name__ == "__main__":
    main()
