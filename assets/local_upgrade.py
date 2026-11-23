"""Local-only upgrade pass: rebuild every REVIEW_ALL trailer edit to the
professional standard (1080p source pref, whisper phrase cuts, clean hard
cuts, polish, gradient thumbnail) and overwrite the file in place.
No YouTube calls. Resume-safe via local_upgrade_done.txt."""
import os, re, sys, time, shutil, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
import build_video as b
import make_edit as m
import polish as p
import rebuild_all as ra

ASSETS = mp.ASSETS
REVIEW = os.path.expanduser(r"~\Downloads\REVIEW_ALL")
DOWNLOADS = os.path.expanduser(r"~\Downloads")
LOG = os.path.join(ASSETS, "local_upgrade.log")
DONE_FILE = os.path.join(ASSETS, "local_upgrade_done.txt")
STATUS = os.path.join(ASSETS, "local_upgrade_status.txt")

# already at the new standard locally
SKIP_TITLES = {
    "Sinners (2025) — The Official Trailer Edit",
    "The Dark Knight (2008) — The Official Trailer Edit",
    "Inside Out 2 (2024) — The Official Trailer Edit",
    # rebuilt + re-uploaded earlier this pass
    "Dune 2021 (2021) — The Official Trailer Edit",
    "Spider-Man No Way Home (2021) — The Official Trailer Edit",
    "Black Panther Wakanda Forever (2022) — The Official Trailer Edit",
    "Jurassic World Dominion (2022) — The Official Trailer Edit",
    "The Batman (2022) — The Official Trailer Edit",
    "Everything Everywhere All at Once (2022) — The Official Trailer Edit",
}

PAT = re.compile(r"^(.*?) \((\d{4})\)\s*—\s*(?:The Official\s+)?Trailer Edit")


def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def done_set():
    if os.path.exists(DONE_FILE):
        return set(open(DONE_FILE, encoding="utf-8").read().splitlines())
    return set()


def upgrade_one(path, title):
    mm = PAT.match(title)
    if not mm:
        return "skip-title"
    movie, year = mm.group(1), int(mm.group(2))
    trailer = ra.find_trailer(movie, year)
    if not trailer:
        return "no-trailer"
    rel = os.path.relpath(trailer, ASSETS).replace(os.sep, "/")
    try:
        hh = b.probe_height(trailer)
    except Exception:
        hh = 0
    clips, tail = mp.speech_cuts(rel, max_clips=28, return_tail=True, dmax=8)
    if not clips:
        wins = m.energy_windows(rel, count=24, win=4.2, min_gap=4.5,
                                seed=abs(hash(movie)) % 5000)
        clips = [(round(t, 2), round(d, 2)) for t, d in wins]
        tail = None
    if tail:
        T = b.probe_duration(trailer)
        clips = clips + [(tail, round(T - tail, 2))]
    key = "lu_" + re.sub(r"\W+", "_", title)[:40]
    seg = b.build_clean_montage(key, rel, clips, target_name=key + ".mp4")
    mp._finish_single(key, [seg])
    out = os.path.join(ASSETS, key + ".mp4")
    polished = p.polish(out)
    os.replace(polished, out)
    thumb = os.path.join(ASSETS, key + ".jpg")
    mp.make_thumb(out, movie, f"{year} Official Trailer Edit", thumb)
    # overwrite review copy + drop a fresh copy in Downloads for judging
    shutil.copy(out, path)
    shutil.copy(out, os.path.join(DOWNLOADS, title + ".mp4"))
    log(f"OK [{hh}p src, {len(clips)} clips] {title} -> {b.probe_duration(out):.0f}s")
    return "ok"


def main():
    files = sorted(f for f in os.listdir(REVIEW) if f.endswith(".mp4"))
    done = done_set()
    total = len(files)
    log(f"=== local upgrade pass: {total} files ===")
    n = 0
    for f in files:
        title = f[:-4]
        if title in SKIP_TITLES or f in done or title in done:
            continue
        path = os.path.join(REVIEW, f)
        n += 1
        try:
            r = upgrade_one(path, title)
        except Exception as e:
            r = "error"
            log("ERR", title, repr(e)[:200])
            traceback.print_exc()
        with open(DONE_FILE, "a", encoding="utf-8") as df:
            df.write(title + "\n")
        with open(STATUS, "w", encoding="utf-8") as sf:
            sf.write(f"{n}/{total - len(SKIP_TITLES)} {r} {title}\n")
        time.sleep(1)
    log("=== local upgrade pass done ===")


if __name__ == "__main__":
    main()
