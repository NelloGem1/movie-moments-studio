"""Generic trailer-edit builder: energy peaks -> fx montage -> score -> mux."""
import os, subprocess, sys
import numpy as np
import build_video as b
import score as sc

ASSETS = b.ASSETS
FF = b.FFMPEG
FFPROBE = b.FFPROBE


def energy_windows(src, count=4, win=4.5, min_gap=9.0, seed=0):
    """Top-energy windows from a trailer's audio."""
    p = subprocess.run([FF, "-v", "error", "-i", os.path.join(ASSETS, src),
                        "-vn", "-ac", "1", "-ar", "22050", "-f", "s16le", "-"],
                       capture_output=True)
    pcm = np.frombuffer(p.stdout, dtype=np.int16).astype(np.float32)
    sr = 22050; w = sr // 2
    rms = [float(np.sqrt(np.mean(pcm[i:i + w] ** 2))) for i in range(0, len(pcm) - w, w)]
    k = 4
    sm = [float(np.mean(rms[i:i + k])) for i in range(len(rms) - k)]
    rng = np.random.default_rng(seed)
    # jitter the scores so different seeds pick different peak sets
    sm = [v * (0.9 + 0.2 * rng.random()) for v in sm]
    order = np.argsort(sm)[::-1]
    dur = b.probe_duration(os.path.join(ASSETS, src))
    picked = []
    for idx in order:
        t = idx * 0.5 + rng.uniform(-0.8, 0.8)
        t = max(0.0, min(t, dur - win - 2))
        if all(abs(t - p) > min_gap for p in picked):
            picked.append(t)
        if len(picked) >= count:
            break
    return sorted((t, win) for t in picked)


def build_movie_seg(tag, src, windows):
    """One movie's montage via fx transitions."""
    clips = [(st, d) for st, d in windows]
    return b.build_fx_montage(tag, src, clips, f"edit_{tag}.mp4",
                              seed=(hash(tag) & 0xFFFF) ^ WIN_SEED)


WIN_SEED = 0


def make_edit(out_name, movies, per_movie=4, win=4.5, score_vol=0.5,
              tr_vol=0.9, seed=0, min_gap=9.0):
    """movies = [(tag, src_path_relative), ...]"""
    global WIN_SEED
    WIN_SEED = seed
    segs = []
    bounds = []
    t_acc = 0.0
    for tag, src in movies:
        wins = energy_windows(src, count=per_movie, win=win, min_gap=min_gap,
                              seed=seed + hash(tag) % 1000)
        seg = build_movie_seg(tag, src, wins)
        segs.append(seg)
        seg_dur = b.probe_duration(seg)
        bounds.append(t_acc + seg_dur)
        t_acc += seg_dur
        print(f"[{tag}] {len(wins)} windows -> {seg_dur:.1f}s")

    concat = os.path.join(ASSETS, f"concat_{out_name}.txt")
    with open(concat, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    base = os.path.join(ASSETS, f"{out_name}_base.mp4")
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", concat,
                    "-c", "copy", "-movflags", "+faststart", base], check=True)
    total = b.probe_duration(base)

    score_path = os.path.join(ASSETS, f"{out_name}_score.wav")
    sc.make_score(total, bounds[:-1], score_path)

    final = os.path.join(ASSETS, f"{out_name}.mp4")
    fc = (f"[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
          f"volume={tr_vol}[tr];"
          f"[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
          f"volume={score_vol}[mus];"
          f"[tr][mus]amix=inputs=2:duration=first:dropout_transition=0,"
          f"lowshelf=f=120:g=5,equalizer=f=90:w=150:g=4,"
          f"loudnorm=I=-13:TP=-1.5:LRA=11[aout]")
    subprocess.run([FF, "-y", "-i", base, "-i", score_path,
                    "-filter_complex", fc, "-map", "0:v", "-map", "[aout]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", final], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")
    return final


if __name__ == "__main__":
    spec = eval(sys.argv[1]) if len(sys.argv) > 1 else None
