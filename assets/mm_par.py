"""Parallel Movie Moments factory — builds QUEUE items across a worker pool.
Each worker runs the same build_one() pipeline; finished videos are staged in
assets/ and only copied to MOVIE_MOMENTS after passing the 100s duration gate.
"""
import os, sys, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_factory as f

WORKERS = int(os.environ.get("MM_WORKERS", "8"))
FLAG = os.path.join(f.ASSETS, "mm_par_running.flag")


def worker(job):
    slug, query, movie, year = job
    try:
        f.build_one(slug, movie, year, query)
    except Exception as e:
        f.log("ERR", slug, repr(e)[:150])


def pending_jobs():
    done = f.uploaded_titles()
    out = []
    for slug, query, movie, year in f.QUEUE:
        title = f"{movie} ({year}) — Christmas Movie Edit"
        out_file = os.path.join(f.OUT_DIR, title + ".mp4")
        if title.lower() in done or os.path.exists(out_file):
            continue
        out.append((slug, query, movie, year))
    return out


def main():
    open(FLAG, "w").write("par factory active")
    f.log(f"=== parallel factory started ({WORKERS} workers) ===")
    try:
        while True:
            jobs = pending_jobs()
            if not jobs:
                f.log("queue exhausted — sleeping 30 min")
                time.sleep(1800)
                continue
            f.log(f"dispatching {len(jobs)} builds across {WORKERS} workers")
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                list(ex.map(worker, jobs))
            time.sleep(10)
    finally:
        try:
            os.remove(FLAG)
        except OSError:
            pass


if __name__ == "__main__":
    main()
