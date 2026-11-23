"""Fix pass 6 (overnight): find every Movie Moments build under 105s and
rebuild it with wider energy windows until it clears the 100s upload gate.

Auto-discovers shorts from assets/mm_*.mp4 finals + QUEUE titles.
Deletes stale intermediates FIRST (including the .mp4.mp4 montage cache
that caused earlier fix passes to silently reuse short renders).
Loops up to 3 passes. Log: mm_fix6.log
"""
import os, re, sys, time, glob, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
import build_video as b
import make_edit as m
import polish as p

ASSETS = mp.ASSETS
TDL = os.path.join(ASSETS, "trailers_dl")
OUT_DIR = os.path.expanduser(r"~\Downloads\MOVIE_MOMENTS")
DONE_UP = os.path.join(ASSETS, "mm_uploaded.txt")
FACTORY = os.path.join(ASSETS, "mm_factory.py")
LOG = os.path.join(ASSETS, "mm_fix6.log")
MIN_DUR = 105.0

# slugs not in QUEUE that also need rebuilds
EXTRA = [
    ("bad_santa",  "Bad Santa",       "2003"),
    ("love_act",   "Love Actually",   "2003"),
]


def log(*a):
    line = time.strftime("[%H:%M:%S]") + " " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def uploaded_titles():
    if not os.path.exists(DONE_UP):
        return set()
    return {os.path.splitext(l.strip())[0].lower()
            for l in open(DONE_UP, encoding="utf-8") if l.strip()}


def queue_map():
    out = {}
    src = open(FACTORY, encoding="utf-8").read()
    for mm in re.finditer(
            r'\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', src):
        slug, query, movie, year = mm.groups()
        out[slug] = (movie, year)
    return out


def find_shorts():
    """slug -> (movie, year) for every built final under MIN_DUR that
    isn't uploaded yet."""
    up = uploaded_titles()
    q = queue_map()
    for s, mv, y in EXTRA:
        q.setdefault(s, (mv, y))
    shorts = {}
    for path in glob.glob(os.path.join(ASSETS, "mm_*.mp4")):
        bname = os.path.basename(path)
        if bname.endswith("_base.mp4") or bname.endswith("_polished.mp4"):
            continue
        slug = bname[3:-4]
        if slug not in q:
            continue
        movie, year = q[slug]
        title = f"{movie} ({year}) — Christmas Movie Edit"
        if title.lower() in up:
            continue
        try:
            dur = b.probe_duration(path)
        except Exception:
            continue
        if dur < MIN_DUR:
            shorts[slug] = (movie, year, dur)
    return shorts


def clear_intermediates(slug):
    for f in (f"mm_{slug}.mp4", f"mm_{slug}.mp4.mp4",
              f"mm_{slug}_base.mp4", f"mm_{slug}_polished.mp4",
              f"mm_{slug}_score.wav", f"concat_mm_{slug}.txt"):
        pth = os.path.join(ASSETS, f)
        try:
            if os.path.exists(pth):
                os.remove(pth)
        except OSError:
            pass


def build(slug, movie, year):
    src = os.path.join(TDL, f"mm_{slug}.mp4")
    if not os.path.exists(src):
        log("ERR missing trailer:", slug)
        return False
    rel = os.path.relpath(src, ASSETS).replace(os.sep, "/")
    clear_intermediates(slug)
    # wide windows, tight gaps: 34 x 6.5s can reach ~3min on long trailers
    wins = m.energy_windows(rel, count=34, win=6.5, min_gap=2.5,
                            seed=(abs(hash(slug)) % 5000) + 1)
    clips = [(round(t, 2), round(d, 2)) for t, d in wins]
    if len(clips) < 12:
        log("ERR too few windows:", slug, len(clips))
        return False
    key = f"mm_{slug}"
    seg = b.build_clean_montage(key, rel, clips, target_name=key)
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
        log(f"OK {movie}: {len(clips)} clips, {dur:.0f}s -> staged")
        return True
    log(f"STILL SHORT {movie}: {len(clips)} clips, {dur:.0f}s")
    return False


def main():
    log("=== mm fix6 started ===")
    for pass_no in range(1, 4):
        shorts = find_shorts()
        if not shorts:
            log(f"pass {pass_no}: no shorts — done")
            break
        log(f"pass {pass_no}: {len(shorts)} shorts -> "
            + ", ".join(f"{s}({v[2]:.0f}s)" for s, v in shorts.items()))
        for slug, (movie, year, dur) in shorts.items():
            try:
                build(slug, movie, year)
            except Exception as e:
                log("ERR", slug, repr(e)[:200])
            time.sleep(2)
        time.sleep(10)
    log("=== mm fix6 done ===")


if __name__ == "__main__":
    main()
