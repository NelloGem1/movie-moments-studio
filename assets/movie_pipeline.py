"""End-to-end single-movie pipeline: trailer -> edit -> polish -> thumb -> upload."""
import os, re, subprocess, sys, time, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import make_edit as m
import polish as p
import build_video as b
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from googleapiclient.http import MediaFileUpload
from youtube_api import get_service

ASSETS = b.ASSETS
YT_DIR = os.path.join(ASSETS, "trailers_dl")
os.makedirs(YT_DIR, exist_ok=True)
FF = b.FFMPEG
DONE_LOG = os.path.join(ASSETS, "posted_log.txt")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def already_posted(key):
    if not os.path.exists(DONE_LOG):
        return False
    return key in open(DONE_LOG).read()


def mark_posted(key):
    with open(DONE_LOG, "a") as f:
        f.write(key + "\n")


def get_trailer(movie, year_hint=None):
    """Download official trailer via yt-dlp ytsearch. Returns local path."""
    tag = slug(movie)
    dst = os.path.join(YT_DIR, tag + ".mp4")
    if os.path.exists(dst) and os.path.getsize(dst) > 1_000_000:
        return dst
    q = f"ytsearch1:{movie} official trailer"
    subprocess.run(["yt-dlp", "-f", "bv*[height<=1080]+ba/b[height<=1080]",
                    "--merge-output-format", "mp4", "-o", dst,
                    q, "--no-playlist", "-q", "--no-warnings"],
                   capture_output=True, timeout=300)
    # yt-dlp may append extension weirdly; find result
    if not os.path.exists(dst):
        cands = glob.glob(os.path.join(YT_DIR, tag + "*.mp4"))
        if cands:
            dst = cands[0]
    return dst if os.path.exists(dst) and os.path.getsize(dst) > 500_000 else None


def make_thumb(video, title, subtitle, out):
    """Cinematic gradient thumbnail — DaVinci-style teal/orange grade,
    vignette, film grain, sharpen, and dark gradient bars top & bottom."""
    d = b.probe_duration(video)
    t = d * 0.62
    frame = os.path.join(ASSETS, "_ft.jpg")
    vf = ("eq=contrast=1.14:saturation=1.22:brightness=-0.02,"
          "colorbalance=rs=-0.09:gs=0.03:bs=0.16:rh=0.13:gh=-0.03:bh=-0.13,"
          "unsharp=5:5:0.9,vignette=PI/4.8,noise=alls=5:allf=t")
    subprocess.run([FF, "-y", "-ss", f"{t:.1f}", "-i", video,
                    "-frames:v", "1", "-vf", vf, "-q:v", "2", frame],
                   capture_output=True)
    im = Image.open(frame).convert("RGB")
    w, h = im.size
    import numpy as np
    arr = np.asarray(im).astype(np.float32)
    # cinematic grade: teal shadows / warm highlights (DaVinci-style split)
    lum = arr.mean(axis=2, keepdims=True) / 255.0
    arr[:, :, 0] += (lum[:, :, 0] - 0.35) * 26    # red: warm highlights
    arr[:, :, 2] -= (lum[:, :, 0] - 0.35) * 20    # blue: cool shadows
    arr[:, :, 0] -= (0.35 - lum[:, :, 0]) * 10    # teal shadow tint
    arr[:, :, 2] += (0.35 - lum[:, :, 0]) * 14
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGB")
    # bottom gradient bar
    bh = int(h * 0.22)
    grad = np.linspace(0, 215, bh)[:, None] ** 1.6
    bar = np.zeros((bh, w, 4), np.uint8)
    bar[:, :, 3] = np.broadcast_to(grad.astype(np.uint8), (bh, w))
    im = im.convert("RGBA")
    im.paste(Image.fromarray(bar, "RGBA"), (0, h - bh),
             Image.fromarray(bar, "RGBA"))
    # top subtle gradient
    th = int(h * 0.12)
    tgrad = np.linspace(140, 0, th)[:, None]
    tbar = np.zeros((th, w, 4), np.uint8)
    tbar[:, :, 3] = np.broadcast_to(tgrad.astype(np.uint8), (th, w))
    tbar_img = Image.fromarray(tbar, "RGBA")
    im.paste(tbar_img, (0, 0), tbar_img)
    # soft center glow — subtle warm lift mid-frame
    import numpy as np
    gx, gy = w // 2, int(h * 0.45)
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - gx) ** 2 + (yy - gy) ** 2)
    alpha = np.clip(26 * (1 - dist / (w * 0.55)), 0, 26).astype(np.uint8)
    glow = Image.fromarray(
        np.dstack([np.full((h, w), 255, np.uint8),
                   np.full((h, w), 235, np.uint8),
                   np.full((h, w), 200, np.uint8), alpha]), "RGBA")
    from PIL import ImageFilter
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    im = Image.alpha_composite(im, glow).convert("RGB")
    im.save(out, "JPEG", quality=93)
    os.remove(frame)


