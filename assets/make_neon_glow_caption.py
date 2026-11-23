#!/usr/bin/env python3
"""Create cinematic neon glow subtitle style."""
import os
import subprocess
import sys
import whisper

# Configuration
TRAILER_PATH = os.path.expanduser("~/youtube-tool/assets/trailers_dl/dune_part_two.mp4")
OUTPUT_DIR = os.path.expanduser("~/Downloads")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "NEON_GLOW_CAPTION_Short.mp4")
TEMP_DIR = "/tmp/neon_glow_caption"
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

def create_neon_glow_ass(segments, output_path, start_time, duration):
    """Create ASS subtitle file with neon glow effect."""
    # ASS header with neon glow style
    ass_content = """[Script Info]
Title: Neon Glow Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: NeonGlow,Arial Black,48,&H00FFFFFF,&H0000FFFF,&H00FFFF00,&H80000000,1,0,0,0,100,100,0,0,1,3,4,5,20,20,100,1
Style: NeonGlowSmall,Arial Black,36,&H00FFFFFF,&H0000FFFF,&H00FFFF00,&H80000000,1,0,0,0,100,100,0,0,1,2,3,5,20,20,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Add dialogue events with neon glow and word-by-word animation
    for seg in segments:
        # Convert to relative time
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
        
        # Create word-by-word animation with neon glow
        text = seg["text"]
        words = text.split()
        
        # Calculate timing for each word
        duration_cs = int((rel_end - rel_start) * 100)
        word_count = len(words)
        cs_per_word = duration_cs // word_count if word_count > 0 else 10
        
        # Build animated text with neon glow effect
        animated_text = ""
        for i, word in enumerate(words):
            # Escape special characters
            word_escaped = word.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
            
            # Add word with fade-in and slight zoom
            # \fad for fade, \fscx/\fscy for scale animation
            fade_in = min(5, cs_per_word // 4)  # Quick fade in
            fade_out = min(5, cs_per_word // 4)  # Quick fade out
            
            # Word appears with fade and slight scale
            word_tag = f"{{\\fad({fade_in},{fade_out})\\fscx80\\fscy80\\t(0,100,\\fscx100\\fscy100)}}{word_escaped} "
            animated_text += word_tag
        
        # Choose style based on text length
        style = "NeonGlow" if len(text) < 50 else "NeonGlowSmall"
        
        # Add event
        ass_content += f"Dialogue: 0,{start_ass},{end_ass},{style},,0,0,0,,{animated_text}\n"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    
    print(f"Neon Glow ASS file created: {output_path}")

def create_neon_glow_video(video_path, ass_path, output_path, start_time, duration):
    """Create video with neon glow captions."""
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
    
    # Burn neon glow subtitles
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
    run_cmd(cmd, "Burning neon glow captions")
    
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
    print("NEON GLOW CAPTION VIDEO CREATOR")
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
    
    # Create neon glow ASS file
    ass_path = os.path.join(TEMP_DIR, "neon_glow.ass")
    create_neon_glow_ass(segments, ass_path, START_TIME, DURATION)
    
    # Create video with neon glow captions
    create_neon_glow_video(TRAILER_PATH, ass_path, OUTPUT_FILE, START_TIME, DURATION)
    
    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANING UP")
    print("=" * 60)
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
    os.rmdir(TEMP_DIR)
    
    print(f"\nNeon Glow Caption Video created: {OUTPUT_FILE}")
    print(f"Location: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
