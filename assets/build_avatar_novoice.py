"""Avatar trailer-only edit — no narration, original audio."""
import build_video as b
import os, subprocess

SRC = "y2009/avatar.mp4"
SEGS = [
    ("avn_1", 0.05), ("avn_2", 0.30), ("avn_3", 0.55),
    ("avn_4", 0.15), ("avn_5", 0.70), ("avn_6", 0.40), ("avn_7", 0.80),
]

def main():
    segs = [b.build_segment_novoice(name, SRC, target=22.0, phase=ph)
            for name, ph in SEGS]
    concat = os.path.join(b.ASSETS, "concat_avn.txt")
    with open(concat, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(b.ASSETS, "avatar_novoice.mp4")
    subprocess.run([b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat,
                    "-c", "copy", "-movflags", "+faststart", final], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
