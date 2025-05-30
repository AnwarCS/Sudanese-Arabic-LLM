import os
import json
import re
from datetime import datetime

# Configuration - match your main script
YT_FILE = "yt.txt"  # Original input file
OUTPUT_FOLDER = "extracted-transcripts"  # Where transcripts are saved
ERROR_LOG = os.path.join(OUTPUT_FOLDER, "error_log.txt")
FAILED_FILE = os.path.join(OUTPUT_FOLDER, "failed_videos.txt")
STATUS_FILE = os.path.join(OUTPUT_FOLDER, "processing_status.json")
LANGUAGE = 'ar'  # Target language

def get_video_id(url):
    """Extract video ID from URL or ID string"""
    if not url:
        return None
    
    # If it's already a video ID (11 chars)
    if len(url) == 11 and all(c.isalnum() or c in ['-', '_'] for c in url):
        return url
    
    # Handle different URL formats
    patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"v=([a-zA-Z0-9_-]{11})",
        r"embed/([a-zA-Z0-9_-]{11})"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_all_original_videos():
    """Get all video IDs from original yt.txt"""
    if not os.path.exists(YT_FILE):
        return set()
    
    video_ids = set()
    with open(YT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            video_id = get_video_id(line)
            if video_id:
                video_ids.add(video_id)
    
    return video_ids

def get_downloaded_videos():
    """Get video IDs of successfully downloaded transcripts"""
    downloaded = set()
    if not os.path.exists(OUTPUT_FOLDER):
        return downloaded
    
    for filename in os.listdir(OUTPUT_FOLDER):
        if filename.endswith('.txt') and filename != "error_log.txt":
            video_id = filename[:-4]  # Remove .txt extension
            if len(video_id) == 11:  # Basic validation
                downloaded.add(video_id)
    
    return downloaded

def get_failed_videos():
    """Get video IDs from failed_videos.txt"""
    if not os.path.exists(FAILED_FILE):
        return set()
    
    with open(FAILED_FILE, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip() and len(line.strip()) == 11}

def analyze_errors():
    """Categorize errors from error log"""
    error_categories = {
        'no_subtitles': set(),
        'rate_limited': set(),
        'unavailable': set(),
        'other': set()
    }

    if not os.path.exists(ERROR_LOG):
        return error_categories

    with open(ERROR_LOG, 'r', encoding='utf-8') as f:
        for line in f:
            # Extract video ID
            match = re.search(r'\[([a-zA-Z0-9_-]{11})\]', line)
            if not match:
                continue
            
            video_id = match.group(1)
            
            if "No subtitles found" in line or "No transcript available" in line:
                error_categories['no_subtitles'].add(video_id)
            elif "rate-limit" in line or "429" in line or "too many requests" in line:
                error_categories['rate_limited'].add(video_id)
            elif "unavailable" in line or "not available" in line or "private" in line:
                error_categories['unavailable'].add(video_id)
            else:
                error_categories['other'].add(video_id)
    
    return error_categories

def create_new_iteration_file(iteration):
    """Create new iteration file with missing videos (write URLs, not IDs)"""
    original_videos = get_all_original_videos()
    downloaded_videos = get_downloaded_videos()
    failed_videos = get_failed_videos()
    error_categories = analyze_errors()
    
    # Calculate missing videos
    missing_videos = original_videos - downloaded_videos
    
    # Remove videos we don't want to retry (only skip 'no_subtitles' and 'unavailable')
    skip_videos = error_categories['no_subtitles'].union(
        error_categories['unavailable']
    )
    videos_to_retry = missing_videos - skip_videos
    
    # Get original URLs for these videos (always use the original URL, not just the ID)
    video_id_to_url = {}
    with open(YT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            video_id = get_video_id(line)
            if video_id:
                video_id_to_url[video_id] = line  # Always map ID to original line (URL or ID)
    
    # Create new iteration file with URLs for videos to retry
    new_filename = f"yt_iteration_{iteration}.txt"
    with open(new_filename, 'w', encoding='utf-8') as f:
        for video_id in videos_to_retry:
            url = video_id_to_url.get(video_id)
            if url:
                f.write(url + "\n")
    
    # Generate report
    report = {
        "date": datetime.now().isoformat(),
        "original_video_count": len(original_videos),
        "downloaded_count": len(downloaded_videos),
        "missing_count": len(missing_videos),
        "retrying_count": len(videos_to_retry),
        "skipped_no_subtitles": len(error_categories['no_subtitles']),
        "skipped_unavailable": len(error_categories['unavailable']),
        "skipped_failed": len(failed_videos),
        "new_file": new_filename
    }
    
    # Save report
    report_file = os.path.join(OUTPUT_FOLDER, f"iteration_{iteration}_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*50)
    print("Video Processing Report")
    print("="*50)
    print(f"Original videos in yt.txt: {report['original_video_count']}")
    print(f"Successfully downloaded: {report['downloaded_count']}")
    print(f"Missing videos: {report['missing_count']}")
    print(f"\nBreaking down missing videos:")
    print(f"- Will retry: {report['retrying_count']}")
    print(f"- Skipped (no subtitles): {report['skipped_no_subtitles']}")
    print(f"- Skipped (unavailable): {report['skipped_unavailable']}")
    print(f"- Skipped (failed): {report['skipped_failed']}")
    print(f"\nNew file created: {report['new_file']}")
    print("\nNext steps:")
    print(f"1. Review the report: {report_file}")
    print(f"2. Wait at least 1 hour before retrying")
    print(f"3. Run: python youtube_transcriber.py --input {new_filename}")
    print("="*50 + "\n")
    
    return new_filename

def main():
    # Ensure output folder exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    # Find next iteration number
    iteration = 1
    while os.path.exists(f"yt_iteration_{iteration}.txt"):
        iteration += 1
    
    print(f"Creating iteration {iteration} processing file...")
    new_file = create_new_iteration_file(iteration)
    
    print(f"\nSuccessfully created {new_file} with videos to retry.")
    print("Recommendations:")
    print("- Wait at least 1 hour before running the next iteration")
    print("- Consider increasing delays in youtube_transcriber.py")
    print("- For rate-limited videos, try using cookies if available")

if __name__ == "__main__":
    main()