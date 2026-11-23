#!/usr/bin/env python3
"""Check Nello Gem channel status using yt-dlp."""
import subprocess
import json

# Use yt-dlp to check channel videos
channel_url = "https://www.youtube.com/@NelloGem/videos"

print("Checking Nello Gem channel videos...")
print(f"URL: {channel_url}")

# Get video list using yt-dlp
cmd = [
    "/home/neilh/venv/bin/yt-dlp",
    "--flat-playlist",
    "--print-json",
    channel_url
]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0:
        # Parse JSON lines
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    video = json.loads(line)
                    videos.append({
                        "id": video.get("id"),
                        "title": video.get("title"),
                        "url": video.get("url")
                    })
                except:
                    pass
        
        print(f"\nFound {len(videos)} videos")
        
        if videos:
            print("\nVideos:")
            for i, v in enumerate(videos[:10], 1):
                print(f"  {i}. {v['title']} | ID: {v['id']}")
            if len(videos) > 10:
                print(f"  ... and {len(videos) - 10} more")
        else:
            print("Channel is empty - no videos found")
            
    else:
        print(f"Error: {result.stderr}")
        
except subprocess.TimeoutExpired:
    print("Timeout - channel check failed")
except Exception as e:
    print(f"Error: {e}")
