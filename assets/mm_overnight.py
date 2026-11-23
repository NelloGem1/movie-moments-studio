"""Overnight orchestrator:
1. Wait for mm_fix6.py to finish rebuilding short videos.
2. Rebuild Eight Crazy Nights (its assets were wiped mid-fix — fix6's
   scanner only picks up existing finals, so it needs a direct build).
3. Launch mm_par.py so fixed videos get staged into MOVIE_MOMENTS and
   the remaining queue keeps building.
Log: mm_overnight.log
"""
import os, sys, time, subprocess, glob

ASSETS = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ASSETS, "mm_overnight.log")
PY = sys.executable
PYW = PY.replace("python.exe", "pythonw.exe")
if not os.path.exists(PYW):
    PYW = PY


def log(*a):
    line = time.strftime("[%Y-%m-%d %H:%M:%S]") + " " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def fix6_running():
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
         "Where-Object {$_.CommandLine -match 'mm_fix6'} | Measure-Object).Count"],
        capture_output=True, text=True, timeout=30)
    try:
        return int(r.stdout.strip()) > 0
    except ValueError:
        return False


def main():
    log("=== mm overnight orchestrator started ===")
    # wait for fix6 (max 5h)
    for _ in range(300):
        if not fix6_running():
            break
        time.sleep(60)
    else:
        log("fix6 still running after 5h — proceeding anyway")
    log("fix6 finished — rebuilding Eight Crazy Nights")
    try:
        sys.path.insert(0, ASSETS)
        import mm_fix6
        mm_fix6.build("8_crazy", "Eight Crazy Nights", "2002")
    except Exception as e:
        log("8_crazy build ERR:", repr(e)[:200])
    # any other slugs whose final is missing but should exist?
    log("launching mm_par.py")
    subprocess.Popen([PYW, os.path.join(ASSETS, "mm_par.py")],
                     cwd=os.path.dirname(ASSETS),
                     creationflags=subprocess.CREATE_NO_WINDOW
                     if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)
    log("=== orchestrator done ===")


if __name__ == "__main__":
    main()
