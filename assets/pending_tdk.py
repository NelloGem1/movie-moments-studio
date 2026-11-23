"""Upload user-approved up_tdk.mp4 when YouTube upload quota resets,
then delete the old Sinners video."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import movie_pipeline as mp
from youtube_api import get_service

VIDEO = os.path.join(mp.ASSETS, "up_tdk.mp4")
THUMB = os.path.join(mp.ASSETS, "up_thumb_tdk.jpg")
OLD = "4PBAOhgx26E"
TITLE = "The Dark Knight (2008) — The Official Trailer Edit"
DESC = ("The Dark Knight (2008) — the most intense moments from the official "
        "trailer, cut into one cinematic edit with original audio. "
        "No narration, just the movie.\n\n"
        "#MovieEdit #TrailerEdit #TheDarkKnight #2008")
TAGS = ["the dark knight", "2008", "trailer edit", "official trailer",
        "movie edit", "cinematic edit"]

for i in range(48):  # retry up to ~24h
    try:
        vid = mp.upload(VIDEO, THUMB, TITLE, DESC, TAGS)
        get_service().videos().delete(id=OLD).execute()
        print("LIVE: https://youtu.be/" + vid, flush=True)
        break
    except Exception as e:
        s = str(e)
        if "exceeded the number of videos" in s:
            print(f"[{i}] still capped, retry in 30min", flush=True)
            time.sleep(1800)
        else:
            print("ERR:", repr(e)[:200], flush=True)
            time.sleep(300)
