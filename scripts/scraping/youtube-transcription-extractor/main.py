import os
import time
import json
import random
import requests
from datetime import datetime
from google.colab import drive
from google.colab import files
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from concurrent.futures import ThreadPoolExecutor, as_completed

# Mount Google Drive
drive.mount('/content/drive')

# Configuration
OUTPUT_FOLDER = "/content/drive/MyDrive/yt-transcriptions"
LANGUAGE = 'ar'  # Arabic
MAX_WORKERS = 1  # Reduced to 1 to avoid rate limiting
BASE_DELAY = 15  # Increased base delay to 10 seconds
MAX_RETRIES = 1  # Reduced retries to avoid hitting limits
STATUS_FILE = os.path.join(OUTPUT_FOLDER, "processing_status.json")
ERROR_LOG = os.path.join(OUTPUT_FOLDER, "error_log.txt")
FAILED_FILE = os.path.join(OUTPUT_FOLDER, "failed_videos.txt")

def log_error(message):
    """Log errors to a file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def log_failed_video(video_id):
    """Log failed videos to a separate file"""
    with open(FAILED_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{video_id}\n")

def is_video_failed(video_id):
    """Check if video is in failed list"""
    if not os.path.exists(FAILED_FILE):
        return False
    with open(FAILED_FILE, 'r', encoding='utf-8') as f:
        return video_id in [line.strip() for line in f]

def initialize():
    """Initialize the environment and folder structure"""
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'w') as f:
            json.dump({
                "completed": [],
                "pending": [],
                "last_request_time": None
            }, f)
    # Create empty error log if not exists
    open(ERROR_LOG, 'a').close()
    open(FAILED_FILE, 'a').close()

def load_status():
    """Load processing status"""
    try:
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "completed": [],
            "pending": [],
            "last_request_time": None
        }

def save_status(status):
    """Save processing status"""
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f)

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    url = url.strip()
    if 'youtube.com/watch' in url and 'v=' in url:
        return url.split('v=')[1].split('&')[0][:11]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0][:11]
    elif len(url) == 11 and all(c.isalnum() or c in ['-', '_'] for c in url):
        return url
    return None

def enforce_rate_limit(status):
    """Enforce rate limiting based on last request time"""
    if status.get('last_request_time'):
        elapsed = time.time() - status['last_request_time']
        if elapsed < BASE_DELAY:
            sleep_time = BASE_DELAY - elapsed + random.uniform(0, 5)  # Added more jitter
            print(f"Rate limiting: Waiting {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
    status['last_request_time'] = time.time()
    save_status(status)

def extract_transcript(video_id):
    """Extract transcript with enhanced retry logic"""
    if is_video_failed(video_id):
        print(f"[{video_id}] Previously failed - skipping")
        return None

    for attempt in range(MAX_RETRIES):
        try:
            status = load_status()
            enforce_rate_limit(status)

            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=[LANGUAGE]
            )
            return transcript

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = (2 ** attempt) + random.uniform(5, 15)  # Longer wait times
                msg = f"[{video_id}] Attempt {attempt + 1} failed: 429 Too Many Requests. Waiting {wait_time:.1f}s"
                print(msg)
                log_error(msg)
                time.sleep(wait_time)
                continue
            else:
                msg = f"[{video_id}] HTTP Error {e.response.status_code}: {str(e)}"
                print(msg)
                log_error(msg)
                log_failed_video(video_id)
                return None

        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            msg = f"[{video_id}] {str(e)}"
            print(msg)
            log_error(msg)
            log_failed_video(video_id)
            return None

        except Exception as e:
            msg = f"[{video_id}] Attempt {attempt + 1} failed: {str(e)}"
            print(msg)
            log_error(msg)
            if attempt == MAX_RETRIES - 1:
                log_failed_video(video_id)
            if attempt < MAX_RETRIES - 1:
                wait_time = BASE_DELAY * (attempt + 1) + random.uniform(0, 5)
                print(f"Waiting {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)
            continue

    return None

def save_transcript_to_file(transcript, video_id):
    """Save transcript to individual text file"""
    output_path = os.path.join(OUTPUT_FOLDER, f"{video_id}.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in transcript:
            f.write(f"{entry['text']}\n")
    print(f"[{video_id}] Transcript saved to {output_path}")

def process_video(video_url):
    """Process a single video with enhanced status tracking"""
    video_id = get_video_id(video_url)
    if not video_id:
        msg = f"[Invalid URL] {video_url}"
        print(msg)
        log_error(msg)
        return False

    status = load_status()
    if video_id in status['completed']:
        print(f"[{video_id}] Already processed")
        return True

    # Mark as pending if not already
    if video_id not in status['pending']:
        status['pending'].append(video_id)
        save_status(status)

    # Extract transcript
    transcript = extract_transcript(video_id)
    if not transcript:
        if video_id in status['pending']:
            status['pending'].remove(video_id)
        save_status(status)
        return False

    # Save to individual file
    save_transcript_to_file(transcript, video_id)

    # Update status
    status['completed'].append(video_id)
    if video_id in status['pending']:
        status['pending'].remove(video_id)
    save_status(status)

    return True

def upload_and_read_file():
    """Upload and read the yt.txt file"""
    print("Please upload your yt.txt file (one YouTube URL per line):")
    uploaded = files.upload()
    for filename in uploaded.keys():
        if filename.lower().startswith('yt') and filename.lower().endswith('.txt'):
            with open(filename, 'r') as f:
                return [line.strip() for line in f if line.strip()]
    return []

def main():
    initialize()

    video_urls = upload_and_read_file()

    if not video_urls:
        print("No valid URLs found in uploaded file")
        return

    status = load_status()

    # Filter out already processed and failed videos
    new_urls = []
    for url in video_urls:
        video_id = get_video_id(url)
        if video_id and video_id not in status['completed'] and not is_video_failed(video_id):
            new_urls.append(url)

    if not new_urls:
        print("No new videos to process (all completed or previously failed)")
        return

    print(f"\nFound {len(new_urls)} new videos to process")
    print("Starting processing (this may take a while)...\n")

    # Process videos with thread pool
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_video, url): url for url in new_urls}

        for future in as_completed(futures):
            url = futures[future]
            try:
                future.result()
            except Exception as e:
                msg = f"Error processing {url}: {str(e)}"
                print(msg)
                log_error(msg)
                # Update status for failed URLs
                video_id = get_video_id(url)
                if video_id:
                    status = load_status()
                    if video_id in status['pending']:
                        status['pending'].remove(video_id)
                    save_status(status)

    # Final status report
    status = load_status()
    print("\nProcessing complete!")
    print(f"Successfully processed: {len(status['completed'])}")
    print(f"Failed videos logged in: {FAILED_FILE}")
    print(f"Transcripts saved in: {OUTPUT_FOLDER}")
    print(f"Error log saved in: {ERROR_LOG}")

if __name__ == "__main__":
    main()
