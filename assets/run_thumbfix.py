"""Rerun thumb_fix passes every 20min until a full pass lands with zero
rate-limits (or ~12 attempts)."""
import os, subprocess, sys, time

ASSETS = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(ASSETS, "thumb_fix.log")
PY = sys.executable


def last_pass_rate_limited():
    if not os.path.exists(LOG):
        return True
    txt = open(LOG, encoding="utf-8", errors="ignore").read()
    # find last pass header
    idx = txt.rfind("=== thumb fix pass")
    if idx == -1:
        return True
    tail = txt[idx:]
    return "RATE LIMITED" in tail or "GAVE UP" in tail


def main():
    for i in range(12):
        print(f"[thumbs] pass {i+1}", flush=True)
        subprocess.run([PY, "thumb_fix.py", "--now"], cwd=ASSETS)
        if not last_pass_rate_limited():
            print("[thumbs] all thumbnails updated", flush=True)
            return
        print("[thumbs] still throttled, sleeping 20min", flush=True)
        time.sleep(1200)
    print("[thumbs] gave up after 12 passes", flush=True)


if __name__ == "__main__":
    main()
