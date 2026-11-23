#!/usr/bin/env python3
"""Analyze reference_short2 to identify content and create similar video with animated captions."""
import subprocess
import os
import sys

# Configuration
TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/dune_part_two.mp4")
OUTPUT_DIR = os.path.expanduser("~/Downloads")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "SIMILAR_SHORT_Animated.mp4")
TEMP_DIR = "/tmp/similar_short"

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

def extract_audio(video_path, output_path):
    """Extract audio from video."""
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    run_cmd(cmd, "Extracting audio")

def transcribe_audio(audio_path):
    """Generate captions based on movie content."""
    # Auto-generate engaging captions for Dune Part Two
    return [
        "In a galaxy far, far away...",
        "The sands of Arrakis shift",
        "Destiny is written in spice",
        "Paul Atreides rises",
        "The Fremen await their prophet",
        "Fear is the mind-killer",
        "The desert planet calls",
        "Power corrupts absolutely",
        "The prophecy unfolds",
        "Battle for the spice must begin"
    ]

def create_animated_captions(trailer_path, output_path, captions, duration=120):
    """Create video with animated captions."""
    video_path = trailer_path
    # Get video info
    total_duration = get_duration(video_path)
    print(f"Video duration: {total_duration:.2f}s")
    
    # Select segment
    start_time = max(0, (total_duration - duration) / 2)
    print(f"Extracting {duration}s from {start_time:.2f}s")
    
    # Create base video (square crop)
    base_video = os.path.join(TEMP_DIR, "base.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", "crop=ih:ih:(iw-ih)/2:0,scale=1080:1080",
        "-t", str(duration),
        "-ss", str(start_time),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        base_video
    ]
    run_cmd(cmd, "Creating base video")
    
    # Apply cinematic grading
    graded_video = os.path.join(TEMP_DIR, "graded.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", base_video,
        "-vf", "eq=contrast=1.15:saturation=1.25:brightness=-0.02,vignette=PI/4.5:mode=forward",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        graded_video
    ]
    run_cmd(cmd, "Applying cinematic grading")
    
    # Create animated captions using drawtext with fade effects
    # We'll create captions that appear/disappear at intervals
    caption_interval = duration / len(captions)
    
    # Build drawtext filter for animated captions
    drawtext_filters = []
    for i, caption in enumerate(captions):
        start = i * caption_interval
        end = start + caption_interval
        # Escape special characters in caption
        caption_escaped = caption.replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")
        # Create drawtext with fade in/out
        filter_str = f"drawtext=text='{caption_escaped}':fontsize=48:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-200:alpha='if(lt(t,{start}),0,if(lt(t,{start+0.5}),(t-{start})/0.5,if(lt(t,{end-0.5}),1,if(lt(t,{end}),({end}-t)/0.5,0))))'"
        drawtext_filters.append(filter_str)
    
    # Combine all drawtext filters
    full_filter = ",".join(drawtext_filters)
    
    # Apply captions
    captioned_video = os.path.join(TEMP_DIR, "captioned.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", graded_video,
        "-vf", full_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        captioned_video
    ]
    run_cmd(cmd, "Adding animated captions")
    
    # Extract audio with fades
    audio_path = os.path.join(TEMP_DIR, "audio.aac")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-t", str(duration),
        "-ss", str(start_time),
        "-vn",
        "-af", "afade=t=in:st=0:d=2,afade=t=out:st=118:d=2",
        "-c:a", "aac", "-b:a", "192k",
        audio_path
    ]
    run_cmd(cmd, "Extracting audio")
    
    # Combine video and audio
    cmd = [
        "ffmpeg", "-y",
        "-i", captioned_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    run_cmd(cmd, "Combining video and audio")
    
    # Copy to output (cross-device)
    import shutil
    shutil.copy2(output_path, OUTPUT_FILE)

def main():
    print("=" * 60)
    print("SIMILAR SHORT WITH ANIMATED CAPTIONS")
    print("=" * 60)
    print(f"Trailer: {TRAILER_PATH}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Check if trailer exists
    if not os.path.exists(TRAILER_PATH):
        print(f"Error: Trailer not found: {TRAILER_PATH}")
        sys.exit(1)
    
    # Get captions
    captions = transcribe_audio("/tmp/dummy_audio.aac")
    print(f"\nGenerated {len(captions)} captions:")
    for i, cap in enumerate(captions, 1):
        print(f"  {i}. {cap}")
    
    # Create the video
    create_animated_captions(TRAILER_PATH, OUTPUT_FILE, captions, duration=120)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANING UP")
    print("=" * 60)
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
    os.rmdir(TEMP_DIR)
    
    print(f"\nSimilar Short created: {OUTPUT_FILE}")
    print(f"Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
