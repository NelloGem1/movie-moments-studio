"""Video 6: Dune Part Three - Final Trailer Breakdown."""
import build_video as b
import os, subprocess

SEGMENTS6 = [
    ("introD", "dune_final.mp4",  "voice_introD.mp3", "DUNE PART 3 BREAKDOWN", "DEC 18"),
    ("story",  "dune_final.mp4",  "voice_story.mp3",  "THE STORY SO FAR",      "PAUL ATREIDES"),
    ("cast",   "dune_teaser.mp4", "voice_cast.mp3",   "THE RETURNING CAST",    "CHALAMET + MORE"),
    ("villain", "dune_final.mp4", "voice_villain.mp3","IS PAUL THE VILLAIN",   "THE DEBATE"),
    ("outroD", "dune_teaser.mp4", "voice_outroD.mp3", "DECEMBER 18 - IN THEATERS","SUBSCRIBE"),
]

def main():
    segs = []
    phases = [0.1, 0.45, 0.2, 0.7, 0.5]
    for s, ph in zip(SEGMENTS6, phases):
        segs.append(b.build_segment(*s, phase=ph))
    concat_list = os.path.join(b.ASSETS, "concat6.txt")
    with open(concat_list, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(b.ASSETS, "dune_breakdown.mp4")
    subprocess.run([
        b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", "-movflags", "+faststart", final,
    ], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
