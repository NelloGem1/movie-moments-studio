"""Find and download 1080p+ official-trailer sources for low-res y2008 files.
Saves as <name>_hd.mp4 next to the original; logs results to hd_upgrade.log."""
import os, re, subprocess, sys, json

ASSETS = os.path.dirname(os.path.abspath(__file__))
Y08 = os.path.join(ASSETS, "y2008")
LOG = os.path.join(ASSETS, "hd_upgrade.log")

JOBS = {
    "hulk":     "The Incredible Hulk 2008 official trailer",
    "im":       "Iron Man 2008 official trailer",
    "indiana":  "Indiana Jones and the Kingdom of the Crystal Skull official trailer",
    "kungfu":   "Kung Fu Panda 2008 official trailer",
    "mamma_mia": "Mamma Mia 2008 official trailer",
    "walle":    "WALL-E 2008 official trailer",
}

FF = "ffprobe"

def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")

def height(path):
    r = subprocess.run([FF, "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=height", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return 0

def search(query):
    r = subprocess.run(["yt-dlp", "--no-playlist", "--flat-playlist",
                        "--print", "%(id)s", f"ytsearch3:{query}"],
                       capture_output=True, text=True, timeout=120)
    return [l.strip() for l in r.stdout.splitlines() if l.strip()]

def best_url(vid):
    r = subprocess.run(["yt-dlp", "--no-playlist", "-F",
                        f"https://www.youtube.com/watch?v={vid}"],
                       capture_output=True, text=True, timeout=120)
    best = None
    for line in r.stdout.splitlines():
        m = re.match(r"\s*\d+\s+\S+\s+(\d+)x(\d+)", line)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
            if h >= 1080 and (best is None or h > best[0]):
                best = (h, w, vid)
    return best

def download(vid, out):
    r = subprocess.run(["yt-dlp", "--no-playlist",
                        "-f", "bv*[height>=1080][ext=mp4]+ba[ext=m4a]/bv*[height>=1080]+ba/b[height>=1080]/b",
                        "--merge-output-format", "mp4",
                        "-o", out,
                        f"https://www.youtube.com/watch?v={vid}"],
                       capture_output=True, text=True, timeout=900)
    return r.returncode == 0 and os.path.exists(out)

def main():
    for name, query in JOBS.items():
        src = os.path.join(Y08, name + ".mp4")
        dst = os.path.join(Y08, name + "_hd.mp4")
        if os.path.exists(dst):
            log(name, "already have HD:", height(dst)); continue
        log("===", name, "searching:", query)
        got = False
        for vid in search(query):
            info = best_url(vid)
            if not info:
                log("  ", vid, "no 1080p+"); continue
            h, w, _ = info
            log("  trying", vid, f"{w}x{h}")
            tmp = dst + ".part.mp4"
            if download(vid, tmp):
                hh = height(tmp)
                if hh >= 1080:
                    os.replace(tmp, dst)
                    log("  OK", name, "->", dst, hh, "p")
                    got = True
                    break
                os.remove(tmp)
                log("  downloaded but only", hh, "p — skipped")
            else:
                log("  download failed for", vid)
        if not got:
            log("!!", name, "NO HD SOURCE FOUND — keeping original")

if __name__ == "__main__":
    main()
    log("=== hd upgrade pass done ===")
