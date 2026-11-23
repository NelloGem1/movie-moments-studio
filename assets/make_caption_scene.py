#!/usr/bin/env python3
"""Create a scene perfect for caption placement, then add caption."""
import os
import subprocess
import sys

# Configuration
TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/dune_part_two.mp4")
OUTPUT_DIR = os.path.expanduser("~/Downloads")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "CAPTION_SCENE_Short.mp4")
TEMP_DIR = "/tmp/caption_scene"

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

def create_caption_scene(trailer_path, output_path, duration=60):
    """Create a scene perfect for caption placement."""
    # Get video info
    total_duration = get_duration(trailer_path)
    print(f"Video duration: {total_duration:.2f}s")
    
    # Select a dramatic scene (usually middle of trailer)
    # For Dune, let's pick around 60-90 seconds where action peaks
    start_time = 60  # Good dramatic moment
    print(f"Extracting {duration}s from {start_time}s")
    
    # Create square crop with space for caption
    # We'll leave bottom 25% clear for caption
    base_video = os.path.join(TEMP_DIR, "base.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", trailer_path,
        "-vf", "crop=ih:ih:(iw-ih)/2:0,scale=1080:810,pad=1080:1080:0:270:black",
        "-t", str(duration),
        "-ss", str(start_time),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        base_video
    ]
    run_cmd(cmd, "Creating base scene with caption space")
    
    # Apply cinematic grading
    graded_video = os.path.join(TEMP_DIR, "graded.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", base_video,
        "-vf", "eq=contrast=1.2:saturation=1.3:brightness=-0.03,vignette=PI/4:mode=forward,colorbalance=rs=-0.08:gs=-0.04:bs=0.1:rm=0.08:gm=0.03:bm=-0.08",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        graded_video
    ]
    run_cmd(cmd, "Applying cinematic grading")
    
    # Add dramatic caption in the reserved space
    # Caption will be centered in the bottom black bar
    caption_text = "THE DESERT AWAITS"
    caption_video = os.path.join(TEMP_DIR, "captioned.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", graded_video,
        "-vf", f"drawtext=text='{caption_text}':fontsize=72:fontcolor=white:borderw=4:bordercolor=black:x=(w-text_w)/2:y=810+100:alpha='if(lt(t,2),0,if(lt(t,3),(t-2)/1,if(lt(t,{duration-3}),1,if(lt(t,{duration-2}),({duration-2}-t)/1,0))))'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        caption_video
    ]
    run_cmd(cmd, "Adding dramatic caption")
    
    # Extract audio with cinematic feel
    audio_path = os.path.join(TEMP_DIR, "audio.aac")
    cmd = [
        "ffmpeg", "-y",
        "-i", trailer_path,
        "-t", str(duration),
        "-ss", str(start_time),
        "-vn",
        "-af", "afade=t=in:st=0:d=3,afade=t=out:st=57:d=3,volume=1.2",
        "-c:a", "aac", "-b:a", "192k",
        audio_path
    ]
    run_cmd(cmd, "Extracting audio")
    
    # Combine video and audio
    cmd = [
        "ffmpeg", "-y",
        "-i", caption_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    run_cmd(cmd, "Combining video and audio")

def main():
    print("=" * 60)
    print("CAPTION SCENE CREATOR")
    print("=" * 60)
    print(f"Trailer: {TRAILER_PATH}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Check if trailer exists
    if not os.path.exists(TRAILER_PATH):
        print(f"Error: Trailer not found: {TRAILER_PATH}")
        sys.exit(1)
    
    # Create the caption scene
    create_caption_scene(TRAILER_PATH, OUTPUT_FILE, duration=60)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANING UP")
    print("=" * 60)
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
    os.rmdir(TEMP_DIR)
    
    print(f"\nCaption Scene created: {OUTPUT_FILE}")
    print(f"Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
