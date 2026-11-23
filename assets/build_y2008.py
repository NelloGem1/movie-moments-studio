"""Build 'Movies That Changed Cinema in 2008' video."""
import build_video as b
import os, subprocess

SEGS = [
    ("y08_intro",   "y2008/im.mp4",      "voice_y08_1.mp3", 0.05),
    ("y08_ironman", "y2008/im.mp4",      "voice_y08_2.mp3", 0.45),
    ("y08_darkknight","y2008/tdk.mp4",   "voice_y08_3.mp3", 0.15),
    ("y08_walle",   "y2008/walle.mp4",   "voice_y08_4.mp3", 0.55),
    ("y08_indiana", "y2008/indiana.mp4", "voice_y08_5.mp3", 0.25),
    ("y08_kungfu",  "y2008/kungfu.mp4",  "voice_y08_6.mp3", 0.65),
    ("y08_hulk",    "y2008/hulk.mp4",    "voice_y08_7.mp3", 0.35),
    ("y08_outro",   "y2008/tdk.mp4",     "voice_y08_8.mp3", 0.75),
]

def main():
    segs = [b.build_segment(name, src, voice, "", "", phase=ph)
            for name, src, voice, ph in SEGS]
    concat = os.path.join(b.ASSETS, "concat_y08.txt")
    with open(concat, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(b.ASSETS, "movies_2008.mp4")
    subprocess.run([b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat,
                    "-c", "copy", "-movflags", "+faststart", final], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
