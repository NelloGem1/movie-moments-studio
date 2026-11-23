#!/usr/bin/env python3
"""Create a YouTube Short from a movie trailer."""
import os
import subprocess
import sys

# Configuration
TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/avengers_doomsday.mp4")
OUTPUT_DIR = os.path.expanduser("~/Downloads")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SHORT_AvengersDoomsday.mp4")
TEMP_DIR = "/tmp/short_build"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_cmd(cmd, description):
    """Run command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Success")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)

def download_trailer(url, output_path):
    """Download trailer using yt-dlp."""
    # Use full path to yt-dlp in venv
    yt_dlp_path = os.path.expanduser("~/venv/bin/yt-dlp")
    cmd = [
        yt_dlp_path,
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "-o", output_path,
        url
    ]
    run_cmd(cmd, "Downloading trailer")

def get_duration(video_path):
    """Get video duration in seconds."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def create_short(video_path, output_path, duration=55):
    """Create vertical 9:16 Short from horizontal video."""
    # Get original duration
    total_duration = get_duration(video_path)
    print(f"Original duration: {total_duration:.2f}s")
    
    # Select best 55 seconds (middle of video usually has best content)
    start_time = max(0, (total_duration - duration) / 2)
    print(f"Extracting {duration}s from {start_time:.2f}s")
    
    # Create vertical crop with blurred background
    # First, create blurred background
    blurred_bg = os.path.join(TEMP_DIR, "blurred_bg.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:20",
        "-t", str(duration),
        "-ss", str(start_time),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        blurred_bg
    ]
    run_cmd(cmd, "Creating blurred background")
    
    # Create foreground (center crop)
    foreground = os.path.join(TEMP_DIR, "foreground.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"scale=1080:608:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-t", str(duration),
        "-ss", str(start_time),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        foreground
    ]
    run_cmd(cmd, "Creating foreground")
    
    # Extract audio
    audio = os.path.join(TEMP_DIR, "audio.aac")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-t", str(duration),
        "-ss", str(start_time),
        "-vn",
        "-c:a", "aac", "-b:a", "128k",
        audio
    ]
    run_cmd(cmd, "Extracting audio")
    
    # Combine blurred background + foreground + audio
    cmd = [
        "ffmpeg", "-y",
        "-i", blurred_bg,
        "-i", foreground,
        "-i", audio,
        "-filter_complex",
        "[0:v][1:v]overlay=0:0[v]",
        "-map", "[v]",
        "-map", "2:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    run_cmd(cmd, "Combining layers")
    
    # Add text overlay (optional - can be added later)
    # For now, just the clean vertical video

def main():
    print("🎬 YouTube Short Creator")
    print(f"Trailer: {TRAILER_PATH}")
    print(f"Output: {OUTPUT_FILE}")
    
    # Check if trailer exists
    if not os.path.exists(TRAILER_PATH):
        print(f"❌ Trailer not found: {TRAILER_PATH}")
        sys.exit(1)
    
    # Create short from local trailer
    create_short(TRAILER_PATH, OUTPUT_FILE, duration=55)
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
    os.rmdir(TEMP_DIR)
    
    print(f"\n✅ Short created: {OUTPUT_FILE}")
    print(f"📁 Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