def upload(video, thumb, title, desc, tags):
    svc = get_service()
    body = {"snippet": {"title": title, "description": desc,
                        "tags": tags, "categoryId": "24"},
            "status": {"privacyStatus": "public",
                       "selfDeclaredMadeForKids": False}}
    media = MediaFileUpload(video, chunksize=-1, resumable=True)
    req = svc.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    try:
        svc.thumbnails().set(videoId=vid, media_body=MediaFileUpload(
            thumb, mimetype="image/jpeg")).execute()
    except Exception as e:
        print("thumb fail:", e)
    return vid


WHISPER_MODEL = os.path.join(ASSETS, "ggml-tiny.en.bin")


def speech_cuts(src_rel, max_clips=16, return_tail=False, dmax=6.5):
    """Whisper-transcribe trailer, return clips bounded by phrase ends.
    If return_tail, also return start time of the trailer's closing tail
    (after the last spoken cue) for use as an outro clip."""
    import re, numpy as np
    src_path = os.path.join(ASSETS, src_rel)
    srt = os.path.join(ASSETS, "_whisper_tmp")
    # ffmpeg filter args can't contain Windows backslash/drive-colon paths —
    # run with cwd=ASSETS and relative names instead
    r = subprocess.run([FF, "-y", "-v", "error", "-i", src_path, "-vn",
                        "-af", "whisper=model=ggml-tiny.en.bin:language=en:format=srt:destination=_whisper_tmp",
                        "-f", "null", "-"], capture_output=True, timeout=600,
                       cwd=ASSETS)
    if not os.path.exists(srt):
        for f in os.listdir(ASSETS):
            if f.startswith("_whisper_tmp"):
                srt = os.path.join(ASSETS, f); break
    if not os.path.exists(srt):
        return (None, None) if return_tail else None
    txt = open(srt, encoding="utf-8", errors="ignore").read()
    cues = []
    for m in re.finditer(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", txt):
        s = int(m[1])*3600+int(m[2])*60+int(m[3])+int(m[4])/1000
        e = int(m[5])*3600+int(m[6])*60+int(m[7])+int(m[8])/1000
        cues.append((s, e))
    cues.sort()
    T = b.probe_duration(src_path)
    cuts = sorted(set(round(e + 0.15, 2) for s, e in cues))
    cuts = [c for c in cuts if 2 < c < T - 2]
    if len(cuts) < 4:
        return (None, None) if return_tail else None
    pcm = np.frombuffer(subprocess.run(
        [FF, "-v", "error", "-i", src_path, "-vn", "-ac", "1", "-ar", "22050",
         "-f", "s16le", "-"], capture_output=True).stdout,
        dtype=np.int16).astype(np.float32)
    sr = 22050
    def energy(a, bb):
        i, j = int(a*sr), int(bb*sr)
        return float(np.sqrt(np.mean(pcm[i:j]**2))) if j > i else 0
    clips, ci = [], 0
    while ci < len(cuts)-1 and len(clips) < max_clips:
        best = None
        for cj in range(ci+1, len(cuts)):
            d = cuts[cj] - cuts[ci]
            if d < 3.0:
                continue
            if d > dmax:
                break
            e = energy(cuts[ci], cuts[cj])
            sc_ = e * (0.6 + 0.4*d/6)
            if best is None or sc_ > best[0]:
                best = (sc_, cj, d)
        if not best:
            ci += 1; continue
        clips.append((round(cuts[ci], 2), round(best[2], 2)))
        ci = best[1]
    if len(clips) < 6:
        return (None, None) if return_tail else None
    tail = None
    if return_tail:
        last_end = max(e for _, e in cues)
        if 2.0 < T - last_end <= 14.0:
            tail = round(last_end + 0.1, 2)
    return (clips, tail) if return_tail else clips


def _finish_single(name, segs):
    """Concat segs -> base -> minimal score -> final (clean audio style)."""
    concat = os.path.join(ASSETS, f"concat_{name}.txt")
    with open(concat, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    base = os.path.join(ASSETS, f"{name}_base.mp4")
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", concat,
                    "-c", "copy", "-movflags", "+faststart", base], check=True)
    total = b.probe_duration(base)
    import score as sc
    s = sc.Score(total)
    s.timpani(total-1.5, 55, 0.9)
    s.taiko(total-1.5, f0=85, f1=38, dec=1.0, vol=1.0)
    s.boom(total-1.5, 1.0)
    sp = os.path.join(ASSETS, f"{name}_score.wav")
    s.write(sp)
    fc = ("[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
          "volume=0.9[tr];"
          "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
          "volume=0.5[mus];"
          "[tr][mus]amix=inputs=2:duration=first:dropout_transition=0,"
          "lowshelf=f=120:g=5,equalizer=f=90:w=150:g=4,"
          "loudnorm=I=-13:TP=-1.5:LRA=11[aout]")
    final = os.path.join(ASSETS, f"{name}.mp4")
    subprocess.run([FF, "-y", "-i", base, "-i", sp, "-filter_complex", fc,
                    "-map", "0:v", "-map", "[aout]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", final], check=True,
                   capture_output=True)


