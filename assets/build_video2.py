"""Video 2: Avengers Doomsday - The Complete Cast List."""
import build_video as b
import os, subprocess

SEGMENTS2 = [
    ("intro2",  "official_teaser.mp4", "voice_intro2.mp3",  "THE COMPLETE CAST",      "AVENGERS DOOMSDAY"),
    ("core",    "steve_teaser.mp4",    "voice_core.mp3",    "CORE AVENGERS RETURN",    "CHRIS EVANS + MORE"),
    ("new",     "return_trailer.mp4",  "voice_new.mp3",     "THE NEW GENERATION",      "FRESH FACE REUNIONS"),
    ("xmen",    "xmen_teaser.mp4",     "voice_xmen.mp3",    "THE X-MEN RETURN",        "STEWART + MCCLLEN"),
    ("ff",      "wakanda_teaser.mp4",  "voice_ff.mp3",      "WAKANDA + FANTASTIC FOUR","MIGHTIEST TEAMS"),
    ("doom",    "return_trailer.mp4",  "voice_doom.mp3",    "DOCTOR DOOM HIMSELF",      "ROBERT DOWNEY JR"),
    ("outro2",  "official_teaser.mp4", "voice_outro2.mp3",  "DECEMBER 18 - IN THEATERS","SUBSCRIBE FOR MORE"),
]

def main():
    segs = [b.build_segment(*s) for s in SEGMENTS2]
    concat_list = os.path.join(b.ASSETS, "concat2.txt")
    with open(concat_list, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(b.ASSETS, "doomsday_cast.mp4")
    subprocess.run([
        b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", "-movflags", "+faststart", final,
    ], check=True)
    print("FINAL:", final, f"{b.probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
