"""Fix pass 4: rebuild all sub-110s videos using energy_windows (visual peaks)
which guarantees ~2min regardless of dialogue density."""
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
    ("red_one",     "The Red One",     "2024", "mm_red_one.mp4"),
    ("terrifier3",  "Terrifier 3",     "2024", "mm_terrifier3.mp4"),
    ("violent_night","Violent Night", "2022", "mm_violent_night.mp4"),
    ("grinch2018",  "The Grinch",      "2018", "mm_grinch2018.mp4"),
    ("ed_scissor",  "Edward Scissorhands","1990","mm_ed_scissor.mp4"),
    ("love_act",    "Love Actually",   "2003", "mm_love_act.mp4"),
    ("nbc",         "The Nightmare Before Christmas","1993","mm_nbc.mp4"),
    ("bad_santa",   "Bad Santa",       "2003", "mm_bad_santa.mp4"),
    ("batman_ret",  "Batman Returns",  "1992", "mm_batman_ret.mp4"),
    ("jingle_jangle","Jingle Jangle",  "2020", "mm_jingle_jangle.mp4"),
]


def log(*a):
    print(" ".join(str(x) for x in a), flush=True)


def build(slug, movie, year, srcf):
    src = os.path.join(TDL, srcf)
    if not os.path.exists(src):
        log("ERR missing trailer:", srcf); return
    rel = os.path.relpath(src, ASSETS).replace(os.sep, "/")
    # visual-energy selection: ~28 peaks x ~5s = ~2:20, dialogue-safe cuts
    wins = m.energy_windows(rel, count=28, win=5.0, min_gap=4.0,
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
    log("=== mm fix4 done ===")