def process_movie(movie, year, extra_src=None):
    """Full pipeline for one movie. Returns youtube url or None."""
    key = f"{year}:{slug(movie)}"
    if already_posted(key):
        print("skip posted:", key); return None
    name = f"edit_{year}_{slug(movie)[:20]}"
    out = os.path.join(ASSETS, name + ".mp4")
    if os.path.exists(out) and os.path.getsize(out) > 1_000_000:
        print("exists:", out)
    else:
        src = extra_src or get_trailer(movie)
        if not src:
            print("NO TRAILER:", movie, flush=True); return None
        rel = os.path.relpath(src, ASSETS)
        tag = "mv_" + slug(movie)[:20]
        try:
            clips, tail = speech_cuts(rel, return_tail=True)
            if not clips:
                wins = m.energy_windows(rel, count=18, win=3.8,
                                        min_gap=5.5,
                                        seed=hash(movie) % 5000)
                clips = [(round(t, 2), round(d, 2)) for t, d in wins]
                tail = None
            if tail:
                T = b.probe_duration(src)
                clips = clips + [(tail, round(T - tail, 2))]
            seg = b.build_clean_montage(tag, rel, clips,
                                        target_name=f"edit_{tag}.mp4")
            _finish_single(name, [seg])
        except Exception as e:
            print("BUILD FAIL:", movie, e, flush=True); return None
        # make_edit names output <out_name>.mp4 — it already is `out`
    polished = p.polish(out)
    os.replace(polished, out)
    thumb = os.path.join(ASSETS, f"thumb_{year}_{slug(movie)[:20]}.jpg")
    make_thumb(out, movie, f"{year} Official Trailer Edit", thumb)
    title = f"{movie} ({year}) — The Official Trailer Edit"
    desc = (f"{movie} ({year}) — the most intense moments from the official "
            f"trailer, cut into one cinematic edit with original audio and a "
            f"custom orchestral score. No narration, just the movie.")
    tags = [movie.lower(), str(year), "trailer edit", "official trailer",
            "movie edit", "cinematic edit"]
    hashtags = ["#MovieEdit", "#TrailerEdit", f"#{slug(movie).replace('_', '')}",
                f"#{year}"]
    desc += "\n\n" + " ".join(hashtags)
    try:
        vid = upload(out, thumb, title, desc, tags)
        mark_posted(key)
        print("LIVE:", f"https://youtu.be/{vid}", "|", title, flush=True)
        return vid
    except Exception as e:
        print("UPLOAD FAIL:", movie, e, flush=True); return None


if __name__ == "__main__":
    year = sys.argv[1]
    movies = sys.argv[2].split("|")
    for mv in movies:
        process_movie(mv.strip(), year)
        time.sleep(3)
