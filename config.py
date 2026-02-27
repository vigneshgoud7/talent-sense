"""
DEET System Configuration
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'models')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Database
DATABASE_PATH = os.path.join(DATA_DIR, 'deet_jobs.db')

# Scraping
SCRAPE_INTERVAL_MINUTES = 60
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
USER_AGENT_ROTATE = True

# NLP
MIN_DESCRIPTION_LENGTH = 50
SUPPORTED_LANGUAGES = ['en']

# ML Classification
JOB_CATEGORIES = [
    'Software Engineering',
    'Data Science',
    'Product Management',
    'Design',
    'Marketing',
    'Sales',
    'Human Resources',
    'Finance',
    'Operations',
    'Customer Support',
    'DevOps',
    'Quality Assurance',
    'Business Analysis',
    'Project Management',
    'Other'
]

# Employer Verification
VERIFICATION_EXPIRY_DAYS = 90
AUTO_VERIFY_THRESHOLD = 0.85

# Career Pages to Monitor (Default)
DEFAULT_CAREER_PAGES = [
    {
        'company': 'Google',
        'url': 'https://careers.google.com/jobs/results/',
        'domain': 'google.com',
        'industry': 'Technology'
    },
    {
        'company': 'Microsoft',
        'url': 'https://careers.microsoft.com/professionals/us/en/search-results',
        'domain': 'microsoft.com',
        'industry': 'Technology'
    },
    {
        'company': 'Amazon',
        'url': 'https://www.amazon.jobs/en/search',
        'domain': 'amazon.com',
        'industry': 'Technology'
    },
    {
        'company': 'Apple',
        'url': 'https://jobs.apple.com/en-us/search',
        'domain': 'apple.com',
        'industry': 'Technology'
    },
    {
        'company': 'Meta',
        'url': 'https://www.metacareers.com/jobs',
        'domain': 'meta.com',
        'industry': 'Technology'
    },
    {
        'company': 'Netflix',
        'url': 'https://jobs.netflix.com/search',
        'domain': 'netflix.com',
        'industry': 'Entertainment'
    },
    {
        'company': 'Salesforce',
        'url': 'https://careers.salesforce.com/en/jobs/',
        'domain': 'salesforce.com',
        'industry': 'Technology'
    },
    {
        'company': 'IBM',
        'url': 'https://www.ibm.com/careers/search',
        'domain': 'ibm.com',
        'industry': 'Technology'
    },
    {
        'company': 'Oracle',
        'url': 'https://www.oracle.com/careers/',
        'domain': 'oracle.com',
        'industry': 'Technology'
    },
    {
        'company': 'Adobe',
        'url': 'https://careers.adobe.com/us/en/search-results',
        'domain': 'adobe.com',
        'industry': 'Technology'
    }
]

# Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'deet-secret-key-2026')
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000
