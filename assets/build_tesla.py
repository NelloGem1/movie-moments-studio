"""Build Tesla life-story video: Ken Burns pans over archival photos + TTS narration."""
import os, subprocess, math
from PIL import Image

ASSETS = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(ASSETS, "tesla_photos")
FFMPEG = r"C:\Users\neilh\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.1-full_build\bin\ffmpeg.exe"
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")
MASTER_W, MASTER_H = 2560, 1440
OUT_W, OUT_H = 1920, 1080

def probe_duration(path):
    out = subprocess.check_output(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], text=True)
    return float(out.strip())

def make_master(src, dst):
    """Cover-fit image onto 2560x1440 canvas; portrait anchored upper-center."""
    im = Image.open(src).convert("RGB")
    w, h = im.size
    scale = max(MASTER_W / w, MASTER_H / h)
    nw, nh = int(w * scale) + 1, int(h * scale) + 1
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (MASTER_W, MASTER_H))
    x = (MASTER_W - nw) // 2
    # anchor portraits toward top so faces aren't cropped
    y = int((MASTER_H - nh) * (0.35 if h > w else 0.5))
    canvas.paste(im, (x, y))
    canvas.save(dst, quality=92)

def build_segment(idx, photo, voice, pan_dir):
    """One narration segment: slow pan across photo master, audio = voice."""
    voice_path = os.path.join(ASSETS, voice)
    master = os.path.join(ASSETS, f"tmaster_{idx:02d}.jpg")
    if not os.path.exists(master):
        make_master(os.path.join(PHOTOS, photo), master)
    out_path = os.path.join(ASSETS, f"tesla_seg_{idx:02d}.mp4")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 500_000:
        print(f"seg {idx} exists, skip"); return out_path
    dur = probe_duration(voice_path) + 0.5
    # pan: x moves across slack (in_w-out_w)=640, y across 360; alternate dirs
    if pan_dir == 0:   # left -> right, slight downward
        xexpr = "(in_w-out_w)*t/DUR"; yexpr = "(in_h-out_h)*0.5"
    elif pan_dir == 1: # right -> left, slight upward
        xexpr = "(in_w-out_w)*(1-t/DUR)"; yexpr = "(in_h-out_h)*(1-0.5*t/DUR)"
    else:              # center-out zoom-ish drift
        xexpr = "(in_w-out_w)*(0.5+0.4*sin(3.14159*t/DUR))"; yexpr = "(in_h-out_h)*0.5"
    vf = (f"crop={OUT_W}:{OUT_H}:x='{xexpr}':y='{yexpr}',"
          f"fade=t=in:st=0:d=0.6,fade=t=out:st={dur-0.7:.2f}:d=0.6,"
          f"format=yuv420p")
    vf = vf.replace("t/DUR", f"t/{dur:.2f}")
    cmd = [FFMPEG, "-y", "-loop", "1", "-t", f"{dur:.2f}", "-i", master,
           "-i", voice_path,
           "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-r", "30",
           "-c:a", "aac", "-b:a", "192k",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
           "-shortest", "-movflags", "+faststart", out_path]
    print(f"seg {idx}: {photo} dur={dur:.1f}s dir={pan_dir}")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path

# (voice_idx, photo, pan_dir)
SEGS = [
    (1,  "tesla_01.jpg", 0),
    (2,  "tesla_00.jpg", 1),
    (3,  "tesla_04.jpg", 0),
    (4,  "tesla_19.jpg", 1),
    (5,  "tesla_05.jpg", 2),
    (6,  "tesla_06.jpg", 0),
    (7,  "tesla_06.jpg", 1),
    (8,  "tesla_07.jpg", 0),
    (9,  "tesla_07.jpg", 1),
    (10, "tesla_14.jpg", 0),
    (11, "tesla_13.jpg", 1),
    (12, "tesla_16.jpg", 0),
    (13, "tesla_04.jpg", 2),
    (14, "tesla_20.jpg", 1),
    (15, "tesla_01.jpg", 2),
]

def main():
    segs = [build_segment(i, p, f"voice_tesla{v}.mp3", d)
            for i, (v, p, d) in enumerate(SEGS, 1)]
    concat = os.path.join(ASSETS, "concat_tesla.txt")
    with open(concat, "w") as f:
        for p in segs:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")
    final = os.path.join(ASSETS, "tesla_story.mp4")
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat,
                    "-c", "copy", "-movflags", "+faststart", final], check=True)
    print("FINAL:", final, f"{probe_duration(final):.1f}s")

if __name__ == "__main__":
    main()
