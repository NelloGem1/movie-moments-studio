#!/usr/bin/env python3
"""Create a creative square-format Short video."""
import os
import subprocess
import sys

# Configuration
TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/dune_part_two.mp4")
if not os.path.exists(TRAILER_PATH):
    # Fallback to dune_2021 if part two doesn't exist
    TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/dune_2021.mp4")
OUTPUT_DIR = os.path.expanduser("~/Downloads")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "CREATIVE_SHORT_Dune.mp4")
TEMP_DIR = "/tmp/creative_short"

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
        print("Success")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Failed: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)

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

def create_square_short(video_path, output_path, duration=120):
    """Create square 1:1 format Short with cinematic editing."""
    # Get original duration
    total_duration = get_duration(video_path)
    print(f"Original duration: {total_duration:.2f}s")
    
    # Select best segment (middle of trailer usually has peak action)
    start_time = max(0, (total_duration - duration) / 2)
    print(f"Extracting {duration}s from {start_time:.2f}s")
    
    # Create square crop (1080x1080) with cinematic effects
    # Step 1: Crop to square and scale
    square_crop = os.path.join(TEMP_DIR, "square_crop.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", "crop=ih:ih:(iw-ih)/2:0,scale=1080:1080",
        "-t", str(duration),
        "-ss", str(start_time),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        square_crop
    ]
    run_cmd(cmd, "Creating square crop")
    
    # Step 2: Apply cinematic color grading (simplified to avoid filter issues)
    graded = os.path.join(TEMP_DIR, "graded.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", square_crop,
        "-vf", "eq=contrast=1.15:saturation=1.25:brightness=-0.02,vignette=PI/4.5:mode=forward",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        graded
    ]
    run_cmd(cmd, "Applying cinematic grading")
    
    # Step 3: Add subtle speed variation (simplified)
    speed_ramped = os.path.join(TEMP_DIR, "speed_ramped.mp4")
    # Simple speed change: slow first 30s, normal middle, fast last 30s
    cmd = [
        "ffmpeg", "-y",
        "-i", graded,
        "-filter_complex",
        "[0:v]split=3[v0][v1][v2];"
        "[v0]trim=0:30,setpts=0.7*(PTS-STARTPTS)[v0s];"
        "[v1]trim=30:90,setpts=PTS-STARTPTS[v1s];"
        "[v2]trim=90:120,setpts=1.3*(PTS-STARTPTS)[v2s];"
        "[v0s][v1s][v2s]concat=n=3:v=1:a=0[v]",
        "-map", "[v]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        speed_ramped
    ]
    run_cmd(cmd, "Adding speed variation")
    
    # Step 4: Extract audio with fade in/out
    audio = os.path.join(TEMP_DIR, "audio.aac")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-t", str(duration),
        "-ss", str(start_time),
        "-vn",
        "-af", "afade=t=in:st=0:d=2,afade=t=out:st=118:d=2",
        "-c:a", "aac", "-b:a", "192k",
        audio
    ]
    run_cmd(cmd, "Extracting audio with fades")
    
    # Step 5: Combine video and audio
    cmd = [
        "ffmpeg", "-y",
        "-i", speed_ramped,
        "-i", audio,
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    run_cmd(cmd, "Combining video and audio")
    
    # Step 6: Skip zoom effect for simplicity, just copy final
    final = output_path
    # Move speed_ramped to final output
    os.rename(speed_ramped, output_path)

def main():
    print("=" * 60)
    print("CREATIVE SQUARE SHORT CREATOR")
    print("=" * 60)
    print(f"Trailer: {TRAILER_PATH}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Check if trailer exists
    if not os.path.exists(TRAILER_PATH):
        print(f"Error: Trailer not found: {TRAILER_PATH}")
        sys.exit(1)
    
    # Create the Short
    create_square_short(TRAILER_PATH, OUTPUT_FILE, duration=120)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANING UP")
    print("=" * 60)
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
    os.rmdir(TEMP_DIR)
    
    print(f"\nShort created: {OUTPUT_FILE}")
    print(f"Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
