"""Check all Movie Moments uploads for blocks/restrictions via API."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from youtube_api import get_service_mm

svc = get_service_mm()
ch = svc.channels().list(part="contentDetails", mine=True).execute()["items"][0]
up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
pl = svc.playlistItems().list(part="snippet", playlistId=up,
                             maxResults=50).execute()
ids = [it["snippet"]["resourceId"]["videoId"] for it in pl.get("items", [])]
titles = {it["snippet"]["resourceId"]["videoId"]: it["snippet"]["title"]
          for it in pl.get("items", [])}

resp = svc.videos().list(part="status,contentDetails,snippet",
                         id=",".join(ids)).execute()
issues = 0
for v in resp.get("items", []):
    vid = v["id"]
    st, cd = v["status"], v.get("contentDetails", {})
    flags = []
    if st.get("uploadStatus") not in ("processed",):
        flags.append(f"UPLOAD={st.get('uploadStatus')}")
    if st.get("privacyStatus") != "public":
        flags.append(f"PRIVACY={st.get('privacyStatus')}")
    rr = cd.get("regionRestriction", {})
    if rr.get("blocked"):
        flags.append(f"BLOCKED-IN:{','.join(rr['blocked'][:5])}")
    if cd.get("contentRating", {}).get("ytRating") == "yt14":
        flags.append("AGE-RESTRICTED")
    name = titles.get(vid, vid)
    if flags:
        issues += 1
        print(f"!! {name}\n    {'; '.join(flags)}")
    else:
        print(f"OK {name}  [{st.get('uploadStatus')}/{st.get('privacyStatus')}]")
print(f"\n{issues} video(s) with issues out of {len(resp.get('items', []))}")
print("NOTE: copyright claims are NOT visible via API - check YouTube Studio > Copyright")
