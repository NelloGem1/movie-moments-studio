"""Build 'Movies That Changed Cinema in 2009' video — narrator drop-out style."""
import build_video as b
import os, subprocess

SEGS = [
    ("y09_intro",   "y2009/avatar.mp4",   "voice_y09_1_in.mp3",  "voice_y09_1_out.mp3",  0.05),
    ("y09_avatar",  "y2009/avatar.mp4",   "voice_y09_2_in.mp3",  "voice_y09_2_out.mp3",  0.45),
    ("y09_startrek","y2009/startrek.mp4", "voice_y09_3_in.mp3",  "voice_y09_3_out.mp3",  0.15),
    ("y09_sherlock","y2009/sherlock.mp4", "voice_y09_4_in.mp3",  "voice_y09_4_out.mp3",  0.55),
    ("y09_hangover","y2009/hangover.mp4","voice_y09_5_in.mp3",  "voice_y09_5_out.mp3",  0.25),
    ("y09_up",      "y2009/up.mp4",       "voice_y09_6_in.mp3",  "voice_y09_6_out.mp3",  0.65),
    ("y09_2012",    "y2009/2012.mp4",     "voice_y09_7_in.mp3",  "voice_y09_7_out.mp3",  0.35),
    ("y09_outro",   "y2009/avatar.mp4",   "voice_y09_8_in.mp3",  "voice_y09_8_out.mp3",  0.75),
]

def main():
    segs = [b.build_segment_split(name, src, vi, vo, "", "", phase=ph)
            for name, src, vi, vo, ph in SEGS]
    concat = os.path.join(b.ASSETS, "concat_y09.txt")
    with open(concat, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(b.ASSETS, "movies_2009.mp4")
    subprocess.run([b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat,
                    "-c", "copy", "-movflags", "+faststart", final], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
