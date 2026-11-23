"""Live Movie Moments dashboard — serves HTML at http://127.0.0.1:8790/"""
import os, re, glob, subprocess, time
from http.server import BaseHTTPRequestHandler, HTTPServer

MM_DIR = os.path.expanduser("~/Downloads/MOVIE_MOMENTS")
ASSETS = os.path.dirname(os.path.abspath(__file__))
DONE = os.path.join(ASSETS, "mm_uploaded.txt")
FACTORY = os.path.join(ASSETS, "mm_factory.py")
MIN_DUR = 100  # seconds — matches upload guard
PORT = 8790


def probe_dur(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def fmt_dur(s):
    return f"{int(s//60)}:{int(s%60):02d}"


def load_queue():
    """Parse QUEUE tuples from mm_factory.py: (slug, query, movie, year)."""
    out = []
    try:
        src = open(FACTORY, encoding="utf-8").read()
        for m in re.finditer(r'\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', src):
            out.append(m.groups())
    except Exception:
        pass
    return out


def norm(s):
    return s.lower().replace("’", "'").replace("‘", "'")


def page():
    # ---- pending files in MOVIE_MOMENTS ----
    pending_files = sorted(glob.glob(os.path.join(MM_DIR, "*.mp4")))
    rows = []
    pending_names = []
    for f in pending_files:
        name = os.path.basename(f)
        pending_names.append(norm(name))
        sz = os.path.getsize(f) / 1e6
        age = time.time() - os.path.getmtime(f)
        dur = probe_dur(f)
        ok = dur >= MIN_DUR
        badge = '<span class="ok">READY</span>' if ok else \
                f'<span class="warn">{fmt_dur(dur)} - under {fmt_dur(MIN_DUR)}, rebuild</span>'
        copying = '<span class="dim">copying...</span>' if age < 90 else ""
        rows.append(f"<tr><td>{name}</td><td>{sz:.0f} MB</td>"
                    f"<td>{fmt_dur(dur)}</td><td>{badge} {copying}</td></tr>")
    pending = "".join(rows) or '<tr><td colspan="4" class="dim">folder empty - all published</td></tr>'

    # ---- published log ----
    done_lines = []
    if os.path.exists(DONE):
        done_lines = [l.strip() for l in open(DONE, encoding="utf-8") if l.strip()]
    done_norm = [norm(l) for l in done_lines]
    recent = "".join(f"<li>{l}</li>" for l in done_lines[-8:][::-1])

    # ---- pipeline data: every queued movie with live status ----
    queue = load_queue()
    qrows = []
    counts = {"LIVE": 0, "PENDING": 0, "BUILT": 0, "QUEUED": 0, "SKIP": 0}
    for slug, query, movie, year in queue:
        built_f = os.path.join(ASSETS, f"mm_{slug}.mp4")
        built = os.path.exists(built_f)
        tag = norm(f"{movie} ({year})")
        if any(tag in d for d in done_norm):
            status, cls = "LIVE", "ok"
        elif any(norm(movie) in p for p in pending_names):
            status, cls = "PENDING", "warn"
        elif built:
            status, cls = "BUILT", "info"
        else:
            status, cls = "QUEUED", "dim"
        counts[status] = counts.get(status, 0) + 1
        qrows.append(f'<tr><td class="dim">{slug}</td><td>{movie} ({year})</td>'
                     f'<td><span class="{cls}">{status}</span></td></tr>')
    queue_tbl = "".join(qrows)

    # ---- workers ----
    try:
        r = subprocess.run(["pgrep", "-af", "python"],
                           capture_output=True, text=True, timeout=10)
        workers = len([line for line in r.stdout.splitlines() if line.strip()])
    except Exception:
        workers = "?"

    total_q = len(queue)
    done_q = counts.get("LIVE", 0)

    return f"""<!doctype html><html><head><meta charset=utf-8>
<meta http-equiv=refresh content=10>
<title>Movie Moments — Live</title>
<style>
body{{background:#0d0f12;color:#e8e8e8;font-family:Consolas,monospace;max-width:1100px;margin:30px auto;padding:0 16px}}
h1{{color:#f5c542;font-size:22px}} h2{{color:#7fd4c1;font-size:15px;margin-top:28px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
td,th{{padding:5px 10px;border-bottom:1px solid #262a30;text-align:left}}
th{{color:#8b93a1;font-weight:normal}}
.ok{{color:#5fd07a}} .warn{{color:#f5a623}} .dim{{color:#6b7280}} .info{{color:#6aa9ff}}
.card{{background:#14181d;border:1px solid #262a30;border-radius:8px;padding:14px 18px}}
li{{margin:3px 0;font-size:13px}}
.big{{font-size:30px;color:#f5c542}}
.pill{{display:inline-block;background:#1c2128;border:1px solid #2c333d;border-radius:10px;padding:2px 10px;margin:2px;font-size:12px}}
.bar{{height:8px;background:#1c2128;border-radius:4px;overflow:hidden;margin-top:6px}}
.bar>div{{height:100%;background:linear-gradient(90deg,#5fd07a,#f5c542)}}
</style></head><body>
<h1>MOVIE MOMENTS EDITS — LIVE DATA</h1>
<div class=card>
<span class=big>{len(done_lines)}</span> published &nbsp;·&nbsp;
<span class=big>{len(pending_files)}</span> pending &nbsp;·&nbsp;
<span class=big>{workers}</span> processes &nbsp;·&nbsp;
<span class=dim>min length {fmt_dur(MIN_DUR)} · refresh 10s</span>
<div class=bar><div style="width:{done_q*100//max(total_q,1)}%"></div></div>
<div class=dim style="font-size:12px;margin-top:4px">catalog progress: {done_q}/{total_q} movies live</div>
</div>

<h2>PENDING IN FOLDER ({len(pending_files)})</h2>
<table><tr><th>Video</th><th>Size</th><th>Length</th><th>Status</th></tr>{pending}</table>

<h2>PIPELINE DATA — every queued movie</h2>
<table><tr><th>slug</th><th>Movie</th><th>Status</th></tr>{queue_tbl}</table>
<div>
<span class="pill ok">LIVE {counts.get('LIVE',0)}</span>
<span class="pill warn">PENDING {counts.get('PENDING',0)}</span>
<span class="pill info">BUILT {counts.get('BUILT',0)}</span>
<span class="pill dim">QUEUED {counts.get('QUEUED',0)}</span>
</div>

<h2>PUBLISHED (latest)</h2><ul>{recent}</ul>
</body></html>"""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = page().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"Live dashboard: http://127.0.0.1:{PORT}/")
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
