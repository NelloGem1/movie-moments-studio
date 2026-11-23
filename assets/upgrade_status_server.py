"""Live progress page for the local video upgrade pass on port 51590."""
import os, re, json
from http.server import BaseHTTPRequestHandler, HTTPServer

ASSETS = os.path.dirname(os.path.abspath(__file__))
STATUS = os.path.join(ASSETS, "local_upgrade_status.txt")
DONE = os.path.join(ASSETS, "local_upgrade_done.txt")
LOG = os.path.join(ASSETS, "local_upgrade.log")
REVIEW = os.path.expanduser(r"~\Downloads\REVIEW_ALL")

PAGE = """<!doctype html><html><head><meta charset=utf-8>
<meta http-equiv=refresh content=3><title>Nello Gem Upgrade</title>
<style>
body{background:#0b0e14;color:#e8ecf4;font-family:Segoe UI,Arial;margin:0;
display:flex;flex-direction:column;align-items:center;padding:60px 20px}
h1{font-size:22px;letter-spacing:2px;color:#f5b942}
.bar{width:640px;height:34px;background:#1a2030;border-radius:8px;overflow:hidden;
margin:18px 0;position:relative}
.fill{height:100%;background:linear-gradient(90deg,#0e7490,#f5b942);
width:__PCT__%;transition:width .5s}
.pct{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
font-weight:700;font-size:15px}
.sub{color:#8b96ad;font-size:14px;margin-top:6px}
.log{width:640px;margin-top:26px;background:#111827;border-radius:8px;padding:14px;
font-family:Consolas,monospace;font-size:12px;color:#9fb3d9;white-space:pre-wrap;
max-height:300px;overflow:auto}
</style></head><body>
<h1>&#127916; NELLO GEM — VIDEO UPGRADE</h1>
<div class=bar><div class=fill></div><div class=pct>__PCT__%</div></div>
<div class=sub>__DONE__ / __TOTAL__ upgraded &nbsp;•&nbsp; __CUR__</div>
<div class=log>__LOG__</div>
</body></html>"""


def stats():
    denom = 60  # non-skipped files in the pass
    total = len([f for f in os.listdir(REVIEW) if f.endswith(".mp4")])
    done = 0
    cur = "starting…"
    if os.path.exists(STATUS):
        s = open(STATUS, encoding="utf-8", errors="ignore").read().strip()
        m = re.match(r"(\d+)/(\d+)\s+(\S+)\s+(.*)", s)
        if m:
            cur = f"{m.group(3)}: {m.group(4)}"
    if os.path.exists(DONE):
        done = len(open(DONE, encoding="utf-8").read().splitlines())
    pct = min(100, round(done / denom * 100))
    logtxt = ""
    if os.path.exists(LOG):
        lines = open(LOG, encoding="utf-8", errors="ignore").read().splitlines()
        logtxt = "\n".join(lines[-12:])
    return pct, done, denom, cur, logtxt


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        pct, done, total, cur, logtxt = stats()
        html = (PAGE.replace("__PCT__", str(pct))
                    .replace("__DONE__", str(done))
                    .replace("__TOTAL__", str(total))
                    .replace("__CUR__", cur.replace("<", "&lt;"))
                    .replace("__LOG__", logtxt.replace("<", "&lt;")))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8321), H).serve_forever()
