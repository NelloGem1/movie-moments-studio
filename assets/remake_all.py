"""Remake every NELLO_ARCHIVE 'Official Trailer Edit' one by one.
Sequential (CPU-safe alongside mm_par). Tracks progress in remake_done.txt.
Usage: python remake_all.py
"""
import os, re, subprocess, sys, time

ASSETS = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.expanduser(r"~\Downloads\NELLO_ARCHIVE")
DONE = os.path.join(ASSETS, "remake_done.txt")
LOG = os.path.join(ASSETS, "remake_all.log")


def log(*a):
    line = time.strftime("[%Y-%m-%d %H:%M:%S]") + " " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def done_titles():
    if not os.path.exists(DONE):
        return set()
    return set(open(DONE, encoding="utf-8").read().splitlines())


def movies():
    out = []
    for f in sorted(os.listdir(ARCHIVE)):
        m = re.match(r"(.+?) \((\d{4})\) — The Official Trailer Edit\.mp4$", f)
        if m:
            out.append((m.group(1), m.group(2), f))
    return out


def main():
    done = done_titles()
    todo = [(mv, y) for mv, y, f in movies() if f not in done]
    log(f"=== remake_all: {len(todo)} movies to rebuild ===")
    for movie, year in todo:
        log("BUILD:", movie, year)
        r = subprocess.run([sys.executable,
                            os.path.join(ASSETS, "remake_one.py"),
                            movie, year],
                           capture_output=True, text=True, timeout=3600)
        tail = (r.stdout or "")[-400:] + (r.stderr or "")[-400:]
        if r.returncode == 0 and "DONE" in (r.stdout or ""):
            title = f"{movie} ({year}) — The Official Trailer Edit.mp4"
            with open(DONE, "a", encoding="utf-8") as fh:
                fh.write(title + "\n")
            log("OK:", movie, year)
        else:
            log("FAIL:", movie, year, tail.replace("\n", " | ")[:300])
        time.sleep(3)
    log("=== remake_all done ===")


if __name__ == "__main__":
    main()
