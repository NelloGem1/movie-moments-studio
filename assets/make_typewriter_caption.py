#!/usr/bin/env python3
"""Create typewriter effect captions like reference_short2."""
import os
import subprocess
import sys
import whisper

# Configuration
TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/dune_part_two.mp4")
OUTPUT_DIR = os.path.expanduser("~/Downloads")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "TYPEWRITER_CAPTION_Short.mp4")
TEMP_DIR = "/tmp/typewriter_caption"
WHISPER_MODEL = "base"
START_TIME = 60
DURATION = 60

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

def transcribe_segment(audio_path):
    """Transcribe the segment."""
    print(f"\n{'='*60}")
    print("TRANSCRIBING WITH WHISPER")
    print(f"{'='*60}")
    
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(audio_path, language="en")
    
    segments = []
    for segment in result["segments"]:
        text = segment["text"].strip()
        
        # Fix common typos
        text = text.replace("tradeings", "trainings")
        text = text.replace("Tradeings", "Trainings")
        
        # Adjust timestamps
        adjusted_start = segment["start"] + START_TIME
        adjusted_end = segment["end"] + START_TIME
        
        segments.append({
            "start": adjusted_start,
            "end": adjusted_end,
            "text": text
        })
    
    print(f"\nTranscription complete: {len(segments)} segments")
    for i, seg in enumerate(segments[:5], 1):
        print(f"  {i}. [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
    
    return segments

def create_typewriter_captions(video_path, segments, output_path, start_time, duration):
    """Create video with typewriter effect captions."""
    print(f"\nCreating video from {start_time}s for {duration}s")
    
    # Create square crop
    base_video = os.path.join(TEMP_DIR, "base.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
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
    
    # Create typewriter effect using drawtext with alpha animation
    # This creates text that appears letter by letter
    typewriter_video = os.path.join(TEMP_DIR, "typewriter.mp4")
    
    # Build filter for typewriter effect
    # We'll use drawtext with alpha that increases over time
    drawtext_filters = []
    
    for i, seg in enumerate(segments):
        # Calculate relative time within the video
        rel_start = seg["start"] - start_time
        rel_end = seg["end"] - start_time
        duration_seg = rel_end - rel_start
        
        # Skip if outside our duration
        if rel_start < 0 or rel_start >= duration:
            continue
        
        # Typewriter speed: ~10 characters per second
        text = seg["text"]
        char_count = len(text)
        type_duration = char_count / 10.0  # 10 chars per second
        
        # Create alpha expression for typewriter effect
        # Alpha goes from 0 to 1 over type_duration, then stays 1 until rel_end
        alpha_expr = f"if(lt(t,{rel_start}),0,if(lt(t,{rel_start+type_duration}),(t-{rel_start})/{type_duration},if(lt(t,{rel_end}),1,0)))"
        
        # Escape text for drawtext
        text_escaped = text.replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")
        
        # Drawtext with typewriter alpha
        filter_str = f"drawtext=text='{text_escaped}':fontsize=42:fontcolor=white:borderw=2:bordercolor=black:x=(w-text_w)/2:y=(h-text_h)/2:alpha='{alpha_expr}'"
        drawtext_filters.append(filter_str)
    
    # Combine all drawtext filters
    if drawtext_filters:
        full_filter = ",".join(drawtext_filters)
        cmd = [
            "ffmpeg", "-y",
            "-i", graded_video,
            "-vf", full_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-an",
            typewriter_video
        ]
        run_cmd(cmd, "Adding typewriter effect captions")
    else:
        # No captions, just copy graded video
        import shutil
        shutil.copy2(graded_video, typewriter_video)
    
    # Extract audio
    audio_path = os.path.join(TEMP_DIR, "audio.aac")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
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
        "-i", typewriter_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path
    ]
    run_cmd(cmd, "Combining video and audio")

def main():
    print("=" * 60)
    print("TYPEWRITER CAPTION VIDEO CREATOR")
    print("=" * 60)
    print(f"Trailer: {TRAILER_PATH}")
    print(f"Segment: {START_TIME}s - {START_TIME+DURATION}s")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Check if trailer exists
    if not os.path.exists(TRAILER_PATH):
        print(f"Error: Trailer not found: {TRAILER_PATH}")
        sys.exit(1)
    
    # Extract audio segment
    audio_path = os.path.join(TEMP_DIR, "segment_audio.wav")
    extract_segment_audio(TRAILER_PATH, audio_path, START_TIME, DURATION)
    
    # Transcribe
    segments = transcribe_segment(audio_path)
    
    # Create video with typewriter captions
    create_typewriter_captions(TRAILER_PATH, segments, OUTPUT_FILE, START_TIME, DURATION)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANING UP")
    print("=" * 60)
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
    os.rmdir(TEMP_DIR)
    
    print(f"\nTypewriter Caption Video created: {OUTPUT_FILE}")
    print(f"Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
