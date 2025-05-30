
# YouTube Transcription Extractor

[![Python Version](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A robust Python script to extract transcriptions from YouTube videos, including auto-generated captions, with comprehensive error handling and multiple output formats.

## Features

- **Extraction Capabilities**:
  - Manual and auto-generated captions
  - Multiple languages support
  - Translation option for auto-generated captions

- **Output Formats**:
  - Plain text (.txt)
  - JSON (.json)
  - SRT subtitles (.srt)
  - VTT subtitles (.vtt)

- **Error Handling**:
  - Automatic retry mechanism (3 attempts by default)
  - Detailed error logging
  - Skip unavailable videos in batch processing
  - Graceful handling of various failure scenarios

## Installation

### Option 1: Clone Repository
```bash
git clone https://github.com/O96a/youtube-transcription-extractor.git
cd youtube-transcription-extractor
pip install -r requirements.txt
```

### Option 2: Install via pip
```bash
pip install youtube-transcription-extractor
```

## Usage

### Basic Command
```bash
python extract_transcript.py [YOUTUBE_URL] [OPTIONS]
```

### Command Options

| Option          | Description                          | Default       |
|-----------------|--------------------------------------|---------------|
| `-o`, `--output` | Output file path                     | transcript.txt|
| `-f`, `--format` | Output format (txt, json, srt, vtt) | txt          |
| `-l`, `--language` | Language code (e.g., ar, en, fr)    | ar           |
| `--translate`    | Translate to English                 | False        |
| `--retries`      | Number of retry attempts             | 3            |
| `--skip-failed`  | Skip failed videos in batch mode     | False        |
| `--verbose`      | Show detailed error messages         | False        |

### Handling Failed Videos

The script includes multiple mechanisms to handle failures:

1. **Automatic Retry System**:
   - 3 retry attempts by default (configurable with `--retries`)
   - Exponential backoff between attempts

2. **Error Logging**:
   - Detailed logs in `transcription_errors.log`
   - Failed video IDs saved in `failed_videos.txt`

3. **Batch Processing**:
   - Use `--skip-failed` to continue processing other videos
   - Progress tracking with success/failure counts

4. **Common Failure Cases Handled**:
   - Videos with disabled captions
   - Age-restricted content
   - Private/deleted videos
   - Network timeouts
   - Invalid language requests
   - Rate limiting from YouTube

### Examples

1. Basic extraction:
```bash
python extract_transcript.py https://youtu.be/example
```

2. Extract Arabic captions as JSON:
```bash
python extract_transcript.py https://youtu.be/example -l ar -f json
```

3. Batch processing with error handling:
```bash
python batch_process.py video_list.txt --skip-failed --retries 5
```

4. Verbose error output:
```bash
python extract_transcript.py https://youtu.be/example --verbose
```

## Dependencies

- Python 3.6+
- [pytube](https://pytube.io) - YouTube content download
- requests - HTTP requests
- webvtt-py - WebVTT format support

Install all dependencies:
```bash
pip install pytube requests webvtt-py
```

## Development

To set up a development environment:
```bash
git clone https://github.com/O96a/youtube-transcription-extractor.git
cd youtube-transcription-extractor
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
```

Run tests:
```bash
pytest
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a Pull Request

Report issues and feature requests in the [Issues section](https://github.com/O96a/youtube-transcription-extractor/issues).

## License

MIT License. See [LICENSE](LICENSE) for details.

