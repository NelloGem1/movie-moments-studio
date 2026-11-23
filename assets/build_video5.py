"""Video 5: Avengers Doomsday - Release Date, Plot & What to Expect."""
import build_video as b
import os, subprocess

SEGMENTS5 = [
    ("intro5", "official_teaser.mp4", "voice_intro5.mp3", "DOOMSDAY GUIDE",      "AVENGERS DOOMSDAY"),
    ("date",   "official_teaser.mp4", "voice_date.mp3",   "DECEMBER 18, 2026",    "RELEASE DATE"),
    ("plot",   "return_trailer.mp4",  "voice_plot.mp3",   "THE PLOT SO FAR",      "MULTIVERSE WAR"),
    ("expect", "official_teaser.mp4", "voice_expect.mp3", "WHAT TO EXPECT",       "BIGGEST EVER"),
    ("outro5", "return_trailer.mp4",  "voice_outro5.mp3", "GET YOUR TICKETS",     "DEC 18"),
]

def main():
    segs = []
    phases = [0.2, 0.5, 0.1, 0.65, 0.35]
    for s, ph in zip(SEGMENTS5, phases):
        segs.append(b.build_segment(*s, phase=ph))
    concat_list = os.path.join(b.ASSETS, "concat5.txt")
    with open(concat_list, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(b.ASSETS, "doomsday_guide.mp4")
    subprocess.run([
        b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", "-movflags", "+faststart", final,
    ], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
