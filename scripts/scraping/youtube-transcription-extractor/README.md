# YouTube Transcript Extractor

## Overview

This Python script is designed to extract transcripts from YouTube videos in Arabic (or any other specified language) and save them as text files. The tool is optimized for use in Google Colab and includes features for handling rate limiting, tracking processing status, and logging errors.

## Features

- **YouTube Transcript Extraction**: Fetches transcripts using the `youtube-transcript-api` package
- **Google Drive Integration**: Saves transcripts directly to your Google Drive
- **Rate Limiting**: Implements intelligent rate limiting to avoid API bans
- **Progress Tracking**: Maintains a JSON file to track completed and pending videos
- **Error Handling**: Comprehensive error logging and retry mechanisms
- **Parallel Processing**: Supports concurrent processing (though default is single-threaded)
- **User-Friendly**: Simple file upload interface in Colab

## Prerequisites

- Google Colab environment
- Google Drive account (for saving transcripts)
- Basic Python knowledge

## Installation

1. Open the script in Google Colab
2. Run the first cell to install dependencies:
   ```python
   !pip install youtube-transcript-api
   ```

## Configuration

Modify these variables at the top of the script as needed:

```python
OUTPUT_FOLDER = "/content/drive/MyDrive/yt-transcriptions"  # Where to save transcripts
LANGUAGE = 'ar'  # Language code for transcripts (Arabic by default)
MAX_WORKERS = 1  # Number of concurrent workers (reduce if hitting rate limits)
BASE_DELAY = 15  # Base delay between requests in seconds
MAX_RETRIES = 1  # Maximum number of retry attempts
```

## Usage

1. **Prepare your input file**:
   - Create a text file named `yt.txt`
   - Add one YouTube URL per line (or just video IDs)
   - Example:
     ```
     https://www.youtube.com/watch?v=VIDEO_ID_1
     https://youtu.be/VIDEO_ID_2
     VIDEO_ID_3
     ```

2. **Run the script**:
   - Execute all cells in order
   - When prompted, upload your `yt.txt` file

3. **Monitor progress**:
   - The script will display progress in the console
   - Detailed logs are saved to:
     - `processing_status.json` - Tracks completed/pending videos
     - `error_log.txt` - Contains error messages
     - `failed_videos.txt` - Lists videos that couldn't be processed

4. **Access results**:
   - Transcripts are saved as individual `.txt` files in your specified output folder
   - Each file is named with the video ID (e.g., `VIDEO_ID_1.txt`)

## File Structure

After running the script, your output folder will contain:

```
/yt-transcriptions/
│── VIDEO_ID_1.txt
│── VIDEO_ID_2.txt
│── ...
│── processing_status.json
│── error_log.txt
│── failed_videos.txt
```

## Error Handling

The script handles several types of errors gracefully:

- **Rate limiting (HTTP 429)**: Automatically waits and retries
- **Transcripts disabled**: Logs the error and skips the video
- **Video unavailable**: Logs the error and skips the video
- **Invalid URLs**: Logs the error and skips

## Performance Notes

- The default configuration uses a single worker (`MAX_WORKERS = 1`) to avoid rate limiting
- Base delay between requests is set to 15 seconds (`BASE_DELAY = 15`)
- You may adjust these values based on your needs and YouTube's response

## Limitations

- Not all YouTube videos have transcripts available
- Some transcripts may be auto-generated and less accurate
- The script may be subject to YouTube's API rate limits

## Troubleshooting

1. **Transcripts not found**:
   - Verify the video has transcripts available
   - Check the language setting matches the video's transcript language

2. **Rate limiting errors**:
   - Increase `BASE_DELAY`
   - Reduce `MAX_WORKERS` to 1
   - Wait and try again later

3. **Google Drive access issues**:
   - Ensure you've mounted Google Drive correctly
   - Check the output folder path exists

## License

This project is open-source and available for use under the MIT License.

## Support

For issues or feature requests, please open an issue in the GitHub repository.
