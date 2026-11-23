"""Video 4: Doctor Doom - Everything We Know."""
import build_video as b
import os, subprocess

SEGMENTS4 = [
    ("intro4", "return_trailer.mp4",  "voice_intro4.mp3", "DOCTOR DOOM EXPLAINED",  "ROBERT DOWNEY JR"),
    ("who",    "official_teaser.mp4", "voice_who.mp3",    "WHO IS DOCTOR DOOM",     "THE VILLAIN"),
    ("rdj",    "return_trailer.mp4",  "voice_rdj.mp3",    "WHY RDJ IS PERFECT",    "IRON MAN VILLAIN"),
    ("powers", "return_trailer.mp4",  "voice_powers.mp3", "DOOM'S POWERS",          "DARK DIMENSION"),
    ("stakes", "official_teaser.mp4", "voice_stakes.mp3", "WHY HE MATTERS",         "MULTIVERSE"),
    ("outro4", "return_trailer.mp4",  "voice_outro4.mp3", "DECEMBER 18 - IN THEATERS","SUBSCRIBE"),
]

def main():
    segs = []
    phases = [0.15, 0.4, 0.6, 0.25, 0.7, 0.45]
    for s, ph in zip(SEGMENTS4, phases):
        segs.append(b.build_segment(*s, phase=ph))
    concat_list = os.path.join(b.ASSETS, "concat4.txt")
    with open(concat_list, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(b.ASSETS, "doomsday_doom.mp4")
    subprocess.run([
        b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", "-movflags", "+faststart", final,
    ], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
