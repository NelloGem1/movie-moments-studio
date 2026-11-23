"""Recurring short-video fix loop: every 45 min, find Movie Moments builds
under 105s and rebuild them with wide energy windows (mm_fix6.build).
Skips slugs whose final file is <10 min old (factory may be mid-build).
Runs forever. Log: mm_fixloop.log
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_fix6

ASSETS = mm_fix6.ASSETS
LOG = os.path.join(ASSETS, "mm_fixloop.log")


def log(*a):
    line = time.strftime("[%Y-%m-%d %H:%M:%S]") + " " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fresh_enough(slug):
    p = os.path.join(ASSETS, f"mm_{slug}.mp4")
    try:
        return time.time() - os.path.getmtime(p) < 600
    except OSError:
        return False


def main():
    log("=== mm fixloop started (scan every 45 min) ===")
    while True:
        try:
            shorts = mm_fix6.find_shorts()
            todo = {s: v for s, v in shorts.items() if not fresh_enough(s)}
            if todo:
                log(f"{len(todo)} shorts -> "
                    + ", ".join(f"{s}({v[2]:.0f}s)" for s, v in todo.items()))
                for slug, (movie, year, dur) in todo.items():
                    try:
                        mm_fix6.build(slug, movie, year)
                    except Exception as e:
                        log("ERR", slug, repr(e)[:200])
                    time.sleep(2)
            else:
                log("no shorts")
        except Exception as e:
            log("ERR scan:", repr(e)[:200])
        time.sleep(2700)


if __name__ == "__main__":
    main()
