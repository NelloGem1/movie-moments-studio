import os, time, glob

DIR = r"C:\Users\neilh\Downloads\REVIEW_ALL"
TOTAL = 69

def stats():
    mp4s = glob.glob(os.path.join(DIR, "*.mp4"))
    parts = glob.glob(os.path.join(DIR, "*.part")) + glob.glob(os.path.join(DIR, "*.f*"))
    size = sum(os.path.getsize(f) for f in mp4s + parts if os.path.exists(f))
    gb = size / 1e9
    pct = min(100, len(mp4s) / TOTAL * 100)
    return len(mp4s), gb, pct

while True:
    n, gb, pct = stats()
    bar = "#" * int(pct // 2.5) + "-" * (40 - int(pct // 2.5))
    os.system("cls")
    print("=" * 46)
    print("  NELLO GEM — VIDEO DOWNLOAD PROGRESS")
    print("=" * 46)
    print(f"  [{bar}] {pct:5.1f}%")
    print(f"  Videos : {n} / {TOTAL}")
    print(f"  Size   : {gb:.2f} GB")
    print(f"  Folder : {DIR}")
    print("=" * 46)
    print("  Leave this window open — it updates live.")
    print("  Close it anytime; download keeps running.")
    time.sleep(5)
