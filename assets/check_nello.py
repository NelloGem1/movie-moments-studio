#!/usr/bin/env python3
"""Check Nello Gem channel videos and analyze content."""
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Nello Gem credentials
creds = Credentials.from_authorized_user_file("token.json", [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload"
])
yt = build("youtube", "v3", credentials=creds)

# Get channel info
request = yt.channels().list(part="contentDetails,snippet", mine=True)
response = request.execute()

if not response["items"]:
    print("No channel found")
    exit(1)

channel = response["items"][0]
channel_title = channel["snippet"]["title"]
uploads_playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]

print(f"Channel: {channel_title}")
print(f"Uploads playlist: {uploads_playlist}")

# Get all videos
all_videos = []
next_page_token = None

while True:
    request = yt.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_playlist,
        maxResults=50,
        pageToken=next_page_token
    )
    response = request.execute()
    
    for item in response["items"]:
        video_id = item["snippet"]["resourceId"]["videoId"]
        title = item["snippet"]["title"]
        published = item["snippet"]["publishedAt"]
        all_videos.append({
            "id": video_id,
            "title": title,
            "published": published
        })
    
    next_page_token = response.get("nextPageToken")
    if not next_page_token:
        break

print(f"\nTotal videos: {len(all_videos)}")
print("\nRecent videos:")
for v in all_videos[:20]:
    print(f"  - {v['published'][:10]} | {v['title']} | ID: {v['id']}")

# Analyze titles for patterns
print("\n=== TITLE ANALYSIS ===")
titles = [v["title"] for v in all_videos]

# Check for common patterns
patterns = {
    "Official Trailer": sum(1 for t in titles if "Official Trailer" in t),
    "Edit": sum(1 for t in titles if "Edit" in t or "edit" in t.lower()),
    "Behind the Scenes": sum(1 for t in titles if "Behind" in t or "BTS" in t),
    "Short": sum(1 for t in titles if "Short" in t or len(t) < 50),
    "Movie": sum(1 for t in titles if "Movie" in t),
    "2024": sum(1 for t in titles if "2024" in t),
    "2025": sum(1 for t in titles if "2025" in t),
}

for pattern, count in patterns.items():
    print(f"{pattern}: {count}")

# Save video list
with open("nello_videos.json", "w") as f:
    json.dump(all_videos, f, indent=2)

print("\nVideo list saved to nello_videos.json")
