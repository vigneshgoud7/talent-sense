"""
Career Page Scraper — Scrapes real job listings from company career pages.
Uses BeautifulSoup for HTML parsing + requests for HTTP.
Supports multiple career page formats with fallback strategies.
"""
import requests
import json
import re
import hashlib
import time
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

try:
    ua = UserAgent()
except:
    ua = None

def get_headers():
    """Get randomized request headers."""
    if ua:
        user_agent = ua.random
    else:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    return {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

def scrape_remoteok():
    """Scrape RemoteOK API for remote jobs."""
    jobs = []
    try:
        headers = get_headers()
        headers['Accept'] = 'application/json'
        resp = requests.get('https://remoteok.com/api', headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for item in data[1:]:  # Skip first item (meta)
                if isinstance(item, dict) and item.get('position'):
                    skills = []
                    if item.get('tags'):
                        skills = item['tags'] if isinstance(item['tags'], list) else [item['tags']]
                    jobs.append({
                        'external_id': f"rok_{item.get('id', '')}",
                        'title': item.get('position', '').strip(),
                        'company': item.get('company', 'Unknown').strip(),
                        'location': item.get('location', 'Remote').strip() or 'Remote',
                        'job_type': 'Full-time',
                        'description': clean_html(item.get('description', '')),
                        'skills': skills,
                        'source_url': item.get('url', ''),
                        'apply_url': item.get('apply_url') or item.get('url', ''),
                        'salary_range': item.get('salary', ''),
                        'posted_date': item.get('date', ''),
                        'source': 'RemoteOK'
                    })
    except Exception as e:
        print(f"[RemoteOK] Error: {e}")
    return jobs

def scrape_github_jobs():
    """Scrape GitHub Jobs (via alternative sources)."""
    jobs = []
    try:
        headers = get_headers()
        resp = requests.get(
            'https://jobs.github.com/positions.json?description=&location=',
            headers=headers, timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data:
                jobs.append({
                    'external_id': f"gh_{item.get('id', '')}",
                    'title': item.get('title', '').strip(),
                    'company': item.get('company', 'Unknown').strip(),
                    'location': item.get('location', 'Remote').strip(),
                    'job_type': item.get('type', 'Full-time'),
                    'description': clean_html(item.get('description', '')),
                    'skills': [],
                    'source_url': item.get('url', ''),
                    'apply_url': item.get('how_to_apply', ''),
                    'posted_date': item.get('created_at', ''),
                    'source': 'GitHub Jobs'
                })
    except Exception as e:
        print(f"[GitHub Jobs] Error: {e}")
    return jobs

def scrape_arbeitnow():
    """Scrape Arbeitnow API for jobs."""
    jobs = []
    try:
        headers = get_headers()
        resp = requests.get('https://www.arbeitnow.com/api/job-board-api', headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get('data', []):
                skills = item.get('tags', [])
                jobs.append({
                    'external_id': f"an_{item.get('slug', '')}",
                    'title': item.get('title', '').strip(),
                    'company': item.get('company_name', 'Unknown').strip(),
                    'location': item.get('location', 'Remote').strip(),
                    'job_type': 'Remote' if item.get('remote', False) else 'Full-time',
                    'description': clean_html(item.get('description', '')),
                    'skills': skills if isinstance(skills, list) else [],
                    'source_url': item.get('url', ''),
                    'apply_url': item.get('url', ''),
                    'posted_date': item.get('created_at', ''),
                    'source': 'Arbeitnow'
                })
    except Exception as e:
        print(f"[Arbeitnow] Error: {e}")
    return jobs

def scrape_findwork():
    """Scrape Findwork.dev API."""
    jobs = []
    try:
        headers = get_headers()
        resp = requests.get('https://findwork.dev/api/jobs/', headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get('results', []):
                skills = item.get('keywords', [])
                jobs.append({
                    'external_id': f"fw_{item.get('id', '')}",
                    'title': item.get('role', '').strip(),
                    'company': item.get('company_name', 'Unknown').strip(),
                    'location': item.get('location', 'Remote').strip() or 'Remote',
                    'job_type': 'Remote' if item.get('remote', False) else 'Full-time',
                    'description': clean_html(item.get('text', '')),
                    'skills': skills if isinstance(skills, list) else [],
                    'source_url': item.get('url', ''),
                    'apply_url': item.get('url', ''),
                    'posted_date': item.get('date_posted', ''),
                    'source': 'Findwork'
                })
    except Exception as e:
        print(f"[Findwork] Error: {e}")
    return jobs

def scrape_generic_career_page(url, company_name):
    """Generic career page scraper using BeautifulSoup."""
    jobs = []
    try:
        headers = get_headers()
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            return jobs

        soup = BeautifulSoup(resp.text, 'lxml')

        # Try to find job listing patterns
        job_elements = find_job_elements(soup)

        for idx, elem in enumerate(job_elements[:50]):  # Max 50 per page
            title = extract_title(elem)
            location = extract_location(elem)
            link = extract_link(elem, url)

            if title and len(title) > 3:
                jobs.append({
                    'external_id': f"gen_{hashlib.md5((title + company_name).encode()).hexdigest()[:12]}",
                    'title': title,
                    'company': company_name,
                    'location': location or 'Not Specified',
                    'job_type': 'Full-time',
                    'description': extract_description(elem),
                    'skills': [],
                    'source_url': url,
                    'apply_url': link or url,
                    'posted_date': datetime.utcnow().isoformat(),
                    'source': f'{company_name} Career Page'
                })
    except Exception as e:
        print(f"[{company_name}] Scraping error: {e}")
    return jobs

def find_job_elements(soup):
    """Find job listing elements in HTML using common patterns."""
    selectors = [
        'div[class*="job"]', 'li[class*="job"]', 'tr[class*="job"]',
        'div[class*="position"]', 'li[class*="position"]',
        'div[class*="opening"]', 'li[class*="opening"]',
        'div[class*="vacancy"]', 'li[class*="vacancy"]',
        'div[class*="listing"]', 'li[class*="listing"]',
        'div[class*="career"]', 'article[class*="job"]',
        '.job-listing', '.job-card', '.position-card',
        '[data-job]', '[data-position]'
    ]
    for selector in selectors:
        elements = soup.select(selector)
        if len(elements) >= 2:  # Likely a list of jobs
            return elements
    return []

def extract_title(elem):
    """Extract job title from an element."""
    title_selectors = [
        'h2', 'h3', 'h4', 'a[class*="title"]', '[class*="title"]',
        'a[class*="job"]', '.job-title', '.position-title', 'a'
    ]
    for sel in title_selectors:
        found = elem.select_one(sel)
        if found and found.get_text(strip=True):
            text = found.get_text(strip=True)
            if len(text) > 3 and len(text) < 200:
                return text
    return elem.get_text(strip=True)[:100] if elem.get_text(strip=True) else None

def extract_location(elem):
    """Extract location from an element."""
    loc_selectors = [
        '[class*="location"]', '[class*="loc"]', '[class*="city"]',
        '[class*="region"]', '[data-location]', 'span[class*="meta"]'
    ]
    for sel in loc_selectors:
        found = elem.select_one(sel)
        if found and found.get_text(strip=True):
            return found.get_text(strip=True)
    return None

def extract_link(elem, base_url):
    """Extract job detail link."""
    link = elem.select_one('a[href]')
    if link:
        href = link.get('href', '')
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{href}"
    return None

def extract_description(elem):
    """Extract description text from element."""
    desc_selectors = [
        '[class*="description"]', '[class*="summary"]', '[class*="snippet"]',
        'p', '[class*="detail"]'
    ]
    for sel in desc_selectors:
        found = elem.select_one(sel)
        if found and found.get_text(strip=True):
            return found.get_text(strip=True)
    return ''

def clean_html(html_text):
    """Clean HTML tags from text."""
    if not html_text:
        return ''
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ── Master Scrape Function ─────────────────────────────────────────────
def scrape_all_sources():
    """
    Scrape all configured sources. Returns dict with results per source.
    """
    results = {}
    sources = [
        ('RemoteOK', scrape_remoteok),
        ('Arbeitnow', scrape_arbeitnow),
    ]

    for name, scraper_fn in sources:
        print(f"[Scraper] Scraping {name}...")
        try:
            jobs = scraper_fn()
            results[name] = {
                'jobs': jobs,
                'count': len(jobs),
                'status': 'success' if jobs else 'no_results',
                'timestamp': datetime.utcnow().isoformat()
            }
            print(f"[Scraper] {name}: Found {len(jobs)} jobs")
        except Exception as e:
            results[name] = {
                'jobs': [],
                'count': 0,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
            print(f"[Scraper] {name}: Error - {e}")
        time.sleep(random.uniform(1, 3))  # Rate limiting

    return results

def scrape_single_source(source_name):
    """Scrape a specific source by name."""
    source_map = {
        'remoteok': scrape_remoteok,
        'arbeitnow': scrape_arbeitnow,
        'findwork': scrape_findwork,
    }
    fn = source_map.get(source_name.lower())
    if fn:
        return fn()
    return []

# Source metadata for the UI
SCRAPE_SOURCES = [
    {
        'id': 'remoteok',
        'name': 'RemoteOK',
        'url': 'https://remoteok.com',
        'type': 'API',
        'description': 'Top remote job board with REST API',
        'icon': '🌐'
    },
    {
        'id': 'arbeitnow',
        'name': 'Arbeitnow',
        'url': 'https://www.arbeitnow.com',
        'type': 'API',
        'description': 'European job board with public API',
        'icon': '🇪🇺'
    },
    {
        'id': 'findwork',
        'name': 'Findwork',
        'url': 'https://findwork.dev',
        'type': 'API',
        'description': 'Developer-focused job board API',
        'icon': '�'
    },
    {
        'id': 'google',
        'name': 'Google Careers',
        'url': 'https://careers.google.com',
        'type': 'Career Page',
        'description': 'Google official career page',
        'icon': '�'
    },
    {
        'id': 'microsoft',
        'name': 'Microsoft Careers',
        'url': 'https://careers.microsoft.com',
        'type': 'Career Page',
        'description': 'Microsoft official career page',
        'icon': '🪟'
    },
    {
        'id': 'amazon',
        'name': 'Amazon Jobs',
        'url': 'https://www.amazon.jobs',
        'type': 'Career Page',
        'description': 'Amazon official job portal',
        'icon': '📦'
    },
    {
        'id': 'meta',
        'name': 'Meta Careers',
        'url': 'https://www.metacareers.com',
        'type': 'Career Page',
        'description': 'Meta/Facebook official careers',
        'icon': '🔵'
    },
    {
        'id': 'apple',
        'name': 'Apple Jobs',
        'url': 'https://jobs.apple.com',
        'type': 'Career Page',
        'description': 'Apple official job openings',
        'icon': '🍎'
    },
    {
        'id': 'netflix',
        'name': 'Netflix Jobs',
        'url': 'https://jobs.netflix.com',
        'type': 'Career Page',
        'description': 'Netflix official career page',
        'icon': '🎬'
    },
    {
        'id': 'ibm',
        'name': 'IBM Careers',
        'url': 'https://www.ibm.com/careers',
        'type': 'Career Page',
        'description': 'IBM official careers portal',
        'icon': '�️'
    },
]
