"""Rebuild the non-'Official Trailer Edit' uploads (Avengers/Dune/Indiana
Jones specials) to the clean-cut Inside Out 2 standard."""
import os, sys, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
import build_video as b
import make_edit as m
import polish as p
from youtube_api import get_service

ASSETS = mp.ASSETS
LOG = os.path.join(ASSETS, "rebuild_special.log")
QUOTA_STOP = os.path.join(ASSETS, "QUOTA_STOP")

# vid -> (title, desc_extra, [(tag, src_rel), ...], thumb_sub)
JOBS = {
    "VL5MdaOdGAU": ("Avengers: Doomsday — Every Reveal in One Epic Edit",
        [("av_official", "official_teaser.mp4"), ("av_return", "return_trailer.mp4")],
        "Every Reveal Edit"),
    "hVaBvUUvTBw": ("Avengers: Doomsday — The Steve Rogers Teaser Edit",
        [("av_steve", "steve_teaser.mp4")], "Steve Rogers Edit"),
    "tuEV2msj-7k": ("Avengers: Doomsday — The Thor Teaser Edit",
        [("av_thor", "thor_teaser.mp4")], "Thor Edit"),
    "OvKN_fqIrrk": ("Avengers: Doomsday — X-Men & Wakanda Teaser Edit",
        [("av_xmen", "xmen_teaser.mp4"), ("av_wakanda", "wakanda_teaser.mp4")],
        "X-Men & Wakanda Edit"),
    "yAFsro1QUbE": ("Avengers: Doomsday — Every Character Teaser Edit",
        [("av_m1", "steve_teaser.mp4"), ("av_m2", "thor_teaser.mp4"),
         ("av_m3", "xmen_teaser.mp4"), ("av_m4", "wakanda_teaser.mp4")],
        "Every Character Edit"),
    "2iqTuvmGb-E": ("Dune Part Three — The Final Trailer Edit",
        [("dun_t2", "dune_trailer2.mp4"), ("dun_p3", "dune_p3_teaser.mp4")],
        "Final Trailer Edit"),
    "qECve57YJlI": ("Dune Part Three — The Official Teaser Edit",
        [("dun_p3", "dune_p3_teaser.mp4")], "Official Teaser Edit"),
    "DNMs5BrHXDM": ("Dune — Every Teaser in One Epic Edit",
        [("dun_teaser", "dune_teaser.mp4"), ("dun_p3", "dune_p3_teaser.mp4")],
        "Every Teaser Edit"),
    "bGKYZ2hK-tU": ("Dune — Every Version, One Epic Edit",
        [("dun_teaser", "dune_teaser.mp4"), ("dun_lynch", "dune_1984.mp4")],
        "Every Version Edit"),
    "jvcjFSSVw0A": ("Indiana Jones and the Kingdom of the Crystal Skull (2008) — Trailer Edit",
        [("y08_indiana", "y2008/indiana.mp4")], "2008 Trailer Edit"),
}

TAGS = {
    "VL5MdaOdGAU": ["#AvengersDoomsday", "#Marvel", "#MCU"],
    "hVaBvUUvTBw": ["#AvengersDoomsday", "#SteveRogers", "#Marvel"],
    "tuEV2msj-7k": ["#AvengersDoomsday", "#Thor", "#Marvel"],
    "OvKN_fqIrrk": ["#AvengersDoomsday", "#XMen", "#Marvel"],
    "yAFsro1QUbE": ["#AvengersDoomsday", "#Marvel", "#MCU"],
    "2iqTuvmGb-E": ["#Dune", "#DunePart3", "#Arrakis"],
    "qECve57YJlI": ["#Dune", "#DunePart3", "#Arrakis"],
    "DNMs5BrHXDM": ["#Dune", "#DuneEdit", "#Arrakis"],
    "bGKYZ2hK-tU": ["#Dune", "#DuneEdit", "#SciFi"],
    "jvcjFSSVw0A": ["#IndianaJones", "#2008", "#Adventure"],
}


def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def clips_for(src_rel, want_tail):
    clips, tail = mp.speech_cuts(src_rel, return_tail=True)
    if not clips:
        wins = m.energy_windows(src_rel, count=14, win=4.0, min_gap=5.0,
                                seed=hash(src_rel) % 5000)
        clips = [(round(t, 2), round(d, 2)) for t, d in wins]
        tail = None
    if tail and want_tail:
        T = b.probe_duration(os.path.join(ASSETS, src_rel))
        clips = clips + [(tail, round(T - tail, 2))]
    return clips


