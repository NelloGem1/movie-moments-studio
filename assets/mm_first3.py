"""Build first 3 Movie Moments Edits: Home Alone, Elf, Die Hard.
Downloads official trailers, builds professional edits, drops in Downloads."""
import os, re, subprocess, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
import build_video as b
import make_edit as m
import polish as p

ASSETS = mp.ASSETS
TDL = os.path.join(ASSETS, "trailers_dl")
OUT_DIR = os.path.expanduser(r"~\Downloads\MOVIE_MOMENTS")
os.makedirs(OUT_DIR, exist_ok=True)

JOBS = [
    ("home_alone", "Home Alone 1990 official trailer", "Home Alone", "1990"),
    ("elf",        "Elf 2003 official trailer",        "Elf",        "2003"),
    ("die_hard",   "Die Hard 1988 official trailer",   "Die Hard",   "1988"),
]


def log(*a):
    print(" ".join(str(x) for x in a), flush=True)


def fetch_trailer(slug, query):
    dst = os.path.join(TDL, f"mm_{slug}.mp4")
    if os.path.exists(dst) and os.path.getsize(dst) > 1_000_000:
        return dst
    # pick best 1080p upload from top search results
    r = subprocess.run(["yt-dlp", "--no-playlist", "--flat-playlist",
                        "--print", "%(id)s", f"ytsearch5:{query}"],
                       capture_output=True, text=True, timeout=120)
    ids = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    for vid in ids:
        tmp = dst + ".part.mp4"
        rr = subprocess.run(["yt-dlp", "--no-playlist",
                             "-f", "bv*[height>=720]+ba/b[height>=720]/b",
                             "--merge-output-format", "mp4",
                             "-o", tmp,
                             f"https://www.youtube.com/watch?v={vid}"],
                            capture_output=True, text=True, timeout=900)
        if rr.returncode == 0 and os.path.exists(tmp):
            os.replace(tmp, dst)
            log("trailer:", slug, "<-", vid)
            return dst
    raise RuntimeError(f"no trailer for {slug}")


def build(slug, movie, year):
    src = fetch_trailer(slug, dict((s, q) for s, q, _, _ in JOBS)[slug])
    rel = os.path.relpath(src, ASSETS).replace(os.sep, "/")
    clips, tail = mp.speech_cuts(rel, max_clips=26, return_tail=True, dmax=8)
    if not clips:
        wins = m.energy_windows(rel, count=22, win=4.2, min_gap=4.5,
                                seed=abs(hash(slug)) % 5000)
        clips = [(round(t, 2), round(d, 2)) for t, d in wins]
        tail = None
    if tail:
        T = b.probe_duration(src)
        clips = clips + [(tail, round(T - tail, 2))]
    key = f"mm_{slug}"
    seg = b.build_clean_montage(key, rel, clips, target_name=key + ".mp4")
    mp._finish_single(key, [seg])
    out = os.path.join(ASSETS, key + ".mp4")
    polished = p.polish(out)
    os.replace(polished, out)
    mp.make_thumb(out, movie, f"{year} Trailer Edit",
                  os.path.join(ASSETS, key + ".jpg"))
    title = f"{movie} ({year}) — Christmas Movie Edit.mp4"
    shutil.copy(out, os.path.join(OUT_DIR, title))
    log(f"OK {movie}: {len(clips)} clips, {b.probe_duration(out):.0f}s -> {title}")


if __name__ == "__main__":
    for slug, query, movie, year in JOBS:
        try:
            build(slug, movie, year)
        except Exception as e:
            log("ERR", slug, repr(e)[:200])
    log("=== movie moments batch done ===")
