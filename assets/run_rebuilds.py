"""Auto-resume wrapper: run rebuild_all -> rebuild_special -> thumb_fix,
retrying every 2h while YouTube's daily upload quota is exhausted."""
import os, subprocess, sys, time

ASSETS = os.path.dirname(os.path.abspath(__file__))
QUOTA = os.path.join(ASSETS, "QUOTA_STOP")
PY = sys.executable


def quota_hit():
    return os.path.exists(QUOTA)


def run(script):
    if quota_hit():
        os.remove(QUOTA)
    subprocess.run([PY, script], cwd=ASSETS)
    return quota_hit()


def main():
    for attempt in range(30):  # up to ~60h of retries
        print(f"[wrapper] attempt {attempt+1}", flush=True)
        if run("rebuild_special.py"):
            print("[wrapper] quota exhausted, sleeping 2h", flush=True)
            time.sleep(7200)
            continue
        if run("rebuild_all.py"):
            print("[wrapper] quota exhausted, sleeping 2h", flush=True)
            time.sleep(7200)
            continue
        subprocess.run([PY, "thumb_fix.py"], cwd=ASSETS)
        print("[wrapper] all done", flush=True)
        return
    print("[wrapper] gave up after 30 attempts", flush=True)


if __name__ == "__main__":
    main()
