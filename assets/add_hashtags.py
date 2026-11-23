"""Add SEO hashtags to every published video's description."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from youtube_api import get_service

svc = get_service()
res = svc.search().list(part="snippet", forMine=True, type="video",
                        maxResults=50).execute()
ids = [it["id"]["videoId"] for it in res["items"]]

SPECIAL = {
    "avengers": ["#AvengersDoomsday", "#Marvel", "#MCU"],
    "dune": ["#Dune", "#DunePart3", "#Arrakis"],
}

def hashtags_for(title):
    tags = ["#MovieEdit", "#TrailerEdit"]
    t = title.lower()
    for key, extra in SPECIAL.items():
        if key in t:
            tags += extra
    # movie name words before year/em-dash
    name = re.split(r"\s*[—(]\s*", title)[0]
    words = re.sub(r"[^A-Za-z0-9 ]", "", name).split()
    tag = "#" + "".join(w.capitalize() for w in words[:4])
    if len(tag) > 2:
        tags.append(tag)
    m = re.search(r"\((\d{4})\)", title)
    if m:
        tags.append(f"#{m.group(1)}")
    return tags

updated = 0
for vid in ids:
    v = svc.videos().list(part="snippet", id=vid).execute()["items"][0]
    sn = v["snippet"]
    desc = sn.get("description", "")
    if "#MovieEdit" in desc:
        continue
    tags = hashtags_for(sn["title"])
    new_desc = desc.rstrip() + "\n\n" + " ".join(tags)
    svc.videos().update(part="snippet",
                        body={"id": vid, "snippet": {
                            "title": sn["title"], "description": new_desc,
                            "tags": sn.get("tags", []),
                            "categoryId": sn.get("categoryId", "24")}}).execute()
    print("updated:", sn["title"][:55], "|", " ".join(tags))
    updated += 1
print("TOTAL UPDATED:", updated)
