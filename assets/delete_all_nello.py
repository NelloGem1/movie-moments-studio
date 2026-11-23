"""Delete all videos from Nello Gem YouTube channel."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import youtube_api

def delete_all_videos():
    yt = youtube_api.get_service()
    
    # Get channel's uploads playlist
    ch = yt.channels().list(part='contentDetails', mine=True).execute()
    uploads_playlist = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    print(f"Channel uploads playlist: {uploads_playlist}")
    
    # Get all video IDs
    video_ids = []
    page_token = None
    while True:
        resp = yt.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist,
            maxResults=50,
            pageToken=page_token
        ).execute()
        
        for item in resp.get('items', []):
            video_ids.append(item['snippet']['resourceId']['videoId'])
        
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    
    print(f"Found {len(video_ids)} videos to delete")
    
    # Delete each video
    deleted = 0
    failed = 0
    for vid in video_ids:
        try:
            yt.videos().delete(id=vid).execute()
            deleted += 1
            print(f"Deleted: {vid} ({deleted}/{len(video_ids)})")
        except Exception as e:
            failed += 1
            print(f"Failed to delete {vid}: {e}")
    
    print(f"\nDone: {deleted} deleted, {failed} failed")

if __name__ == "__main__":
    delete_all_videos()
