#!/usr/bin/env python3
"""Scheduled Movie Moments publisher - runs every 4 hours."""
import os
import sys
import time
import subprocess
import requests
from datetime import datetime, timedelta

# Configuration
MOVIE_MOMENTS_DIR = os.path.expanduser("~/Downloads/MOVIE_MOMENTS")
ASSETS_DIR = os.path.expanduser("~/youtube-tool/assets")
LOG_FILE = os.path.join(ASSETS_DIR, "scheduled_publisher.log")
INTERVAL_HOURS = 4

def log(message):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

def check_internet():
    """Check if internet is available."""
    try:
        response = requests.get("https://www.youtube.com", timeout=10)
        return response.status_code == 200
    except:
        return False

def get_next_publish_time():
    """Calculate next publish time (every 4 hours)."""
    now = datetime.now()
    # Round up to next 4-hour mark (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
    current_hour = now.hour
    next_hour = ((current_hour // INTERVAL_HOURS) + 1) * INTERVAL_HOURS
    if next_hour >= 24:
        next_publish = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        next_publish = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    return next_publish

def build_and_publish():
    """Build one movie and publish it."""
    log("=" * 60)
    log("Starting scheduled Movie Moments publish")
    log("=" * 60)
    
    # Check internet
    if not check_internet():
        log("ERROR: No internet connection - skipping")
        return False
    
    log("Internet connection OK")
    
    # Check if MOVIE_MOMENTS folder exists
    if not os.path.exists(MOVIE_MOMENTS_DIR):
        log(f"ERROR: {MOVIE_MOMENTS_DIR} not found")
        return False
    
    # Check if there are pending files
    pending_files = [f for f in os.listdir(MOVIE_MOMENTS_DIR) if f.endswith('.mp4')]
    
    if pending_files:
        log(f"Found {len(pending_files)} pending files - uploading first")
        # Upload pending files
        upload_script = os.path.join(ASSETS_DIR, "mm_upload.py")
        result = subprocess.run(
            [sys.executable, upload_script],
            cwd=ASSETS_DIR,
            capture_output=True,
            text=True
        )
        log(f"Upload result: {result.returncode}")
        if result.stdout:
            log(f"Upload output: {result.stdout}")
        if result.stderr:
            log(f"Upload error: {result.stderr}")
        return result.returncode == 0
    
    # No pending files - build a new one
    log("No pending files - building new movie")
    
    # Run the factory to build one movie
    factory_script = os.path.join(ASSETS_DIR, "mm_factory.py")
    
    # Check if factory has movies to build
    # We'll run it and let it handle the queue
    result = subprocess.run(
        [sys.executable, factory_script, "--once"],
        cwd=ASSETS_DIR,
        capture_output=True,
        text=True,
        timeout=3600  # 1 hour timeout
    )
    
    log(f"Build result: {result.returncode}")
    if result.stdout:
        log(f"Build output: {result.stdout[-500:]}")  # Last 500 chars
    if result.stderr:
        log(f"Build error: {result.stderr[-500:]}")
    
    # After building, check for new files and upload
    new_pending = [f for f in os.listdir(MOVIE_MOMENTS_DIR) if f.endswith('.mp4')]
    if new_pending:
        log(f"New file built: {new_pending[0]}")
        # Upload it
        upload_script = os.path.join(ASSETS_DIR, "mm_upload.py")
        upload_result = subprocess.run(
            [sys.executable, upload_script],
            cwd=ASSETS_DIR,
            capture_output=True,
            text=True
        )
        log(f"Upload result: {upload_result.returncode}")
        return upload_result.returncode == 0
    else:
        log("No new file was built")
        return False

def main():
    """Main scheduled publisher loop."""
    log("=" * 60)
    log("Movie Moments Scheduled Publisher Started")
    log(f"Interval: Every {INTERVAL_HOURS} hours")
    log(f"Next publish: {get_next_publish_time()}")
    log("=" * 60)
    
    while True:
        try:
            # Calculate time until next publish
            next_publish = get_next_publish_time()
            now = datetime.now()
            wait_seconds = (next_publish - now).total_seconds()
            
            log(f"Next publish at: {next_publish}")
            log(f"Waiting {wait_seconds/3600:.1f} hours...")
            
            # Sleep until next publish time
            time.sleep(wait_seconds)
            
            # Publish
            success = build_and_publish()
            
            if success:
                log("Publish completed successfully")
            else:
                log("Publish failed or skipped")
                # Wait 30 minutes before retrying
                log("Retrying in 30 minutes...")
                time.sleep(1800)
                
        except KeyboardInterrupt:
            log("Publisher stopped by user")
            break
        except Exception as e:
            log(f"ERROR: {e}")
            log("Retrying in 1 hour...")
            time.sleep(3600)

if __name__ == "__main__":
    main()
