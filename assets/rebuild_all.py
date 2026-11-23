"""Rebuild every published 'Official Trailer Edit' video with the clean-cut
standard (hard cuts, no audio fades, whisper phrase boundaries, outro tail,
fade-to-black ending). Replaces the old upload, then deletes it."""
import os, re, sys, time, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
import build_video as b
import make_edit as m
import polish as p
from youtube_api import get_service

ASSETS = mp.ASSETS
YT = mp.YT_DIR
LOG = os.path.join(ASSETS, "rebuild.log")
DONE_FILE = os.path.join(ASSETS, "rebuild_done.txt")
QUOTA_STOP = os.path.join(ASSETS, "QUOTA_STOP")
SKIP = {"inside_out_2", "sinners", "the_dark_knight"}  # already handled
REVIEW_DIR = os.path.expanduser(r"~\Downloads\REVIEW_ALL")
DOWNLOADS = os.path.expanduser(r"~\Downloads")


def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def channel_uploads(svc):
    ch = svc.channels().list(part="contentDetails", mine=True).execute()
    up = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    vids, tok = [], None
    while True:
        r = svc.playlistItems().list(part="contentDetails", playlistId=up,
                                     maxResults=50, pageToken=tok).execute()
        for it in r["items"]:
            vids.append(it["contentDetails"]["videoId"])
        tok = r.get("nextPageToken")
        if not tok:
            return vids


def video_title(svc, vid):
    r = svc.videos().list(part="snippet", id=vid).execute()
    return r["items"][0]["snippet"]["title"] if r["items"] else ""


Y08_ALIASES = {
    "the_incredible_hulk": "hulk", "iron_man": "im",
    "indiana_jones_and_the_kingdom_of_the_crystal_skull": "indiana",
    "kung_fu_panda": "kungfu", "mamma_mia!": "mamma_mia", "mamma_mia": "mamma_mia",
    "wall-e": "walle", "wall_e": "walle", "slumdog_millionaire": "slumdog",
    "the_dark_knight": "tdk",
}
Y08_DIR = os.path.join(ASSETS, "y2008")


def find_trailer(movie, year):
    tag = mp.slug(movie)
    cands = [tag + ".mp4", tag + "_" + str(year) + ".mp4",
             mp.slug(movie + " " + str(year)) + ".mp4"]
    for c in cands:
        p = os.path.join(YT, c)
        if os.path.exists(p) and os.path.getsize(p) > 500_000:
            return p
    # fuzzy: slug prefix match
    pref = tag[:18]
    for f in os.listdir(YT):
        if f.endswith(".mp4") and f.startswith(pref):
            return os.path.join(YT, f)
    # 2008 batch lives in y2008/ under short aliases; prefer *_hd sources
    alias = Y08_ALIASES.get(tag) or Y08_ALIASES.get(tag.replace("!", ""))
    if alias and os.path.isdir(Y08_DIR):
        hd = os.path.join(Y08_DIR, alias + "_hd.mp4")
        if os.path.exists(hd) and os.path.getsize(hd) > 500_000:
            return hd
        p = os.path.join(Y08_DIR, alias + ".mp4")
        if os.path.exists(p) and os.path.getsize(p) > 500_000:
            return p
    return None


def rebuild(vid, movie, year, orig_title=None):
    trailer = find_trailer(movie, year)
    if not trailer:
        log("NO TRAILER:", movie, year); return False
    rel = os.path.relpath(trailer, ASSETS).replace(os.sep, "/")
    hh = b.probe_height(trailer) if hasattr(b, "probe_height") else 0
    if hh and hh < 1080:
        log("LOW-RES SOURCE:", movie, year, hh, "p —", trailer)
    key = f"rb_{vid}"
    try:
        clips, tail = mp.speech_cuts(rel, max_clips=28, return_tail=True, dmax=8)
        if not clips:
            wins = m.energy_windows(rel, count=18, win=3.8, min_gap=5.5,
                                    seed=hash(movie) % 5000)
            clips = [(round(t, 2), round(d, 2)) for t, d in wins]
            tail = None
        if tail:
            T = b.probe_duration(trailer)
            clips = clips + [(tail, round(T - tail, 2))]
        seg = b.build_clean_montage("rb_" + vid, rel, clips,
                                    target_name=f"rb_{vid}.mp4")
        mp._finish_single(key, [seg])
        out = os.path.join(ASSETS, key + ".mp4")
        polished = p.polish(out)
        os.replace(polished, out)
        thumb = os.path.join(ASSETS, f"rb_thumb_{vid}.jpg")
        mp.make_thumb(out, movie, f"{year} Official Trailer Edit", thumb)
        title = orig_title or f"{movie} ({year}) — The Official Trailer Edit"
        for d in (REVIEW_DIR, DOWNLOADS):
            tgt = os.path.join(d, title + ".mp4")
            if os.path.exists(tgt):
                import shutil
                shutil.copy(out, tgt)
                log("local copy updated:", tgt)
        desc = (f"{movie} ({year}) — the most intense moments from the official "
                f"trailer, cut into one cinematic edit with original audio. "
                f"No narration, just the movie.")
        tags = [movie.lower(), str(year), "trailer edit", "official trailer",
                "movie edit", "cinematic edit"]
        desc += "\n\n" + " ".join(["#MovieEdit", "#TrailerEdit",
                                   f"#{mp.slug(movie).replace('_', '')}",
                                   f"#{year}"])
        new_vid = mp.upload(out, thumb, title, desc, tags)
        get_service().videos().delete(id=vid).execute()
        with open(DONE_FILE, "a") as f:
            f.write(new_vid + "\n")
        log("REBUILT:", title, "->", "https://youtu.be/" + new_vid)
        return True
    except Exception as e:
        log("ERR:", movie, year, repr(e)[:200])
        s = str(e)
        if "exceeded the number of videos" in s:
            open(QUOTA_STOP, "w").write("quota")
            log("UPLOAD CAP — stopping pass")
            return "quota"
        if "quotaExceeded" in s or "exceeded your" in s:
            import youtube_api as _ya
            _ya.use_backup()
            log("API quota hit — switched to backup project")
        return False


def done_ids():
    ids = set()
    if os.path.exists(DONE_FILE):
        ids.update(open(DONE_FILE).read().split())
    if os.path.exists(LOG):
        for m in re.finditer(r"youtu\.be/([\w-]+)", open(LOG).read()):
            ids.add(m.group(1))
    return ids


def _main_inner():
    svc = get_service()
    done = done_ids()
    vids = [v for v in channel_uploads(svc) if v not in done]
    log("=== rebuild pass,", len(vids), "uploads ===")
    pat = re.compile(r"^(.*?) \((\d{4})\)\s*—\s*(?:The Official\s+)?Trailer Edit")
    for vid in vids:
        svc = get_service()
        title = video_title(svc, vid)
        m = pat.match(title)
        if not m:
            continue
        movie, year = m.group(1), int(m.group(2))
        if mp.slug(movie) in SKIP:
            log("skip (already clean):", title)
            continue
        if rebuild(vid, movie, year, orig_title=title) == "quota":
            break
        time.sleep(2)
    else:
        log("=== rebuild pass done ===")


def main():
    try:
        _main_inner()
    except Exception as e:
        s = str(e)
        if "quotaExceeded" in s or "exceeded your" in s:
            import youtube_api as _ya
            _ya.use_backup()
            log("API quota hit — switched to backup project, retrying")
            main()
        else:
            raise


if __name__ == "__main__":
    main()
