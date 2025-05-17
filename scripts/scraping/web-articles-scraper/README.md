
# Web Scraper for Article Extraction

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4.9.3-green.svg)
![Requests](https://img.shields.io/badge/Requests-2.25.1-yellowgreen.svg)

This web scraper is designed to run in Google colab to extract articles from websites and save them to a local folder with enhanced stealth features to avoid detection.

## Features

- **Stealthy Crawling**: Rotates user agents, adds random delays, and mimics human behavior
- **Comprehensive Extraction**: Captures article title, content, publication date, and URL
- **BFS Crawling**: Uses Breadth-First Search to systematically explore the website
- **Persistent Cache**: Tracks processed URLs to avoid re-scraping
- **Error Handling**: Robust retry mechanism with exponential backoff
- **Content Cleaning**: Removes boilerplate text and unwanted HTML elements

## Installation

1. **Prerequisites**:
   - Python 3.6+

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Configuration

Edit these variables in the script:
```python
BASE_URL = "https://example.com"  # Replace with your target website
SAVE_DIR = "All_Articles"         # Output directory (local)
```

## Usage

1. Set `BASE_URL` in `scraper.py` to your target website.
2. Run the script locally:
   ```powershell
   python scraper.py
   ```
3. The scraper will:
   - Start from the BASE_URL
   - Discover all article links
   - Extract content from each article
   - Save articles sequentially in the specified directory

## File Structure

Saved articles follow this format:
```
article_00001.txt
article_00002.txt
...
```

Each file contains:
- Article URL
- Title
- Publication date
- Cleaned content

## Advanced Features

### Stealth Techniques
- Random user agent rotation
- Referer header spoofing
- Randomized delays between requests
- Exponential backoff on failures

### Content Extraction
- Multiple fallback selectors for title/content/date
- Automatic boilerplate removal
- Comprehensive HTML cleaning

### Caching System
- JSON-based URL cache
- Periodic automatic saves
- Prevents duplicate scraping

## Customization

To adapt the scraper for different websites:

1. **Article Link Detection**:
   Modify `extract_article_links()` to match your target site's URL patterns

2. **Content Selectors**:
   Adjust the CSS selectors in `extract_article_content()` to match the site's structure

3. **Request Headers**:
   Update `HEADERS` and `USER_AGENTS` as needed

## Performance Notes

- Processes up to 5000 articles (safety limit)
- Includes random delays to avoid overwhelming servers
- Saves progress every 10 articles

## License

This project is open-source and available for use under the MIT License.

## Support

For issues or feature requests, please open an issue in the GitHub repository.
