"""SSD cleanup loop for Movie Moments assets.

- MOVIE_MOMENTS staging files are already deleted by mm_upload.py after
  each successful YouTube upload (runs every 5 min via mm_watch.py).
- This script reclaims space inside assets/:
    * intermediates (_base.mp4, _polished.mp4, _score.wav, concat_mm_*.txt)
      are deleted once the final mm_<slug>.mp4 exists and is >10 min old
      (build finished; intermediates are never reused)
    * final mm_<slug>.mp4 is deleted once its title appears in
      mm_uploaded.txt (video is live; local master no longer needed)
    * *.mp4.mp4 doubled-extension leftovers and _ft.jpg are always junk
Runs every 20 min, forever. Log: mm_cleanup.log
"""
import os, re, sys, time, glob

ASSETS = os.path.dirname(os.path.abspath(__file__))
DONE_UP = os.path.join(ASSETS, "mm_uploaded.txt")
FACTORY = os.path.join(ASSETS, "mm_factory.py")
LOG = os.path.join(ASSETS, "mm_cleanup.log")
STABLE_AGE = 600  # seconds — don't touch files a build may still be writing


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


def slug_titles():
    """slug -> 'Movie (Year) — Christmas Movie Edit' from mm_factory.QUEUE."""
    out = {}
    try:
        src = open(FACTORY, encoding="utf-8").read()
        for m in re.finditer(
                r'\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', src):
            slug, query, movie, year = m.groups()
            out[slug] = f"{movie} ({year}) — Christmas Movie Edit"
    except Exception:
        pass
    return out


def old_enough(path):
    try:
        return time.time() - os.path.getmtime(path) > STABLE_AGE
    except OSError:
        return False


def sweep():
    freed = ndel = 0
    up = uploaded_titles()
    titles = slug_titles()
    slug_up = {s for s, t in titles.items() if t.lower() in up}

    for path in glob.glob(os.path.join(ASSETS, "mm_*")):
        b = os.path.basename(path)
        if not os.path.isfile(path) or not old_enough(path):
            continue
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        # junk patterns: doubled ext, intermediates
        if b.endswith(".mp4.mp4") or b.endswith("_base.mp4") \
                or b.endswith("_polished.mp4") or b.endswith("_score.wav") \
                or b.startswith("concat_mm_"):
            # intermediates only safe once the final exists
            m = re.match(r"mm_(.+?)(?:_base|_polished)?\.mp4", b)
            slug = m.group(1) if m else None
            if slug and not os.path.exists(
                    os.path.join(ASSETS, f"mm_{slug}.mp4")) \
                    and not b.endswith(".mp4.mp4"):
                continue  # build may be mid-flight
            try:
                os.remove(path); freed += size; ndel += 1
            except OSError:
                pass
        else:
            # final mm_<slug>.mp4 — delete only if uploaded
            m = re.match(r"mm_(.+)\.mp4$", b)
            if m and m.group(1) in slug_up:
                try:
                    os.remove(path); freed += size; ndel += 1
                except OSError:
                    pass

    for junk in glob.glob(os.path.join(ASSETS, "*.mp4.mp4")) + \
            [os.path.join(ASSETS, "_ft.jpg")]:
        if os.path.isfile(junk) and old_enough(junk):
            try:
                freed += os.path.getsize(junk)
                os.remove(junk); ndel += 1
            except OSError:
                pass
    return ndel, freed


def main():
    log("=== mm cleanup loop started (every 20 min) ===")
    while True:
        try:
            ndel, freed = sweep()
            if ndel:
                log(f"freed {freed/1e6:.0f} MB across {ndel} files")
        except Exception as e:
            log("ERR:", repr(e)[:200])
        time.sleep(1200)


if __name__ == "__main__":
    main()
