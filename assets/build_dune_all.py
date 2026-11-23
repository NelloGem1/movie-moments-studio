"""Build all 4 remaining Dune videos sequentially."""
import build_video as b
import os, subprocess

VIDEOS = {
    "dune_cast": [
        ("introA", "dune_final.mp4",    "voice_introA.mp3",  "THE COMPLETE CAST",   "DUNE PART 3"),
        ("coreA",  "dune_teaser.mp4",   "voice_coreA.mp3",   "PAUL + CHANI + IDAHO", "LEADERS"),
        ("ladiesA","dune_trailer2.mp4", "voice_ladiesA.mp3", "THE WOMEN OF ARRAKIS", "IRULAN + JESSICA"),
        ("newA",   "dune_final.mp4",    "voice_newA.mp3",    "NEW FACES + PATTINSON", "STAR-STUDDED"),
        ("outroA", "dune_teaser.mp4",   "voice_outroA.mp3",  "DECEMBER 18 - IN THEATERS","SUBSCRIBE"),
    ],
    "dune_theories": [
        ("introB",  "dune_final.mp4",    "voice_introB.mp3",  "HERO OR VILLAIN",     "PAUL ATREIDES"),
        ("heroB",   "dune_teaser.mp4",   "voice_heroB.mp3",   "THE CASE FOR HERO",   "MESSIAH"),
        ("villainB","dune_final.mp4",    "voice_villainB.mp3","THE CASE FOR VILLAIN", "TYRANT?"),
        ("verdictB","dune_trailer2.mp4", "voice_verdictB.mp3","MY VERDICT",          "CORRUPTION"),
        ("outroB",  "dune_teaser.mp4",   "voice_outroB.mp3",  "DECEMBER 18 - IN THEATERS","SUBSCRIBE"),
    ],
    "dune_guide": [
        ("introC", "dune_final.mp4",    "voice_introC.mp3", "DUNE PART 3 GUIDE",   "DEC 18"),
        ("dateC",  "dune_teaser.mp4",   "voice_dateC.mp3",  "DECEMBER 18, 2026",   "RELEASE DATE"),
        ("storyC", "dune_final.mp4",    "voice_storyC.mp3", "THE STORY SO FAR",    "MUAD'DIB"),
        ("expectC","dune_trailer2.mp4", "voice_expectC.mp3","WHAT TO EXPECT",      "IMAX EVENT"),
        ("outroC", "dune_teaser.mp4",   "voice_outroC.mp3", "GET YOUR TICKETS",    "ARRAKIS"),
    ],
    "dune_recap": [
        ("introD2","dune_trailer2.mp4", "voice_introD.mp3", "PART 2 RECAP",        "GET READY"),
        ("recap1", "dune_final.mp4",    "voice_recap1.mp3", "PARTS 1 AND 2",        "STORY SO FAR"),
        ("recap2", "dune_teaser.mp4",   "voice_recap2.mp3", "WHERE PART 2 ENDED",   "THE THRONE"),
        ("recap3", "dune_final.mp4",    "voice_recap3.mp3", "WHO TO REMEMBER",      "CAST"),
        ("outroD2","dune_trailer2.mp4", "voice_outroD2.mp3","DECEMBER 18 - IN THEATERS","SUBSCRIBE"),
    ],
}

def main():
    for vname, segs_def in VIDEOS.items():
        print("=" * 30, vname, "=" * 30, flush=True)
        segs = []
        for idx, s in enumerate(segs_def):
            segs.append(b.build_segment(*s, phase=idx * 0.23 + 0.1))
        concat_list = os.path.join(b.ASSETS, f"concat_{vname}.txt")
        with open(concat_list, "w") as f:
            for p in segs:
                f.write(f"file '{p.replace(os.sep, '/')}'\n")
        final = os.path.join(b.ASSETS, f"{vname}.mp4")
        subprocess.run([
            b.FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
            "-c", "copy", "-movflags", "+faststart", final,
        ], check=True)
        print("FINAL:", final, f"{b.probe_duration(final):.1f}s", flush=True)

if __name__ == "__main__":
    main()
