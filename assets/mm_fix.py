"""Fix pass: rebuild videos that came out too short or failed."""
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

# (slug, movie, year, src_file, max_clips, dmax)
JOBS = [
    ("red_one",    "The Red One",     "2024", "mm_red_one.mp4",     26, 7.0),
    ("terrifier3", "Terrifier 3",     "2024", "mm_terrifier3.mp4",  26, 7.0),
    ("violent_night","Violent Night","2022","mm_violent_night.mp4",26, 7.0),
    ("ed_scissor", "Edward Scissorhands","1990","mm_ed_scissor.mp4",30, 8.5),
    ("grinch2018", "The Grinch",      "2018", "mm_grinch2018.mp4",  26, 7.0),
]


def log(*a):
    print(" ".join(str(x) for x in a), flush=True)


def build(slug, movie, year, srcf, maxc, dmax):
    src = os.path.join(TDL, srcf)
    if not os.path.exists(src):
        log("ERR missing trailer:", srcf)
        return
    rel = os.path.relpath(src, ASSETS).replace(os.sep, "/")
    clips, tail = mp.speech_cuts(rel, max_clips=maxc, return_tail=True, dmax=dmax)
    if not clips:
        wins = m.energy_windows(rel, count=24, win=4.5, min_gap=4.0,
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
    log("=== mm fix batch done ===")
