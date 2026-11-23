"""Poll LibreHardwareMonitor web server, log temps/load to monitor_log.csv."""
import json, time, urllib.request, csv, os, sys

URL = "http://localhost:8085/data.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor_log.csv")
DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 300
INTERVAL = 2.0

def fetch():
    with urllib.request.urlopen(URL, timeout=5) as r:
        return json.load(r)

def find_sensors(root, path=""):
    out = {}
    def walk(o, trail):
        if isinstance(o, dict):
            sid = o.get("SensorId")
            if sid and o.get("Type"):
                out[(trail, o.get("Text",""), o.get("Type",""))] = o.get("Value","")
            t = o.get("Text","")
            for c in o.get("Children", []):
                walk(c, trail + "/" + t if t else trail)
        elif isinstance(o, list):
            for c in o: walk(c, trail)
    walk(root, path)
    return out

def parse_temp(v):
    try: return float(str(v).replace("°C","C").replace("\xc2\xb0C","C").split()[0])
    except: return None

def parse_pct(v):
    try: return float(str(v).replace("%",""))
    except: return None

def parse_w(v):
    try: return float(str(v).replace("W",""))
    except: return None

new = not os.path.exists(OUT)
f = open(OUT, "a", newline="")
w = csv.writer(f)
if new:
    w.writerow(["time","cpu_package_c","core_max_c","cpu_load_pct","cpu_power_w","gpu_power_w"])

t0 = time.time()
while time.time() - t0 < DURATION:
    try:
        s = find_sensors(fetch())
        pkg = core = load = cpow = gpow = None
        for (trail, name, typ), val in s.items():
            key = (trail + name).lower()
            if typ == "Temperature":
                if name == "CPU Package": pkg = parse_temp(val)
                if name == "Core Max": core = parse_temp(val)
            elif typ == "Load" and name == "CPU Total": load = parse_pct(val)
            elif typ == "Power":
                if "package" in name.lower(): cpow = parse_w(val)
                if "gpu" in key: gpow = parse_w(val)
        w.writerow([time.strftime("%H:%M:%S"), pkg, core, load, cpow, gpow])
        f.flush()
    except Exception as e:
        w.writerow([time.strftime("%H:%M:%S"), "ERR", str(e)[:40], "", "", ""])
        f.flush()
    time.sleep(INTERVAL)
f.close()
print("monitor done ->", OUT)
