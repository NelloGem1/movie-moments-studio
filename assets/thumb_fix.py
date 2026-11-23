"""Replace thumbnails on all trailer-edit uploads with clean text-free frames.
Waits for rebuild passes to finish (checks log markers), then updates thumbs."""
import os, re, sys, time, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
import build_video as b
from youtube_api import get_service
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageEnhance
import subprocess

ASSETS = mp.ASSETS
FF = b.FFMPEG
LOG = os.path.join(ASSETS, "thumb_fix.log")

SPECIAL_SRC = {
    "VL5MdaOdGAU": ["avengers_reveals.mp4"],
    "hVaBvUUvTBw": ["avengers_steve.mp4"],
    "tuEV2msj-7k": ["avengers_thor.mp4"],
    "OvKN_fqIrrk": ["avengers_xmen.mp4"],
    "yAFsro1QUbE": ["avengers_castmix.mp4"],
    "2iqTuvmGb-E": ["dune_final.mp4"],
    "qECve57YJlI": ["dune_guide.mp4"],
    "DNMs5BrHXDM": ["dune_theories.mp4"],
    "bGKYZ2hK-tU": ["dune_recap.mp4"],
    "jvcjFSSVw0A": ["y2008/indiana.mp4"],
}
# note: special vids change after rebuild; match by title instead below.

TITLE_PAT = re.compile(
    r"(Official Trailer Edit|Trailer Edit|Teaser Edit|Epic Edit)")


def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def uploads(svc):
    ch = svc.channels().list(part="contentDetails", mine=True).execute()
    up = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    vids, tok = [], None
    while True:
        r = svc.playlistItems().list(part="contentDetails", playlistId=up,
                                     maxResults=50, pageToken=tok).execute()
        vids += [it["contentDetails"]["videoId"] for it in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            return vids


def find_video_file(title):
    """Locate a local rendered mp4 suitable for a thumbnail frame."""
    cands = []
    ym = re.match(r"^(.*?) \((\d{4})\)", title)
    if ym:
        movie, year = ym.group(1), ym.group(2)
        tag = mp.slug(movie)
        cands += [f"edit_{year}_{tag[:20]}.mp4",
                  f"edit_{year}_{tag[:20]}_base.mp4",
                  f"edit_mv_{tag[:20]}.mp4.mp4"]
        # rebuilt files are named rb_<oldvid>; can't map, but rsp_ for specials
        cands += glob.glob(os.path.join(ASSETS, f"rb_*{tag[:12]}*.mp4"))
    # specials by title keywords
    tl = title.lower()
    if "avengers" in tl or "doomsgay" in tl or "doomsday" in tl:
        cands += ["avengers_reveals.mp4", "avengers_steve.mp4",
                  "avengers_thor.mp4", "avengers_xmen.mp4",
                  "avengers_castmix.mp4"]
    if "dune" in tl:
        cands += ["dune_final.mp4", "dune_guide.mp4", "dune_theories.mp4",
                  "dune_recast.mp4", "dune_recap.mp4", "dune_cast.mp4"]
    if "indiana" in tl:
        cands += ["y2008/indiana.mp4"]
    for c in cands:
        p = c if os.path.isabs(c) else os.path.join(ASSETS, c)
        if os.path.exists(p) and os.path.getsize(p) > 1_000_000:
            return p
    # fuzzy slug search
    words = [w for w in re.findall(r"[a-z0-9]+", title.lower())
             if len(w) > 3][:3]
    if words:
        for f in glob.glob(os.path.join(ASSETS, "*.mp4")):
            base = os.path.basename(f).lower()
            if all(w in base for w in words[:2]):
                return f
    return None


def clean_thumb(video, out):
    d = b.probe_duration(video)
    t = d * 0.62
    frame = os.path.join(ASSETS, "_tf.jpg")
    subprocess.run([FF, "-y", "-ss", f"{t:.1f}", "-i", video,
                    "-frames:v", "1", "-q:v", "2", frame],
                   capture_output=True)
    im = Image.open(frame).convert("RGB")
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = ImageEnhance.Color(im).enhance(1.15)
    im.save(out, "JPEG", quality=92)
    os.remove(frame)


def wait_for_rebuilds():
    while True:
        done = 0
        for lg in ("rebuild.log", "rebuild_special.log"):
            p = os.path.join(ASSETS, lg)
            if os.path.exists(p) and "done ===" in open(p).read():
                done += 1
        # rebuild_special may not have started; also require its log absent-or-done
        sp = os.path.join(ASSETS, "rebuild_special.log")
        started = os.path.exists(sp)
        if done == 2 or (done == 1 and not started):
            # give rebuild_special a grace period if rebuild.log just finished
            if done == 1 and not started:
                time.sleep(300)
                if not os.path.exists(sp):
                    return
                continue
            return
        time.sleep(120)


def main():
    if "--now" not in sys.argv:
        wait_for_rebuilds()
    svc = get_service()
    vids = uploads(svc)
    log("=== thumb fix pass,", len(vids), "uploads ===")
    items = []
    for i in range(0, len(vids), 50):
        det = svc.videos().list(part="snippet",
                                id=",".join(vids[i:i + 50])).execute()
        items += det["items"]
    for it in items:
        title = it["snippet"]["title"]
        vid = it["id"]
        if not TITLE_PAT.search(title):
            continue
        src = find_video_file(title)
        if not src:
            log("NO SRC:", title)
            continue
        thumb = os.path.join(ASSETS, f"clean_thumb_{vid}.jpg")
        try:
            clean_thumb(src, thumb)
            svc.thumbnails().set(videoId=vid, media_body=MediaFileUpload(
                thumb, mimetype="image/jpeg")).execute()
            log("THUMB:", title)
        except Exception as e:
            msg = repr(e)[:150]
            if "quotaExceeded" in msg or "429" in msg or "403" in msg:
                log("RATE LIMITED:", title)
                import youtube_api as _ya
                _ya.use_backup()
                svc = get_service()
            else:
                log("ERR:", title, msg)
        time.sleep(3)
    log("=== thumb fix done ===")


if __name__ == "__main__":
    main()
