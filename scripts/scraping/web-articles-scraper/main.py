import os
import requests
from bs4 import BeautifulSoup
from google.colab import drive
from urllib.parse import urljoin, urlparse
import time
import re
import random
import json
from datetime import datetime

# Mount Google Drive
drive.mount('/content/drive', force_remount=True)

# Configuration
BASE_URL = "website URL"
SAVE_DIR = "/content/drive/MyDrive/All_Articles/"  # Single folder for all articles
CACHE_FILE = os.path.join(SAVE_DIR, "scraper_cache.json")  # Cache in the same folder
os.makedirs(SAVE_DIR, exist_ok=True)

# Enhanced stealth configuration
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
]

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1'
}

# Initialize session
session = requests.Session()
session.headers.update({'User-Agent': random.choice(USER_AGENTS)})

def load_cache():
    """Load cached URLs from the single folder"""
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_cache(cache):
    """Save cache to the single folder"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(cache), f, ensure_ascii=False)

def get_soup(url, retries=3):
    """Stealthy request with retries"""
    cache = load_cache()
    if url in cache:
        return None

    for attempt in range(retries):
        try:
            # Random delay with exponential backoff
            delay = random.uniform(1, 3) * (attempt + 1)
            time.sleep(delay)

            # Rotate headers and user agent
            session.headers.update({
                'User-Agent': random.choice(USER_AGENTS),
                'Referer': random.choice([BASE_URL, 'https://www.google.com/', 'https://www.bing.com/'])
            })

            response = session.get(url, headers=HEADERS, timeout=(10, 15))

            if response.status_code == 403:
                print(f"Block detected, rotating...")
                time.sleep(10)
                continue

            response.raise_for_status()

            if 'text/html' not in response.headers.get('content-type', ''):
                return None

            # Random human-like delay
            time.sleep(random.uniform(0.5, 1.5))

            cache.add(url)
            save_cache(cache)

            return BeautifulSoup(response.text, 'html.parser')

        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {url}: {str(e)[:200]}")
            if attempt == retries - 1:
                return None

def extract_article_links(soup):
    """Find all article links on a page"""
    article_links = set()

    # Multiple detection methods
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href or href.startswith(('mailto:', 'javascript:', '#')):
            continue

        full_url = urljoin(BASE_URL, href)
        parsed = urlparse(full_url)

        # Validate URL
        if (parsed.netloc == urlparse(BASE_URL).netloc and
            not any(ext in full_url.lower() for ext in ['.jpg', '.png', '.pdf', '.jpeg', '.mp3', '.mp4']) and
            not any(part in full_url.lower() for part in ['wp-admin', 'wp-login', 'feed', 'author', 'tag'])):

            article_links.add(full_url)

    return article_links

def extract_article_content(soup):
    """Extract complete article content"""
    # Title extraction
    title = ""
    for selector in [
        {'name': 'h1', 'class_': re.compile('entry-title|post-title|article-title')},
        {'property': 'og:title'},
        {'name': 'h1'},
        {'name': 'title'}
    ]:
        title_tag = soup.find(**selector)
        if title_tag:
            title = clean_text(title_tag.get_text())
            if title:
                break

    # Content extraction
    content = ""
    for selector in [
        {'class_': re.compile('entry-content|post-content|article-content|content-area')},
        {'itemprop': 'articleBody'},
        {'id': re.compile('content|article|main|primary')}
    ]:
        content_div = soup.find('article', **selector) or soup.find('div', **selector)
        if content_div:
            # Clean content
            for element in content_div.find_all(['script', 'style', 'iframe', 'nav',
                                              'footer', 'aside', 'form', 'button',
                                              'ul', 'ol', 'share', 'social', 'related']):
                element.decompose()

            content = clean_text(content_div.get_text(separator='\n'))
            break

    # Metadata
    date_published = ""
    for selector in [
        {'class_': re.compile('entry-date|post-date|date')},
        {'itemprop': 'datePublished'},
        {'property': 'article:published_time'}
    ]:
        date_tag = soup.find(**selector)
        if date_tag:
            date_published = clean_text(date_tag.get('content', date_tag.get_text()))
            break

    return {
        'title': title or "No Title",
        'content': content or "No Content",
        'date': date_published,
        'url': soup.find('link', {'rel': 'canonical'})['href'] if soup.find('link', {'rel': 'canonical'}) else ""
    }

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""

    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove common boilerplate
    boilerplate = ["Share this:", "Like this:", "Related", "Tweet", "Print",
                  "Email"]
    for phrase in boilerplate:
        text = text.replace(phrase, '')

    return text

def save_article(article, index):
    """Save article to the single folder with sequential numbering"""
    # Clean filename (using index for consistent ordering)
    filename = f"article_{index:05d}.txt"
    filepath = os.path.join(SAVE_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"URL: {article['url']}\n")
            f.write(f"Title: {article['title']}\n")
            f.write(f"Date: {article['date']}\n\n")
            f.write(article['content'])
        print(f"Saved: {filename}")
    except Exception as e:
        print(f"Failed to save {filename}: {e}")

def scrape_all_articles():
    """Main scraping function that saves everything in one folder"""
    print(f"Starting full website scrape at {datetime.now().isoformat()}")

    all_articles = set()
    processed_urls = load_cache()
    queue = [BASE_URL]
    article_count = 0

    # BFS website crawl
    while queue and article_count < 5000:  # Safety limit
        current_url = queue.pop(0)

        if current_url in processed_urls:
            continue

        print(f"\nProcessing: {current_url}")

        soup = get_soup(current_url)
        if not soup:
            continue

        # Find all links
        links = extract_article_links(soup)
        new_articles = [link for link in links if link not in processed_urls]

        # Add listing pages to queue
        if not re.search(r'/\d{4}/\d{2}/[^/]+/$', current_url):  # Not an article URL
            for link in links:
                if link not in queue and link not in processed_urls:
                    queue.append(link)

        # Process articles
        for article_url in new_articles:
            print(f"\nScraping article {article_count + 1}: {article_url}")

            article_soup = get_soup(article_url)
            if not article_soup:
                continue

            article_data = extract_article_content(article_soup)
            save_article(article_data, article_count + 1)
            article_count += 1

            # Human-like delay pattern
            time.sleep(random.choice([1.2, 1.5, 1.8, 2.0, 2.3, 2.7]))

            # Periodic cache save
            if article_count % 10 == 0:
                save_cache(processed_urls)

    print(f"\nScraping completed at {datetime.now().isoformat()}")
    print(f"Total articles saved: {article_count}")
    print(f"All articles saved in: {SAVE_DIR}")
