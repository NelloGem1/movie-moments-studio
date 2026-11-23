"""Video 3: The Baby in the Steve Rogers Teaser - Every Theory Explained."""
import build_video as b
import os, subprocess

SEGMENTS3 = [
    ("intro3",  "steve_teaser.mp4",    "voice_intro3.mp3",  "THE BABY THEORY",      "STEVE ROGERS"),
    ("theory1", "steve_teaser.mp4",    "voice_theory1.mp3", "THEORY 1 - PEGGY CARTER","MOST LIKELY"),
    ("theory2", "return_trailer.mp4",  "voice_theory2.mp3", "THEORY 2 - SHARON CARTER","THE NIECE"),
    ("theory3", "official_teaser.mp4", "voice_theory3.mp3", "THEORY 3 - A NEW CAP?", "LEGACY TWIST"),
    ("verdict", "steve_teaser.mp4",    "voice_verdict.mp3", "MY VERDICT",           "PEGGY WINS"),
    ("outro3",  "steve_teaser.mp4",    "voice_outro3.mp3",  "DECEMBER 18 - IN THEATERS","SUBSCRIBE"),
]

def main():
    segs = []
    phases = [0.0, 0.3, 0.55, 0.75, 0.1, 0.6]
    for s, ph in zip(SEGMENTS3, phases):
        segs.append(b.build_segment(*s, phase=ph))
    concat_list = os.path.join(b.ASSETS, "concat3.txt")
    with open(concat_list, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(b.ASSETS, "doomsday_baby.mp4")
    subprocess.run([
        b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", "-movflags", "+faststart", final,
    ], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
