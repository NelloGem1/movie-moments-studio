"""Build the Avengers: Doomsday breakdown video from trailer clips + TTS narration."""
import json
import math
import os
import re
import shutil
import subprocess
import sys

ASSETS = os.path.dirname(os.path.abspath(__file__))
FFMPEG = os.environ.get("FFMPEG", shutil.which("ffmpeg") or "/usr/bin/ffmpeg")
FFPROBE = os.environ.get("FFPROBE", shutil.which("ffprobe") or "/usr/bin/ffprobe")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# name, source video, narration voice file, big title text, small tag
SEGMENTS = [
    ("intro",   "official_teaser.mp4",  "voice_intro.mp3",   "EVERY REVEAL EXPLAINED",        "AVENGERS DOOMSDAY"),
    ("steve",   "steve_teaser.mp4",     "voice_steve.mp3",   "REVEAL 1 - CAPTAIN AMERICA",    "STEVE ROGERS RETURNS"),
    ("thor",    "thor_teaser.mp4",      "voice_thor.mp3",    "REVEAL 2 - THOR IS A FATHER",   "THOR ODINSON"),
    ("xmen",    "xmen_teaser.mp4",      "voice_xmen.mp3",    "REVEAL 3 - THE X-MEN RETURN",   "X-MEN ASSEMBLE"),
    ("wakanda", "wakanda_teaser.mp4",   "voice_wakanda.mp3", "REVEAL 4 - WAKANDA + FF",       "SHAKE IT UP"),
    ("return",  "return_trailer.mp4",   "voice_return.mp3",  "REVEAL 5 - DOCTOR DOOM",        "VICTOR VON DOOM"),
    ("outro",   "official_teaser.mp4",  "voice_outro.mp3",   "DECEMBER 18 - IN THEATERS",     "SUBSCRIBE FOR MORE"),
]


def probe_duration(path):
    out = subprocess.check_output(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], text=True)
    return float(out.strip())


def probe_height(path):
    out = subprocess.check_output(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=height", "-of", "csv=p=0", path], text=True)
    return int(out.strip())


def esc_drawtext(s):
    return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "%%")


