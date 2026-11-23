"""Watch MOVIE_MOMENTS and auto-upload new finished videos every 5 min."""
import subprocess, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
while True:
    r = subprocess.run([sys.executable, os.path.join(HERE, "mm_upload.py")],
                       capture_output=True, text=True)
    print(r.stdout, flush=True)
    if r.stderr:
        print(r.stderr[-500:], flush=True)
    time.sleep(300)
