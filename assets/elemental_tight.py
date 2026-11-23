"""Elemental pilot: tighter, punchier trailer edit (~60-75s)."""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
import build_video as b
import make_edit as m
import polish as p

ASSETS = mp.ASSETS
SRC = "trailers_dl/elemental.mp4"
OUT_DIR = os.path.expanduser(r"~\Downloads\MOVIE_MOMENTS")

clips, tail = mp.speech_cuts(SRC, max_clips=12, return_tail=True, dmax=5.0)
print("clips:", clips, "tail:", tail, flush=True)
if tail:
    T = b.probe_duration(os.path.join(ASSETS, SRC))
    clips = clips + [(tail, round(T - tail, 2))]
key = "elemental_tight"
seg = b.build_clean_montage(key, SRC, clips, target_name=key + ".mp4")
mp._finish_single(key, [seg])
out = os.path.join(ASSETS, key + ".mp4")
polished = p.polish(out)
os.replace(polished, out)
mp.make_thumb(out, "Elemental", "2023 Trailer Edit",
              os.path.join(ASSETS, key + ".jpg"))
title = "Elemental (2023) — The Official Trailer Edit.mp4"
shutil.copy(out, os.path.join(OUT_DIR, title))
print(f"OK -> {b.probe_duration(out):.0f}s -> {title}", flush=True)
