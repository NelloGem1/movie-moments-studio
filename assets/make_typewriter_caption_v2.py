#!/usr/bin/env python3
"""Create typewriter effect captions using ASS subtitles."""
import os
import subprocess
import sys
import whisper

# Configuration
TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/everything_everywhere_all_at_once.mp4")
OUTPUT_DIR = os.path.expanduser("~/Downloads")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "TYPEWRITER_CAPTION_Test.mp4")
TEMP_DIR = "/tmp/typewriter_caption_test"
WHISPER_MODEL = "base"
START_TIME = 30  # Different segment for variety
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

def create_ass_file(segments, output_path, start_time, duration):
    """Create ASS subtitle file with typewriter effect."""
    # ASS header
    ass_content = """[Script Info]
Title: Typewriter Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,42,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,5,20,20,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Add dialogue events with typewriter effect
    for seg in segments:
        # Convert to relative time (ASS uses centiseconds)
        rel_start = seg["start"] - start_time
        rel_end = seg["end"] - start_time
        
        # Skip if outside duration
        if rel_start < 0 or rel_start >= duration:
            continue
        
        # Convert to ASS time format (H:MM:SS.cc)
        def ass_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            centis = int((seconds % 1) * 100)
            return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"
        
        start_ass = ass_time(rel_start)
        end_ass = ass_time(rel_end)
        
        # Create typewriter effect using \k tags
        # \k distributes the duration across characters
        text = seg["text"]
        # Remove special characters that might break ASS
        text = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        
        # Calculate karaoke timing (centiseconds per character)
        duration_cs = int((rel_end - rel_start) * 100)
        char_count = len(text.replace(" ", ""))  # Count non-space chars
        if char_count > 0:
            cs_per_char = duration_cs // char_count
        else:
            cs_per_char = 10
        
        # Build karaoke text
        karaoke_text = ""
        for char in text:
            if char == " ":
                karaoke_text += " "
            else:
                karaoke_text += f"{{\\k{cs_per_char}}}{char}"
        
        # Add event
        ass_content += f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{karaoke_text}\n"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    
    print(f"ASS file created: {output_path}")

def create_typewriter_video(video_path, ass_path, output_path, start_time, duration):
    """Create video with typewriter captions."""
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
    
    # Burn ASS subtitles with typewriter effect
    subtitle_video = os.path.join(TEMP_DIR, "subtitle.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-i", graded_video,
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",
        subtitle_video
    ]
    run_cmd(cmd, "Burning typewriter captions")
    
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
    print("TYPEWRITER CAPTION VIDEO CREATOR (ASS)")
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
    
    # Create ASS file with typewriter effect
    ass_path = os.path.join(TEMP_DIR, "typewriter.ass")
    create_ass_file(segments, ass_path, START_TIME, DURATION)
    
    # Create video with typewriter captions
    create_typewriter_video(TRAILER_PATH, ass_path, OUTPUT_FILE, START_TIME, DURATION)
    
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
