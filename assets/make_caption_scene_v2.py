#!/usr/bin/env python3
"""Create improved caption scene with better audio and caption."""
import os
import subprocess
import sys

# Configuration
TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/dune_part_two.mp4")
OUTPUT_DIR = os.path.expanduser("~/Downloads")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "CAPTION_SCENE_Short_v2.mp4")
TEMP_DIR = "/tmp/caption_scene_v2"

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

def create_improved_caption_scene(trailer_path, output_path, duration=60):
    """Create improved caption scene."""
    # Select a dramatic scene
    start_time = 60
    print(f"Extracting {duration}s from {start_time}s")
    
    # Create square crop with space for caption (bottom 20%)
    base_video = os.path.join(TEMP_DIR, "base.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", trailer_path,
        "-vf", "crop=ih:ih:(iw-ih)/2:0,scale=1080:864,pad=1080:1080:0:216:black",
        "-t", str(duration),
        "-ss", str(start_time),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",
        base_video
    ]
    run_cmd(cmd, "Creating base scene")
    
    # Apply cinematic grading
    graded_video = os.path.join(TEMP_DIR, "graded.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", base_video,
        "-vf", "eq=contrast=1.15:saturation=1.25:brightness=-0.02,vignette=PI/4.5:mode=forward",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",
        graded_video
    ]
    run_cmd(cmd, "Applying cinematic grading")
    
    # Add better caption - larger, more prominent
    caption_text = "FATE IS WRITTEN IN SPICE"
    caption_video = os.path.join(TEMP_DIR, "captioned.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", graded_video,
        "-vf", f"drawtext=text='{caption_text}':fontsize=64:fontcolor=yellow:borderw=3:bordercolor=black:x=(w-text_w)/2:y=864+80:alpha='if(lt(t,3),0,if(lt(t,4),(t-3)/1,if(lt(t,{duration-4}),1,if(lt(t,{duration-3}),({duration-3}-t)/1,0))))'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",
        caption_video
    ]
    run_cmd(cmd, "Adding caption")
    
    # Extract audio with proper volume
    audio_path = os.path.join(TEMP_DIR, "audio.aac")
    cmd = [
        "ffmpeg", "-y",
        "-i", trailer_path,
        "-t", str(duration),
        "-ss", str(start_time),
        "-vn",
        "-af", "volume=1.5,afade=t=in:st=0:d=2,afade=t=out:st=58:d=2",
        "-c:a", "aac", "-b:a", "192k",
        audio_path
    ]
    run_cmd(cmd, "Extracting audio")
    
    # Combine video and audio with proper settings
    cmd = [
        "ffmpeg", "-y",
        "-i", caption_video,
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]
    run_cmd(cmd, "Combining video and audio")

def main():
    print("=" * 60)
    print("IMPROVED CAPTION SCENE CREATOR")
    print("=" * 60)
    print(f"Trailer: {TRAILER_PATH}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Check if trailer exists
    if not os.path.exists(TRAILER_PATH):
        print(f"Error: Trailer not found: {TRAILER_PATH}")
        sys.exit(1)
    
    # Create the improved caption scene
    create_improved_caption_scene(TRAILER_PATH, OUTPUT_FILE, duration=60)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANING UP")
    print("=" * 60)
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
    os.rmdir(TEMP_DIR)
    
    print(f"\nImproved Caption Scene created: {OUTPUT_FILE}")
    print(f"Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
