"""Fix pass 5: rebuild the remaining sub-100s Movie Moments edits
(Bad Santa, Love Actually, Jingle Jangle) with energy_windows selection."""
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
    ("bad_santa",     "Bad Santa",       "2003", "mm_bad_santa.mp4"),
    ("love_act",      "Love Actually",   "2003", "mm_love_act.mp4"),
]


def log(*a):
    print(" ".join(str(x) for x in a), flush=True)


def build(slug, movie, year, srcf):
    src = os.path.join(TDL, srcf)
    if not os.path.exists(src):
        log("ERR missing trailer:", srcf); return
    rel = os.path.relpath(src, ASSETS).replace(os.sep, "/")
    wins = m.energy_windows(rel, count=30, win=6.0, min_gap=3.0,
                            seed=abs(hash(slug)) % 5000)
    clips = [(round(t, 2), round(d, 2)) for t, d in wins]
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
    if dur >= 105:
        shutil.copy(out, os.path.join(OUT_DIR, title))
    log(f"OK {movie}: {len(clips)} clips, {dur:.0f}s -> {title}")


if __name__ == "__main__":
    for slug, movie, year, srcf in JOBS:
        try:
            build(slug, movie, year, srcf)
        except Exception as e:
            log("ERR", slug, repr(e)[:200])
    log("=== mm fix5 done ===")
