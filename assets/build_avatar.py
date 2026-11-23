"""Build the Avatar breakdown video — narrator drop-out style."""
import build_video as b
import os, subprocess

SRC = "y2009/avatar.mp4"

SEGS = [
    ("av_hook",    "voice_av_1_in.mp3",  "voice_av_1_out.mp3",  0.05),
    ("av_pandora", "voice_av_2_in.mp3",  "voice_av_2_out.mp3",  0.40),
    ("av_jake",    "voice_av_3_in.mp3",  "voice_av_3_out.mp3",  0.20),
    ("av_choice",  "voice_av_4_in.mp3",  "voice_av_4_out.mp3",  0.60),
    ("av_battle",  "voice_av_5_in.mp3",  "voice_av_5_out.mp3",  0.30),
    ("av_record",  "voice_av_6_in.mp3",  "voice_av_6_out.mp3",  0.70),
    ("av_legacy",  "voice_av_7_in.mp3",  "voice_av_7_out.mp3",  0.50),
]

def main():
    segs = [b.build_segment_split(name, SRC, vi, vo, "", "", phase=ph)
            for name, vi, vo, ph in SEGS]
    concat = os.path.join(b.ASSETS, "concat_av.txt")
    with open(concat, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(b.ASSETS, "avatar_story.mp4")
    subprocess.run([b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat,
                    "-c", "copy", "-movflags", "+faststart", final], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