def rebuild(vid, title, sources, sub):
    key = "rsp_" + vid
    try:
        segs = []
        boundaries = []
        t = 0.0
        clip_data = []
        for i, (tag, rel) in enumerate(sources):
            clips = clips_for(rel, want_tail=(i == len(sources) - 1))
            seg = b.build_clean_montage(f"{key}_{tag}", rel, clips,
                                        target_name=f"{key}_{tag}")
            segs.append(seg)
            clip_data.append((seg, clips))
        # finish with epic score: taiko hit on every cut + finale impact
        import score as sc
        concat = os.path.join(ASSETS, f"concat_{key}.txt")
        with open(concat, "w") as f:
            for s in segs:
                f.write(f"file '{s.replace(os.sep, '/')}'\n")
        base = os.path.join(ASSETS, f"{key}_base.mp4")
        subprocess.run([b.FFMPEG, "-y", "-f", "concat", "-safe", "0",
                        "-i", concat, "-c", "copy", "-movflags", "+faststart",
                        base], check=True, capture_output=True)
        total = b.probe_duration(base)
        # output-time cut boundaries from clip durations per segment
        off = 0.0
        for seg, clips in clip_data:
            sd = b.probe_duration(seg)
            acc = 0.0
            for st, d in clips[:-1]:
                acc += d
                bt = off + acc
                if 1 < bt < total - 2:
                    boundaries.append(round(bt, 2))
            off += sd
        s = sc.Score(total)
        for bt in boundaries:
            s.taiko(bt, f0=90, f1=40, dec=0.5, vol=0.55)
        s.timpani(total - 1.5, 55, 0.9)
        s.taiko(total - 1.5, f0=85, f1=38, dec=1.0, vol=1.0)
        s.boom(total - 1.5, 1.0)
        sp = os.path.join(ASSETS, f"{key}_score.wav")
        s.write(sp)
        fc = ("[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
              "volume=0.85[tr];"
              "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
              "volume=0.6[mus];"
              "[tr][mus]amix=inputs=2:duration=first:dropout_transition=0,"
              "lowshelf=f=120:g=5,equalizer=f=90:w=150:g=4,"
              "loudnorm=I=-13:TP=-1.5:LRA=11[aout]")
        out = os.path.join(ASSETS, key + ".mp4")
        subprocess.run([b.FFMPEG, "-y", "-i", base, "-i", sp,
                        "-filter_complex", fc, "-map", "0:v", "-map", "[aout]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", out], check=True,
                       capture_output=True)
        polished = p.polish(out)
        os.replace(polished, out)
        thumb = os.path.join(ASSETS, f"{key}_thumb.jpg")
        mp.make_thumb(out, title.split(" — ")[0], sub, thumb)
        desc = ("The most intense moments, cut into one cinematic edit "
                "with original trailer audio. No narration, just the movie.")
        tags = ["trailer edit", "movie edit", "cinematic edit"]
        desc += "\n\n" + " ".join(["#MovieEdit", "#TrailerEdit"] +
                                 TAGS.get(vid, []))
        new_vid = mp.upload(out, thumb, title, desc, tags)
        get_service().videos().delete(id=vid).execute()
        log("REBUILT:", title, "->", "https://youtu.be/" + new_vid)
        return True
    except Exception as e:
        log("ERR:", title, repr(e)[:200])
        s = str(e)
        if "exceeded the number of videos" in s:
            open(QUOTA_STOP, "w").write("quota")
            log("UPLOAD CAP — stopping pass")
            return "quota"
        if "quotaExceeded" in s or "exceeded your" in s:
            import youtube_api as _ya
            _ya.use_backup()
            log("API quota hit — switched to backup project")
        return False


def main():
    svc = get_service()
    log("=== special rebuild pass ===")
    quota = False
    for vid, (title, sources, sub) in JOBS.items():
        svc = get_service()
        # if the old video id no longer exists, it was already replaced
        try:
            chk = svc.videos().list(part="id", id=vid).execute()
        except Exception as e:
            if "exceeded the number of videos" in str(e):
                open(QUOTA_STOP, "w").write("quota")
                log("UPLOAD CAP — stopping pass")
                break
            if "quotaExceeded" in str(e) or "exceeded your" in str(e):
                import youtube_api as _ya
                _ya.use_backup()
                svc = get_service()
                try:
                    chk = svc.videos().list(part="id", id=vid).execute()
                except Exception as e2:
                    log("ERR(check):", title, repr(e2)[:150])
                    continue
            else:
                raise
        if not chk.get("items"):
            log("skip (already replaced):", title)
            continue
        if rebuild(vid, title, sources, sub) == "quota":
            break
        time.sleep(2)
    if not quota:
        log("=== special rebuild done ===")


if __name__ == "__main__":
    main()
