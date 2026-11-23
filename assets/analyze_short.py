#!/usr/bin/env python3
"""Download and analyze reference Short video."""
import subprocess
import os
import sys

# Configuration
VIDEO_URL = "https://www.youtube.com/watch?v=pRjeLiW1t2M"
OUTPUT_DIR = "/tmp/reference_analysis"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "reference_short.mp4")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_video(url, output_path):
    """Download video using yt-dlp."""
    cmd = [
        "/home/neilh/venv/bin/yt-dlp",
        "--merge-output-format", "mp4",
        "-o", output_path,
        url
    ]
    print(f"Downloading: {url}")
    print(f"Output: {output_path}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Download successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def get_video_info(video_path):
    """Get video metadata using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate",
        "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        import json
        info = json.loads(result.stdout)
        return info
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None

def extract_frames(video_path, output_dir, interval=1):
    """Extract frames for visual analysis."""
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{interval}",
        "-q:v", "2",
        os.path.join(output_dir, "frame_%04d.jpg")
    ]
    print(f"Extracting frames to {output_dir}...")
    subprocess.run(cmd, check=True)

def analyze_audio(video_path):
    """Analyze audio characteristics."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate",
        "-of", "json",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        import json
        info = json.loads(result.stdout)
        return info
    except Exception as e:
        print(f"Error analyzing audio: {e}")
        return None

def main():
    print("=" * 60)
    print("REFERENCE SHORT VIDEO ANALYSIS")
    print("=" * 60)
    print(f"URL: {VIDEO_URL}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Download video
    if not download_video(VIDEO_URL, OUTPUT_FILE):
        print("Failed to download video")
        sys.exit(1)
    
    # Get video info
    print("\n" + "=" * 60)
    print("VIDEO METADATA")
    print("=" * 60)
    info = get_video_info(OUTPUT_FILE)
    if info:
        format_info = info.get("format", {})
        print(f"Duration: {format_info.get('duration', 'N/A')}s")
        print(f"Size: {format_info.get('size', 'N/A')} bytes")
        print(f"Bit rate: {format_info.get('bit_rate', 'N/A')}")
        
        streams = info.get("streams", [])
        for stream in streams:
            if stream.get("codec_type") == "video":
                print(f"\nVideo Stream:")
                print(f"  Codec: {stream.get('codec_name')}")
                print(f"  Resolution: {stream.get('width')}x{stream.get('height')}")
                print(f"  Frame rate: {stream.get('r_frame_rate')}")
            elif stream.get("codec_type") == "audio":
                print(f"\nAudio Stream:")
                print(f"  Codec: {stream.get('codec_name')}")
                print(f"  Sample rate: {stream.get('sample_rate')}")
                print(f"  Channels: {stream.get('channels')}")
    
    # Extract frames for analysis
    print("\n" + "=" * 60)
    print("EXTRACTING FRAMES FOR VISUAL ANALYSIS")
    print("=" * 60)
    frames_dir = os.path.join(OUTPUT_DIR, "frames")
    extract_frames(OUTPUT_FILE, frames_dir, interval=2)  # Every 2 seconds
    
    # Count frames
    frame_count = len([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
    print(f"Extracted {frame_count} frames")
    print(f"Frames saved to: {frames_dir}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Video saved to: {OUTPUT_FILE}")
    print(f"Frames saved to: {frames_dir}")
    print("\nNext: Review frames to analyze editing style, pacing, and effects")

if __name__ == "__main__":
    main()
