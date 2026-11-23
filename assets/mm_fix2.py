"""Fix pass 2: rebuild videos still under 110s with bigger clip windows."""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
import build_video as b
import make_edit as m
import polish as p

ASSETS = mp.ASSETS
TDL = os.path.join(ASSETS, "trailers_dl")
OUT_DIR = os.path.expanduser(r"~\Downloads\MOVIE_MOMENTS")

JOBS = [
    ("love_act", "Love Actually",        "2003", "mm_love_act.mp4",  30, 8.5),
    ("nbc",      "The Nightmare Before Christmas", "1993", "mm_nbc.mp4", 30, 8.5),
]


def log(*a):
    print(" ".join(str(x) for x in a), flush=True)


def build(slug, movie, year, srcf, maxc, dmax):
    src = os.path.join(TDL, srcf)
    if not os.path.exists(src):
        log("ERR missing trailer:", srcf); return
    rel = os.path.relpath(src, ASSETS).replace(os.sep, "/")
    clips, tail = mp.speech_cuts(rel, max_clips=maxc, return_tail=True, dmax=dmax)
    if not clips:
        wins = m.energy_windows(rel, count=26, win=5.0, min_gap=4.0,
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
    dur = b.probe_duration(out)
    mp.make_thumb(out, movie, f"{year} Trailer Edit",
                  os.path.join(ASSETS, key + ".jpg"))
    title = f"{movie} ({year}) — Christmas Movie Edit.mp4"
    if dur >= 100:
        shutil.copy(out, os.path.join(OUT_DIR, title))
    log(f"OK {movie}: {len(clips)} clips, {dur:.0f}s -> {title}")


if __name__ == "__main__":
    for slug, movie, year, srcf, maxc, dmax in JOBS:
        try:
            build(slug, movie, year, srcf, maxc, dmax)
        except Exception as e:
            log("ERR", slug, repr(e)[:200])
    log("=== mm fix2 done ===")
