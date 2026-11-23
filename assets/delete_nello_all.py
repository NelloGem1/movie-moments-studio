#!/usr/bin/env python3
"""Check and delete all videos in Nello Gem channel."""
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Try backup credentials first
try:
    creds = Credentials.from_authorized_user_file("token2.json", [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.upload"
    ])
    yt = build("youtube", "v3", credentials=creds)
except:
    # Fall back to original
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

# Confirmation
print("\n" + "="*60)
print("⚠️  WARNING: This will PERMANENTLY DELETE all videos!")
print("="*60)

confirm = input("Type 'DELETE ALL' to proceed: ")

if confirm != "DELETE ALL":
    print("Cancelled.")
    exit(0)

# Delete all videos
deleted_count = 0
failed_count = 0

for video in all_videos:
    try:
        yt.videos().delete(id=video["id"]).execute()
        print(f"✅ Deleted: {video['title']}")
        deleted_count += 1
    except HttpError as e:
        print(f"❌ Failed to delete {video['title']}: {e}")
        failed_count += 1

print(f"\n{'='*60}")
print(f"✅ Deleted: {deleted_count} videos")
print(f"❌ Failed: {failed_count} videos")
print(f"{'='*60}")
