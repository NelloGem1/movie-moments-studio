"""Re-mix all edits with the updated score (no harp/celesta)."""
import os, glob, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_video as b
import score as sc
from batch_edits import JOBS

ASSETS = b.ASSETS
FF = b.FFMPEG

for name, movies, kw in JOBS:
    base = os.path.join(ASSETS, f"{name}_base.mp4")
    final = os.path.join(ASSETS, f"{name}.mp4")
    if not os.path.exists(base) or name == "movies_2009":
        pass
    if not os.path.exists(base):
        print("no base:", name); continue
    # recompute section bounds from segment files
    bounds = []
    t = 0.0
    for tag, src in movies:
        segs = glob.glob(os.path.join(ASSETS, f"edit_{tag}*.mp4"))
        if not segs:
            print("missing seg", tag); break
        d = b.probe_duration(segs[0])
        t += d
        bounds.append(t)
    else:
        total = b.probe_duration(base)
        sp = os.path.join(ASSETS, f"{name}_score.wav")
        sc.make_score(total, bounds[:-1], sp)
        fc = (f"[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
              f"volume=0.9[tr];"
              f"[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
              f"volume=0.5[mus];"
              f"[tr][mus]amix=inputs=2:duration=first:dropout_transition=0,"
              f"lowshelf=f=120:g=5,equalizer=f=90:w=150:g=4,"
              f"loudnorm=I=-13:TP=-1.5:LRA=11[aout]")
        tmp = final + ".new.mp4"
        subprocess.run([FF, "-y", "-i", base, "-i", sp, "-filter_complex", fc,
                        "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                        tmp], check=True, capture_output=True)
        os.replace(tmp, final)
        subprocess.run(["cp", final, os.path.join(os.path.expanduser("~"), "Downloads", name + ".mp4")])
        print("remixed:", name, f"{total:.0f}s")
