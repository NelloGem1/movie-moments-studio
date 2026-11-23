"""Re-upload longer versions of the 3 too-short videos, then delete the shorts."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from youtube_api import get_service_mm
import mm_upload as U

MM_DIR = U.MM_DIR
ASSETS = U.ASSETS

# old (too-short) video IDs to delete after replacements are live
OLD = {
    "Terrifier 3 (2024) — Christmas Movie Edit.mp4": "QswBWpu9KoY",
    "The Red One (2024) — Christmas Movie Edit.mp4": "S1u1Ts5yJi4",
    "Violent Night (2022) — Christmas Movie Edit.mp4": "NoKdCN5OuKc",
}


def main():
    svc = get_service_mm()
    new_ids = {}
    for fname, old_id in OLD.items():
        path = os.path.join(MM_DIR, fname)
        if not os.path.exists(path):
            print("missing:", fname, flush=True)
            continue
        import build_video as _b
        dur = _b.probe_duration(path)
        if dur < 100:
            print(f"SKIP too short ({dur:.0f}s < 100s):", fname, flush=True)
            continue
        title = os.path.splitext(fname)[0]
        print("uploading replacement:", title, flush=True)
        body = {
            "snippet": {
                "title": title,
                "description": U.DESC,
                "tags": U.TAGS,
                "categoryId": "24",
            },
            "status": {"privacyStatus": "public",
                       "selfDeclaredMadeForKids": False},
        }
        media = MediaFileUpload(path, chunksize=-1, resumable=True)
        req = svc.videos().insert(part="snippet,status", body=body,
                                  media_body=media)
        resp = None
        while resp is None:
            _, resp = req.next_chunk()
        vid = resp["id"]
        new_ids[fname] = vid
        tp = U.thumb_for(title)
        if tp:
            try:
                svc.thumbnails().set(
                    videoId=vid,
                    media_body=MediaIoBaseUpload(open(tp, "rb"),
                                                 mimetype="image/jpeg")).execute()
            except Exception as e:
                print("  thumb fail:", repr(e)[:120], flush=True)
        print("  OK:", f"https://youtu.be/{vid}", flush=True)
        time.sleep(5)

    print("=== deleting old short uploads ===", flush=True)
    for fname, old_id in OLD.items():
        try:
            svc.videos().delete(id=old_id).execute()
            print("  deleted:", old_id, "<-", fname, flush=True)
        except Exception as e:
            print("  del ERR:", old_id, repr(e)[:150], flush=True)
        time.sleep(2)
    print("=== replace done ===", flush=True)


if __name__ == "__main__":
    main()
