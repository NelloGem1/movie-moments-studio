"""Remake ONE 'Official Trailer Edit' locally (no YouTube).
Usage: python remake_one.py "Inside Out 2" 2024 ["Custom Output Title"]
Writes <Movie> (<year>) — The Official Trailer Edit.mp4 into NELLO_ARCHIVE.
Enforces >=105s duration (rebuilds with wider windows if short) so the
final MP4 lands >=200 MB."""
import os, sys, shutil, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
import build_video as b
import make_edit as m
import polish as p
import rebuild_all as ra

ASSETS = mp.ASSETS
ARCHIVE = os.path.expanduser(r"~\Downloads\NELLO_ARCHIVE")
MIN_DUR = 105.0
MIN_MB = 200 * 1024 * 1024


def pick_clips(rel, trailer, movie, wide=False):
    if not wide:
        clips, tail = mp.speech_cuts(rel, max_clips=28, return_tail=True, dmax=8)
        if clips:
            if tail:
                T = b.probe_duration(trailer)
                clips = clips + [(tail, round(T - tail, 2))]
            return clips
    wins = m.energy_windows(rel, count=26 if wide else 18,
                            win=5.5 if wide else 3.8,
                            min_gap=3.5 if wide else 5.5,
                            seed=(hash(movie) % 5000) + (777 if wide else 0))
    return [(round(t, 2), round(d, 2)) for t, d in wins]


def render(key, rel, clips):
    for f in glob.glob(os.path.join(ASSETS, f"{key}*")):
        try:
            os.remove(f)
        except OSError:
            pass
    seg = b.build_clean_montage(key, rel, clips, target_name=key)
    mp._finish_single(key, [seg])
    out = os.path.join(ASSETS, key + ".mp4")
    polished = p.polish(out)
    os.replace(polished, out)
    return out


def main():
    movie, year = sys.argv[1], sys.argv[2]
    custom = sys.argv[3] if len(sys.argv) > 3 else None
    trailer = ra.find_trailer(movie, year)
    if not trailer:
        print("NO TRAILER FOUND for", movie, year); sys.exit(1)
    print("trailer:", trailer)
    rel = os.path.relpath(trailer, ASSETS).replace(os.sep, "/")
    key = "rm_" + mp.slug(movie)[:20]

    clips = pick_clips(rel, trailer, movie)
    print(f"pass1: {len(clips)} clips")
    out = render(key, rel, clips)
    dur = b.probe_duration(out)

    if dur < MIN_DUR:
        print(f"pass1 too short ({dur:.0f}s) — rebuilding wider")
        clips = pick_clips(rel, trailer, movie, wide=True)
        print(f"pass2: {len(clips)} clips")
        out = render(key, rel, clips)
        dur = b.probe_duration(out)

    title = custom or f"{movie} ({year}) — The Official Trailer Edit"
    thumb = os.path.join(ASSETS, f"rm_thumb_{mp.slug(movie)[:20]}.jpg")
    mp.make_thumb(out, movie, f"{year} Official Trailer Edit", thumb)
    tgt = os.path.join(ARCHIVE, title + ".mp4")
    shutil.copy(out, tgt)
    size = os.path.getsize(tgt)
    flag = "OK" if size >= MIN_MB else "UNDER-200MB!"
    print(f"wrote: {tgt} {dur:.0f}s {size/1048576:.0f}MB [{flag}]")
    for f in glob.glob(os.path.join(ASSETS, f"{key}*")):
        try:
            os.remove(f)
        except OSError:
            pass
    print("DONE", title)


if __name__ == "__main__":
    main()
