import os
import re
import time
import json
import random
import requests
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration - Update these paths according to your local setup
COOKIES_FILE = r"cookies.txt"  # Path to your cookies file
YT_URLS_FILE = r"yt_iteration_15.txt"  # Path to your YouTube URLs file
OUTPUT_FOLDER = r"extracted-transcripts"  # Folder where transcripts will be saved

LANGUAGE = 'ar'  # Arabic
MAX_WORKERS = 1  # Single worker to avoid detection
BASE_DELAY = 60  # Base delay between requests
MAX_RETRIES = 1  # Only 1 attempt as requested
BATCH_SIZE = 50  # Batch size for processing
STATUS_FILE = os.path.join(OUTPUT_FOLDER, "processing_status.json")
ERROR_LOG = os.path.join(OUTPUT_FOLDER, "error_log.txt")
FAILED_FILE = os.path.join(OUTPUT_FOLDER, "failed_videos.txt")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15"
]

def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format"""
    return str(timedelta(seconds=seconds))

class YouTubeScraper:
    def __init__(self):
        self.last_request_time = 0
        self.request_count = 0
        self.user_agents = USER_AGENTS.copy()
        random.shuffle(self.user_agents)
        self.current_agent_index = 0
        self.cookies_available = os.path.exists(COOKIES_FILE)
        
    def get_user_agent(self):
        """Rotate user agents"""
        agent = self.user_agents[self.current_agent_index]
        self.current_agent_index = (self.current_agent_index + 1) % len(self.user_agents)
        return agent
        
    def get_ytdlp_options(self):
        """Get yt-dlp options with cookies if available"""
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': [LANGUAGE],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'retries': 1,
            'throttledratelimit': 50,
        }
        
        if self.cookies_available:
            ydl_opts['cookiefile'] = COOKIES_FILE
            print("Using cookies for authentication")
            
        return ydl_opts

    def get_transcript_ytdlp(self, video_id):
        """Get transcript using yt-dlp with cookie support"""
        ydl_opts = self.get_ytdlp_options()
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    f'https://www.youtube.com/watch?v={video_id}',
                    download=False
                )
                if not info:
                    raise Exception("No video info found")
                
                # Check for manual captions
                if info.get('subtitles') and LANGUAGE in info['subtitles']:
                    sub_url = info['subtitles'][LANGUAGE][-1]['url']
                    sub_data = requests.get(sub_url).text
                    return self.parse_subtitles(sub_data)
                
                # Check for auto-generated captions
                elif info.get('automatic_captions') and LANGUAGE in info['automatic_captions']:
                    sub_url = info['automatic_captions'][LANGUAGE][-1]['url']
                    sub_data = requests.get(sub_url).text
                    return self.parse_subtitles(sub_data)
                
                raise Exception("No subtitles found for the specified language")
                
        except Exception as e:
            # If we have cookies and still get blocked, mark cookies as invalid
            if "Sign in to confirm you're not a bot" in str(e) and self.cookies_available:
                print("Cookies may be invalid, trying without cookies")
                self.cookies_available = False
                return self.get_transcript_ytdlp(video_id)
            raise Exception(f"yt-dlp error: {str(e)}")

    def parse_subtitles(self, sub_data):
        """Parse subtitle data into timestamped format with duplicate removal"""
        try:
            subtitles = []
            
            # For XML format subtitles
            if '<text start=' in sub_data:
                soup = BeautifulSoup(sub_data, 'html.parser')
                for text in soup.find_all('text'):
                    try:
                        start = float(text['start'])
                        duration = float(text.get('dur', 0))
                        content = text.get_text().strip()
                        if content:  # Only add non-empty content
                            subtitles.append({
                                'text': content,
                                'start': start,
                                'duration': duration
                            })
                    except (KeyError, ValueError):
                        continue
            
            # For JSON format subtitles
            elif 'events' in sub_data:
                try:
                    data = json.loads(sub_data)
                    for event in data['events']:
                        if 'segs' in event and event['segs']:
                            try:
                                start = event.get('tStartMs', 0) / 1000
                                duration = event.get('dDurationMs', 0) / 1000
                                content = ' '.join(seg.get('utf8', '') for seg in event['segs']).strip()
                                if content:
                                    subtitles.append({
                                        'text': content,
                                        'start': start,
                                        'duration': duration
                                    })
                            except (KeyError, TypeError):
                                continue
                except json.JSONDecodeError:
                    pass
            
            # For SRT format
            elif '-->' in sub_data:
                lines = [line.strip() for line in sub_data.split('\n') if line.strip()]
                i = 0
                while i < len(lines):
                    if '-->' in lines[i]:
                        try:
                            times = lines[i].split('-->')
                            start = self.srt_time_to_seconds(times[0].strip())
                            end = self.srt_time_to_seconds(times[1].strip())
                            duration = end - start
                            if i+1 < len(lines):
                                content = lines[i+1].strip()
                                if content:
                                    subtitles.append({
                                        'text': content,
                                        'start': start,
                                        'duration': duration
                                    })
                            i += 2
                        except (IndexError, ValueError):
                            i += 1
                    else:
                        i += 1
            
            if not subtitles:
                raise Exception("No valid subtitles found in the data")
            
            # Remove duplicates - keep only one instance of each unique text at the same start time
            unique_subtitles = []
            seen = set()
            for sub in subtitles:
                identifier = (sub['start'], sub['text'])
                if identifier not in seen:
                    seen.add(identifier)
                    unique_subtitles.append(sub)
            
            return unique_subtitles
            
        except Exception as e:
            raise Exception(f"Subtitle parsing error: {str(e)}")

    def srt_time_to_seconds(self, time_str):
        """Convert SRT time format to seconds with better error handling"""
        try:
            if ',' in time_str:
                time_part, ms_part = time_str.split(',')
                ms = float(ms_part)
            elif '.' in time_str:
                time_part, ms_part = time_str.split('.')
                ms = float(ms_part)
            else:
                time_part = time_str
                ms = 0
            
            time_parts = list(map(float, time_part.split(':')))
            if len(time_parts) == 3:  # HH:MM:SS
                return time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2] + ms/1000
            elif len(time_parts) == 2:  # MM:SS
                return time_parts[0] * 60 + time_parts[1] + ms/1000
            else:
                return time_parts[0] + ms/1000  # SS
        except:
            return 0  # Default to 0 if parsing fails

# Initialize scraper
scraper = YouTubeScraper()

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
                "last_request_time": None,
                "batch_count": 0,
                "processed_count": 0
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
            "last_request_time": None,
            "batch_count": 0,
            "processed_count": 0
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
    """Enforce rate limiting with more sophisticated delay patterns"""
    if status.get('last_request_time'):
        elapsed = time.time() - status['last_request_time']
        
        # Variable delay based on request patterns
        if status.get('processed_count', 0) % 10 == 0 and status['processed_count'] > 0:
            # Longer delay every 10 videos
            delay = BASE_DELAY * 2 + random.uniform(30, 60)
        else:
            # Normal delay with random variation
            delay = BASE_DELAY + random.uniform(10, 20)
            
        if elapsed < delay:
            sleep_time = delay - elapsed
            print(f"Rate limiting: Waiting {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
            
    status['last_request_time'] = time.time()
    save_status(status)

def extract_transcript(video_id):
    """Extract transcript using multiple methods with fallbacks"""
    if is_video_failed(video_id):
        print(f"[{video_id}] Previously failed - skipping")
        return None

    try:
        status = load_status()
        enforce_rate_limit(status)

        # Try yt-dlp method first (with cookies if available)
        transcript = scraper.get_transcript_ytdlp(video_id)
        if transcript:
            return transcript

        raise Exception("No transcript found using any method")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            msg = f"[{video_id}] Failed: 429 Too Many Requests"
            print(msg)
            log_error(msg)
        else:
            msg = f"[{video_id}] HTTP Error {e.response.status_code}: {str(e)}"
            print(msg)
            log_error(msg)
        log_failed_video(video_id)
        return None

    except Exception as e:
        msg = f"[{video_id}] Failed: {str(e)}"
        print(msg)
        log_error(msg)
        log_failed_video(video_id)
        return None

def save_individual_transcript(transcript, video_id):
    """Save transcript to individual file named after video ID with timestamps"""
    output_path = os.path.join(OUTPUT_FOLDER, f"{video_id}.txt")
    
    # Ensure we don't have consecutive duplicates
    previous_text = None
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in transcript:
            current_text = entry['text'].strip()
            if current_text != previous_text:  # Only write if different from previous line
                timestamp = format_timestamp(entry['start'])
                f.write(f"[{timestamp}] {current_text}\n")
                previous_text = current_text
    
    print(f"[{video_id}] Transcript with timestamps saved to {output_path}")

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

    # Update status
    status['completed'].append(video_id)
    status['processed_count'] += 1
    if video_id in status['pending']:
        status['pending'].remove(video_id)
    save_status(status)

    # Save individual transcript with timestamps
    save_individual_transcript(transcript, video_id)

    # Check if we need to process a batch
    if status['processed_count'] % BATCH_SIZE == 0:
        print(f"\nCompleted batch of {BATCH_SIZE} transcripts (total processed: {status['processed_count']})")
        # Add artificial delay between batches
        time.sleep(random.uniform(30, 90))

    return True

def read_urls_from_file():
    """Read YouTube URLs from the input file (YT_URLS_FILE)"""
    if not YT_URLS_FILE or not os.path.exists(YT_URLS_FILE):
        print(f"Error: Could not find input file: {YT_URLS_FILE}")
        return []
    try:
        with open(YT_URLS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading {YT_URLS_FILE}: {e}")
        return []

def main():
    global YT_URLS_FILE
    initialize()
    
    # Allow input file override via command-line argument
    input_file = YT_URLS_FILE
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg in ('--input', '-i') and i + 1 < len(sys.argv):
                input_file = sys.argv[i + 1]
                break
            elif arg.endswith('.txt') and i > 0:
                input_file = arg
                break
    YT_URLS_FILE = input_file

    # Read video URLs from file
    video_urls = read_urls_from_file()
    
    if not video_urls:
        print("No valid URLs found in the file")
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
    print(f"Total batches completed: {status['processed_count'] // BATCH_SIZE}")
    print(f"Failed videos logged in: {FAILED_FILE}")
    print(f"Transcripts saved in: {OUTPUT_FOLDER}")
    print(f"Error log saved in: {ERROR_LOG}")

if __name__ == "__main__":
    # Run the main function
    main()