def build_segment(name, src, voice, title, tag, phase=0.0):
    src_path = os.path.join(ASSETS, src)
    voice_path = os.path.join(ASSETS, voice)
    out_path = os.path.join(ASSETS, f"seg_{name}.mp4")

    # resume support: skip segments that already rendered successfully
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1_000_000:
        print(f"[{name}] already rendered, skipping")
        return out_path

    src_dur = probe_duration(src_path)
    aud_dur = probe_duration(voice_path)
    target = aud_dur + 0.4  # small tail

    # choose clip count/length to roughly cover narration
    clip_len = 3.6
    n = max(4, math.ceil(target / clip_len))
    # spread clip starts evenly, avoid first/last 5% of source
    margin = src_dur * 0.04
    usable = src_dur - 2 * margin - clip_len
    # phase shifts the window grid so different segments get different clips
    starts = []
    for i in range(n):
        t = margin + (i + phase) / n * usable
        t = min(t, src_dur - margin - clip_len)
        starts.append(max(margin, t))

    fc_parts = []
    labels = []
    alabels = []
    fade_d = 0.3
    for i, st in enumerate(starts):
        fc_parts.append(
            f"[0:v]trim=start={st:.2f}:duration={clip_len:.2f},"
            f"setpts=PTS-STARTPTS,"
            f"fade=t=in:st=0:d={fade_d},fade=t=out:st={clip_len - fade_d:.2f}:d={fade_d},"
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{i}]"
        )
        labels.append(f"[v{i}]")
        # matching audio slice from source trailer (kept quiet under narration)
        fc_parts.append(
            f"[0:a]atrim=start={st:.2f}:duration={clip_len:.2f},"
            f"asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:"
            f"channel_layouts=stereo,afade=t=in:st=0:d={fade_d},"
            f"afade=t=out:st={clip_len - fade_d:.2f}:d={fade_d}[a{i}]"
        )
        alabels.append(f"[a{i}]")
    fc_parts.append("".join(labels) + f"concat=n={n}:v=1:a=0[vcat]")
    fc_parts.append("".join(alabels) + f"concat=n={n}:v=0:a=1[acat]")
    # trailer audio bed at low volume, padded to cover video; mix with narration
    fc_parts.append("[acat]apad,volume=0.5[amb]")
    fc_parts.append("[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                    "volume=0.7[voice]")
    fc_parts.append("[amb][voice]amix=inputs=2:duration=longest:dropout_transition=0,"
                    "loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    fc_parts.append("[vcat]format=yuv420p[vout]")
    fc = ";".join(fc_parts)

    cmd = [
        FFMPEG, "-y", "-i", src_path, "-i", voice_path,
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{target:.2f}",
        "-movflags", "+faststart",
        out_path,
    ]
    print(f"[{name}] {n} clips x {clip_len}s, target {target:.1f}s")
    subprocess.run(cmd, check=True)
    return out_path


INTENSE_GAP = 7.0  # seconds of trailer-only "drop-out" moment per segment


def build_segment_split(name, src, voice_in, voice_out, title, tag, phase=0.0):
    """Narrator intro -> silent intense trailer moment -> narrator outro."""
    src_path = os.path.join(ASSETS, src)
    vin_path = os.path.join(ASSETS, voice_in)
    vout_path = os.path.join(ASSETS, voice_out)
    out_path = os.path.join(ASSETS, f"seg_{name}.mp4")

    if os.path.exists(out_path) and os.path.getsize(out_path) > 1_000_000:
        print(f"[{name}] already rendered, skipping")
        return out_path

    src_dur = probe_duration(src_path)
    in_dur = probe_duration(vin_path)
    out_dur = probe_duration(vout_path)
    outro_start = in_dur + INTENSE_GAP + 0.5
    target = outro_start + out_dur + 0.5
    # trailer audio goes loud only during the narrator-free window
    amb_hi_start = in_dur + 0.3
    amb_hi_end = in_dur + INTENSE_GAP + 0.4

    clip_len = 3.6
    n = max(5, math.ceil(target / clip_len))
    margin = src_dur * 0.04
    usable = src_dur - 2 * margin - clip_len
    starts = []
    for i in range(n):
        t = margin + (i + phase) / n * usable
        t = min(t, src_dur - margin - clip_len)
        starts.append(max(margin, t))

    fc_parts = []
    labels = []
    alabels = []
    fade_d = 0.3
    for i, st in enumerate(starts):
        fc_parts.append(
            f"[0:v]trim=start={st:.2f}:duration={clip_len:.2f},"
            f"setpts=PTS-STARTPTS,"
            f"fade=t=in:st=0:d={fade_d},fade=t=out:st={clip_len - fade_d:.2f}:d={fade_d},"
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{i}]"
        )
        labels.append(f"[v{i}]")
        fc_parts.append(
            f"[0:a]atrim=start={st:.2f}:duration={clip_len:.2f},"
            f"asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:"
            f"channel_layouts=stereo,afade=t=in:st=0:d={fade_d},"
            f"afade=t=out:st={clip_len - fade_d:.2f}:d={fade_d}[a{i}]"
        )
        alabels.append(f"[a{i}]")
    fc_parts.append("".join(labels) + f"concat=n={n}:v=1:a=0[vcat]")
    fc_parts.append("".join(alabels) + f"concat=n={n}:v=0:a=1[acat]")

    # trailer bed: quiet under narration, loud during the drop-out window
    fc_parts.append(
        "[acat]asplit=3[ac1][ac2][ac3];"
        f"[ac1]atrim=0:{amb_hi_start:.2f},asetpts=PTS-STARTPTS,volume=0.4[ba];"
        f"[ac2]atrim={amb_hi_start:.2f}:{amb_hi_end:.2f},asetpts=PTS-STARTPTS,volume=0.9[bb];"
        f"[ac3]atrim={amb_hi_end:.2f}:,asetpts=PTS-STARTPTS,volume=0.4,apad[bc];"
        "[ba][bb][bc]concat=n=3:v=0:a=1[amb]"
    )
    delay_ms = int(outro_start * 1000)
    fc_parts.append(
        "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "volume=0.7[vi];"
        "[2:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        f"volume=0.7,adelay={delay_ms}|{delay_ms}[vo];"
        "[amb][vi][vo]amix=inputs=3:duration=longest:dropout_transition=0,"
        "loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
    )
    fc_parts.append("[vcat]format=yuv420p[vout]")
    fc = ";".join(fc_parts)

    cmd = [
        FFMPEG, "-y", "-i", src_path, "-i", vin_path, "-i", vout_path,
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{target:.2f}",
        "-movflags", "+faststart",
        out_path,
    ]
    print(f"[{name}] {n} clips, intro {in_dur:.1f}s, gap {INTENSE_GAP}s, "
          f"outro {out_dur:.1f}s, target {target:.1f}s")
    subprocess.run(cmd, check=True)
    return out_path


def build_segment_novoice(name, src, target=22.0, phase=0.0):
    """Trailer-only segment: original movie audio, no narration."""
    src_path = os.path.join(ASSETS, src)
    out_path = os.path.join(ASSETS, f"seg_{name}.mp4")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1_000_000:
        print(f"[{name}] already rendered, skipping")
        return out_path

    src_dur = probe_duration(src_path)
    clip_len = 3.6
    n = max(5, math.ceil(target / clip_len))
    margin = src_dur * 0.04
    usable = src_dur - 2 * margin - clip_len
    starts = []
    for i in range(n):
        t = margin + (i + phase) / n * usable
        t = min(t, src_dur - margin - clip_len)
        starts.append(max(margin, t))

    fc_parts, labels, alabels = [], [], []
    fade_d = 0.3
    for i, st in enumerate(starts):
        fc_parts.append(
            f"[0:v]trim=start={st:.2f}:duration={clip_len:.2f},"
            f"setpts=PTS-STARTPTS,"
            f"fade=t=in:st=0:d={fade_d},fade=t=out:st={clip_len - fade_d:.2f}:d={fade_d},"
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{i}]"
        )
        labels.append(f"[v{i}]")
        fc_parts.append(
            f"[0:a]atrim=start={st:.2f}:duration={clip_len:.2f},"
            f"asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:"
            f"channel_layouts=stereo,afade=t=in:st=0:d={fade_d},"
            f"afade=t=out:st={clip_len - fade_d:.2f}:d={fade_d}[a{i}]"
        )
        alabels.append(f"[a{i}]")
    fc_parts.append("".join(labels) + f"concat=n={n}:v=1:a=0[vcat]")
    fc_parts.append("".join(alabels) + f"concat=n={n}:v=0:a=1[acat]")
    fc_parts.append("[acat]apad,volume=0.9,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    fc_parts.append("[vcat]format=yuv420p[vout]")
    fc = ";".join(fc_parts)

    cmd = [
        FFMPEG, "-y", "-i", src_path,
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{target:.2f}",
        "-movflags", "+faststart",
        out_path,
    ]
    print(f"[{name}] {n} clips, target {target:.1f}s (no voice)")
    subprocess.run(cmd, check=True)
    return out_path


XFADE_TRANSITIONS = [
    "fade", "fadeblack", "fadewhite", "fadegrays",
    "dissolve", "pixelize", "zonedice", "hblur",
    "radial", "distance",
    "wipeleft", "wiperight", "wipeup", "wipedown",
    "wipetl", "wipetr", "wipebl", "wipebr",
    "slideleft", "slideright", "slideup", "slidedown",
    "smoothleft", "smoothright", "smoothup", "smoothdown",
    "circleopen", "circleclose",
    "vertopen", "vertclose", "horzopen", "horzclose",
    "diagbl", "diagbr", "diagtl", "diagtr",
    "hlslice", "hrslice", "vuslice", "vdslice",
    "coverleft", "coverright", "coverup", "coverdown",
    "squeezeh", "squeezev", "zoomin", "zoomout",
    "hlwind", "hrwind", "vuwind", "vdwind",
]


def build_xfade(name, src, clips, target_name=None, fd=0.4, trans_list=None,
                loudnorm=True):
    """Montage with real xfade transitions between clips.
    clips = [(start_sec, duration_sec), ...] all from one source file."""
    import random
    src_path = os.path.join(ASSETS, src)
    out_path = os.path.join(ASSETS, f"{target_name or name}.mp4")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 500_000:
        print(f"[{name}] already rendered, skipping")
        return out_path

    n = len(clips)
    rng = random.Random(hash(name) & 0xFFFF)
    pool = trans_list or XFADE_TRANSITIONS
    chosen = [pool[rng.randrange(len(pool))] for _ in range(n - 1)]

    # one input per clip with fast seek — avoids decoding the whole source n times
    fc = []
    for i, (st, d) in enumerate(clips):
        fc.append(
            f"[{i}:v]setpts=PTS-STARTPTS,"
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p[v{i}]"
        )
        fc.append(
            f"[{i}:a]asetpts=PTS-STARTPTS,"
            f"aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]"
        )

    # video xfade chain: out_dur = offset + d_next ; offset = L_prev - fd
    L = clips[0][1]
    vprev = "[v0]"
    for i in range(1, n):
        off = L - fd
        fc.append(f"{vprev}[v{i}]xfade=transition={chosen[i-1]}:"
                  f"duration={fd}:offset={off:.3f}[x{i}]")
        vprev = f"[x{i}]"
        L = L + clips[i][1] - fd
    fc.append(f"{vprev}format=yuv420p[vout]")

    # audio acrossfade chain (same timing math)
    aprev = "[a0]"
    for i in range(1, n):
        fc.append(f"{aprev}[a{i}]acrossfade=d={fd}:c1=tri:c2=tri[ax{i}]")
        aprev = f"[ax{i}]"
    if loudnorm:
        fc.append(f"{aprev}apad,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    else:
        fc.append(f"{aprev}apad,volume=1.0,alimiter=limit=0.95[aout]")

    inputs = []
    for st, d in clips:
        inputs += ["-ss", f"{st:.2f}", "-t", f"{d:.2f}", "-i", src_path]
    cmd = (
        [FFMPEG, "-y"] + inputs +
        ["-filter_complex", ";".join(fc),
         "-map", "[vout]", "-map", "[aout]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", out_path]
    )
    print(f"[{name}] {n} clips, transitions: {chosen}")
    subprocess.run(cmd, check=True)
    return out_path


def _entrance_fx(kind, rng):
    """Return (video_filters, exit_color) for a clip entrance.
    exit_color = color this clip should fade OUT to (matches next entrance)."""
    if kind == "white":
        return "fade=t=in:st=0:d=0.35:color=white", "white"
    if kind == "color":
        c = rng.choice(["0xFF3300", "0x2255FF", "0xFFDD00", "0x00CC88"])
        return f"fade=t=in:st=0:d=0.35:color={c}", c
    if kind == "flash":
        return ("fade=t=in:st=0:d=0.3,"
                "eq=brightness=0.35:saturation=0.4:enable='between(t,0,0.15)'"), "black"
    if kind == "glitch":
        return ("fade=t=in:st=0:d=0.25,"
                "noise=alls=12:allf=t+u:enable='between(t,0,0.3)',"
                "eq=contrast=1.4:enable='between(t,0,0.3)'"), "black"
    if kind == "focus":
        return ("fade=t=in:st=0:d=0.4,"
                "gblur=sigma=6:enable='between(t,0,0.45)'"), "black"
    return "fade=t=in:st=0:d=0.35", "black"  # plain fade from black


ENTRANCES = ["black", "white", "flash", "glitch", "focus"]


def build_fx_montage(name, src, clips, target_name=None, seed=7):
    """Fast montage with varied transition FX (dip-to-color, flash, glitch,
    focus-pull) using per-clip inputs — no xfade, renders quickly."""
    import random
    src_path = os.path.join(ASSETS, src)
    out_path = os.path.join(ASSETS, f"{target_name or name}.mp4")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 500_000:
        print(f"[{name}] already rendered, skipping")
        return out_path

    n = len(clips)
    rng = random.Random(seed)
    kinds = [ENTRANCES[rng.randrange(len(ENTRANCES))] for _ in range(n)]
    entrances = [_entrance_fx(k, rng) for k in kinds]  # (vf, in_color)
    fc, vlabels, alabels = [], [], []

    for i, (st, d) in enumerate(clips):
        vf, _ = entrances[i]
        # exit fades to the NEXT clip's entrance color (dip-to-color)
        exit_color = entrances[i + 1][1] if i + 1 < n else "black"
        fc.append(
            f"[{i}:v]setpts=PTS-STARTPTS,"
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,format=yuv420p,"
            f"{vf},fade=t=out:st={d-0.35:.2f}:d=0.35:color={exit_color}[v{i}]"
        )
        vlabels.append(f"[v{i}]")
        fc.append(
            f"[{i}:a]asetpts=PTS-STARTPTS,"
            f"aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"afade=t=in:st=0:d=0.3,afade=t=out:st={d-0.35:.2f}:d=0.35[a{i}]"
        )
        alabels.append(f"[a{i}]")
    fc.append("".join(vlabels) + f"concat=n={n}:v=1:a=0[vcat]")
    fc.append("".join(alabels) + f"concat=n={n}:v=0:a=1[acat]")
    fc.append("[acat]volume=1.0,alimiter=limit=0.95[aout]")
    fc.append("[vcat]format=yuv420p[vout]")

    inputs = []
    for st, d in clips:
        inputs += ["-ss", f"{st:.2f}", "-t", f"{d:.2f}", "-i", src_path]
    cmd = ([FFMPEG, "-y"] + inputs +
           ["-filter_complex", ";".join(fc),
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", out_path])
    print(f"[{name}] {n} clips, entrances: {kinds}")
    subprocess.run(cmd, check=True)
    return out_path


def build_clean_montage(name, src, clips, target_name=None):
    """Hard-cut montage: no transition FX, no audio fades — dialogue stays
    at full volume. Only the final clip fades to black."""
    src_path = os.path.join(ASSETS, src)
    out_path = os.path.join(ASSETS, f"{target_name or name}.mp4")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 500_000:
        print(f"[{name}] already rendered, skipping")
        return out_path
    n = len(clips)
    fc, vl, al = [], [], []
    for i, (st, d) in enumerate(clips):
        last = i == n - 1
        fst = f"{d - 1.6:.2f}" if last else "0"
        vf = (",fade=t=out:st=" + fst + ":d=1.6:color=black") if last else ""
        af = (",afade=t=out:st=" + fst + ":d=1.6") if last else ""
        fc.append(f"[{i}:v]setpts=PTS-STARTPTS,"
                  f"scale=1920:1080:force_original_aspect_ratio=decrease,"
                  f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,"
                  f"format=yuv420p{vf}[v{i}]")
        vl.append(f"[v{i}]")
        fc.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=48000,"
                  f"aformat=sample_fmts=fltp:channel_layouts=stereo{af}[a{i}]")
        al.append(f"[a{i}]")
    fc.append("".join(vl) + f"concat=n={n}:v=1:a=0[vcat]")
    fc.append("".join(al) + f"concat=n={n}:v=0:a=1[acat]")
    fc.append("[acat]alimiter=limit=0.95[aout]")
    fc.append("[vcat]format=yuv420p[vout]")
    inputs = []
    for st, d in clips:
        inputs += ["-ss", f"{st:.2f}", "-t", f"{d:.2f}", "-i", src_path]
    cmd = ([FFMPEG, "-y"] + inputs +
           ["-filter_complex", ";".join(fc),
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", out_path])
    print(f"[{name}] {n} clips, clean hard cuts")
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def main():
    segs = [build_segment(*s) for s in SEGMENTS]
    concat_list = os.path.join(ASSETS, "concat.txt")
    with open(concat_list, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(ASSETS, "doomsday_breakdown.mp4")
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", "-movflags", "+faststart", final,
    ], check=True)
    print("FINAL:", final, f"{probe_duration(final):.1f}s")


if __name__ == "__main__":
    main()
