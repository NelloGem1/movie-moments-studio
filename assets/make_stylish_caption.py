#!/usr/bin/env python3
"""Create video with stylish captions and better timing."""
import os
import subprocess
import sys
import whisper

# Configuration
TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/dune_part_two.mp4")
OUTPUT_DIR = os.path.expanduser("~/Downloads")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "STYLISH_CAPTION_Short.mp4")
TEMP_DIR = "/tmp/stylish_caption"
WHISPER_MODEL = "base"
START_TIME = 60
DURATION = 60
TIMING_OFFSET = 1.0  # Increase offset to 1.0 second

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

def extract_segment_audio(trailer_path, output_path, start_time, duration):
    """Extract only the segment we need."""
    cmd = [
        "ffmpeg", "-y",
        "-i", trailer_path,
        "-ss", str(start_time),
        "-t", str(duration),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_path
    ]
    run_cmd(cmd, f"Extracting audio segment")

def transcribe_and_fix(audio_path):
    """Transcribe and fix common typos."""
    print(f"\n{'='*60}")
    print("TRANSCRIBING WITH WHISPER + FIXING TYPOS")
    print(f"{'='*60}")
    
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(audio_path, language="en")
    
    segments = []
    for segment in result["segments"]:
        text = segment["text"].strip()
        
        # Fix common typos
        text = text.replace("tradeings", "trainings")
        text = text.replace("Tradeings", "Trainings")
        text = text.replace("TRADEINGS", "TRAININGS")
        
        # Adjust timestamps with larger offset
        adjusted_start = segment["start"] + START_TIME + TIMING_OFFSET
        adjusted_end = segment["end"] + START_TIME + TIMING_OFFSET
        
        segments.append({
            "start": adjusted_start,
            "end": adjusted_end,
            "text": text
        })
    
    print(f"\nTranscription complete: {len(segments)} segments")
    print("\nSample dialogue (with 1.0s offset):")
    for i, seg in enumerate(segments[:5], 1):
        print(f"  {i}. [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
    
    return segments

def create_stylish_srt(segments, output_path, start_time, duration):
    """Create SRT with perfect timing."""
    with open(output_path, "w", encoding="utf-8") as f:
        caption_num = 1
        for seg in segments:
            # Convert to relative timestamps
            relative_start = seg["start"] - start_time
            relative_end = seg["end"] - start_time
            
            # Only include if within duration
            if relative_start >= 0 and relative_start < duration:
                def format_time(seconds):
                    hours = int(seconds // 3600)
                    minutes = int((seconds % 3600) // 60)
                    secs = int(seconds % 60)
                    millis = int((seconds % 1) * 1000)
                    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
                
                f.write(f"{caption_num}\n")
                f.write(f"{format_time(relative_start)} --> {format_time(relative_end)}\n")
                f.write(f"{seg['text']}\n\n")
                caption_num += 1
    
    print(f"Stylish SRT created: {output_path}")

def create_stylish_video(trailer_path, srt_path, output_path, start_time, duration):
    """Create video with stylish captions."""
    print(f"\nCreating video from {start_time}s for {duration}s")
    
    # Create square crop
    base_video = os.path.join(TEMP_DIR, "base.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", trailer_path,
        "-vf", "crop=ih:ih:(iw-ih)/2:0,scale=1080:1080",
        "-t", str(duration),
        "-ss", str(start_time),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
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
        "-pix_fmt", "yuv420p",
        "-an",
        graded_video
    ]
    run_cmd(cmd, "Applying cinematic grading")
    
    # Burn subtitles with STYLISH formatting
    # Using impact font, yellow color, larger size, shadow, and box background
    subtitle_video = os.path.join(TEMP_DIR, "subtitle.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", graded_video,
        "-vf", f"subtitles={srt_path}:force_style='FontName=Impact,FontSize=36,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=3,Shadow=2,Alignment=2,MarginV=80,BackColour=&H80000000'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",
        subtitle_video
    ]
    run_cmd(cmd, "Burning stylish subtitles")
    
    # Extract audio
    audio_path = os.path.join(TEMP_DIR, "audio.aac")
    cmd = [
        "ffmpeg", "-y",
        "-i", trailer_path,
        "-t", str(duration),
        "-ss", str(start_time),
        "-vn",
        "-c:a", "aac", "-b:a", "192k",
        audio_path
    ]
    run_cmd(cmd, "Extracting audio")
    
    # Combine video and audio
    cmd = [
        "ffmpeg", "-y",
        "-i", subtitle_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    run_cmd(cmd, "Combining video and audio")

def main():
    print("=" * 60)
    print("STYLISH CAPTION VIDEO CREATOR")
    print("=" * 60)
    print(f"Trailer: {TRAILER_PATH}")
    print(f"Segment: {START_TIME}s - {START_TIME+DURATION}s")
    print(f"Timing offset: +{TIMING_OFFSET}s")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Check if trailer exists
    if not os.path.exists(TRAILER_PATH):
        print(f"Error: Trailer not found: {TRAILER_PATH}")
        sys.exit(1)
    
    # Extract audio segment
    audio_path = os.path.join(TEMP_DIR, "segment_audio.wav")
    extract_segment_audio(TRAILER_PATH, audio_path, START_TIME, DURATION)
    
    # Transcribe and fix typos
    segments = transcribe_and_fix(audio_path)
    
    # Create stylish SRT
    srt_path = os.path.join(TEMP_DIR, "stylish_subtitles.srt")
    create_stylish_srt(segments, srt_path, START_TIME, DURATION)
    
    # Create video with stylish captions
    create_stylish_video(TRAILER_PATH, srt_path, OUTPUT_FILE, START_TIME, DURATION)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANING UP")
    print("=" * 60)
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
    os.rmdir(TEMP_DIR)
    
    print(f"\nStylish Caption Video created: {OUTPUT_FILE}")
    print(f"Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
