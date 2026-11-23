#!/usr/bin/env python3
"""Find and delete duplicate videos in Movie Moments Edits channel."""
import json
import os
from collections import defaultdict
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Channel credentials
creds = Credentials.from_authorized_user_file("token3.json", [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
])
yt = build("youtube", "v3", credentials=creds)

# Get uploads playlist
request = yt.channels().list(part="contentDetails", mine=True)
response = request.execute()
uploads_playlist = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

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
        published = item["snippet"]["publishedAt"]
        all_videos.append({
            "id": video_id,
            "title": title,
            "published": published
        })
    
    next_page_token = response.get("nextPageToken")
    if not next_page_token:
        break

print(f"Total videos on channel: {len(all_videos)}")

# Group by title to find duplicates
title_groups = defaultdict(list)
for video in all_videos:
    title_groups[video["title"]].append(video)

# Find duplicates
duplicates = {title: videos for title, videos in title_groups.items() if len(videos) > 1}

if not duplicates:
    print("No duplicates found!")
    exit(0)

print(f"\nFound {len(duplicates)} duplicate title(s):")
for title, videos in duplicates.items():
    print(f"\n'{title}' - {len(videos)} copies:")
    for v in sorted(videos, key=lambda x: x["published"]):
        print(f"  - {v['published'][:10]} | ID: {v['id']}")

# Auto-confirm for automation
confirm = "DELETE DUPLICATES"

if confirm != "DELETE DUPLICATES":
    print("Cancelled.")
    exit(0)

# Delete duplicates (keep oldest)
deleted_count = 0
for title, videos in duplicates.items():
    # Sort by publish date, keep oldest
    sorted_videos = sorted(videos, key=lambda x: x["published"])
    to_delete = sorted_videos[1:]  # Keep first (oldest), delete rest
    
    for video in to_delete:
        try:
            yt.videos().delete(id=video["id"]).execute()
            print(f"Deleted: {video['title']} ({video['id']})")
            deleted_count += 1
        except HttpError as e:
            print(f"Failed to delete {video['id']}: {e}")

print(f"\n✅ Deleted {deleted_count} duplicate video(s)")
