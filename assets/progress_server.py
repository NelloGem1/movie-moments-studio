import os, glob, json, time
from http.server import HTTPServer, BaseHTTPRequestHandler

DIR = r"C:\Users\neilh\Downloads\REVIEW_ALL"
TOTAL = 69
PAGE = b"""<!doctype html><html><head><meta charset=utf-8>
<title>Nello Gem Progress</title><style>
body{background:#0d0d0f;color:#eee;font-family:Consolas,monospace;
display:flex;flex-direction:column;align-items:center;justify-content:center;
height:100vh;margin:0}
.bar{width:640px;height:44px;background:#222;border-radius:10px;overflow:hidden;
border:1px solid #444}
.fill{height:100%;background:linear-gradient(90deg,#e50914,#ff6b35);
transition:width .8s}
.txt{margin-top:18px;font-size:22px}
.sub{margin-top:8px;color:#999}
h1{font-size:20px;letter-spacing:2px;color:#fff}
</style></head><body>
<h1>NELLO GEM &mdash; VIDEO DOWNLOAD</h1>
<div class=bar><div class=fill id=f></div></div>
<div class=txt id=t></div><div class=sub id=s></div>
<script>
async function tick(){
 const r=await fetch('/progress.json');const d=await r.json();
 document.getElementById('f').style.width=d.pct+'%';
 document.getElementById('t').textContent=d.pct.toFixed(1)+'%  -  '+d.n+' / '+d.total+' videos';
 document.getElementById('s').textContent=d.gb.toFixed(2)+' GB downloaded';
 if(d.done)document.title='DONE - Nello Gem';
}
tick();setInterval(tick,3000);
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/progress.json"):
            mp4s = glob.glob(os.path.join(DIR, "*.mp4"))
            parts = glob.glob(os.path.join(DIR, "*.part")) + \
                glob.glob(os.path.join(DIR, "*.f*"))
            files = [f for f in mp4s + parts if os.path.exists(f)]
            size = sum(os.path.getsize(f) for f in files)
            n = len(mp4s)
            body = json.dumps({
                "pct": min(100, n / TOTAL * 100),
                "n": n, "total": TOTAL,
                "gb": size / 1e9,
                "done": n >= TOTAL,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(PAGE)

    def log_message(self, *a):
        pass


HTTPServer(("127.0.0.1", 8321), H).serve_forever()
