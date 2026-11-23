#!/usr/bin/env python3
"""Delete all videos in Nello Gem channel using new API key."""
import json
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Use new token4.json
creds = Credentials.from_authorized_user_file("token4.json", [
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
print(f"Checking for videos...")

# Get all videos
all_videos = []
next_page_token = None

while True:
    request = yt.playlistItems().list(
        part="snippet",
        playlistId=uploads_playlist,
        maxResults=50,
        pageToken=next_page_token
    )
    response = request.execute()
    
    for item in response["items"]:
        video_id = item["snippet"]["resourceId"]["videoId"]
        title = item["snippet"]["title"]
        all_videos.append({
            "id": video_id,
            "title": title
        })
    
    next_page_token = response.get("nextPageToken")
    if not next_page_token:
        break

print(f"Found {len(all_videos)} videos")

if not all_videos:
    print("Channel is already empty - no videos to delete")
    exit(0)

print("\nVideos to be deleted:")
for i, v in enumerate(all_videos[:10], 1):
    print(f"  {i}. {v['title']}")
if len(all_videos) > 10:
    print(f"  ... and {len(all_videos) - 10} more")

# Auto-confirm for automation
print("\n" + "="*60)
print("Deleting all videos...")
print("="*60)

# Delete all videos
deleted_count = 0
failed_count = 0

for i, video in enumerate(all_videos, 1):
    try:
        yt.videos().delete(id=video["id"]).execute()
        print(f"[{i}/{len(all_videos)}] Deleted: {video['title']}")
        deleted_count += 1
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
        
    except HttpError as e:
        if e.resp.status == 403:
            print(f"[{i}/{len(all_videos)}] Quota exceeded - stopping")
            print(f"Deleted {deleted_count} videos before quota limit")
            break
        else:
            print(f"[{i}/{len(all_videos)}] Failed to delete {video['title']}: {e}")
            failed_count += 1
    except Exception as e:
        print(f"[{i}/{len(all_videos)}] Error deleting {video['title']}: {e}")
        failed_count += 1

print(f"\n{'='*60}")
print(f"Deleted: {deleted_count} videos")
print(f"Failed: {failed_count} videos")
print(f"{'='*60}")

if deleted_count < len(all_videos):
    print(f"\nNote: {len(all_videos) - deleted_count} videos remaining")
    print("You may need to run this script again later for remaining videos")
