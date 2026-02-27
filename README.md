<p align="center">
  <h1 align="center">🏛️ DEET — Job Vacancy Discovery System</h1>
  <p align="center">
    <strong>An autonomous, intelligent platform for scraping, processing, and analyzing job vacancies from major career pages.</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white" alt="Flask">
    <img src="https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite">
    <img src="https://img.shields.io/badge/scikit--learn-1.3-F7931E?style=flat-square&logo=scikit-learn&logoColor=white" alt="scikit-learn">
    <img src="https://img.shields.io/badge/NLTK-3.8-154F5B?style=flat-square" alt="NLTK">
    <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
  </p>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Modules](#-modules)
- [Configuration](#-configuration)
- [Screenshots](#-screenshots)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Overview

**DEET (Data-Enriched Employment Tracker)** is a fully automated workforce intelligence platform that discovers, scrapes, classifies, and analyzes job vacancies from 10+ major company career pages — all with **zero manual input**.

The system combines **web scraping**, **Natural Language Processing (NLP)**, and **Machine Learning (ML)** to provide real-time insights into the job market, including skill demand trends, hiring patterns, and employer trust verification.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🤖 **Autonomous Scraping** | Automatically scrapes jobs from RemoteOK, Arbeitnow, Findwork, GitHub Jobs, and major career pages (Google, Microsoft, Amazon, Apple, Meta, Netflix, etc.) |
| 🧠 **NLP Processing** | Extracts skills, experience levels, salary info, job types, and categories from raw job descriptions using regex-based NLP |
| 🔬 **ML Deduplication** | TF-IDF vectorization + cosine similarity to detect and eliminate duplicate job postings |
| ✅ **Auto Employer Verification** | Multi-signal verification pipeline (domain check, career page validation, company name matching, job count scoring) runs on startup and after every scrape |
| 📊 **Workforce Intelligence Dashboard** | Real-time metrics, category distribution charts, top hiring companies, and scrape monitoring |
| ⏱️ **Scheduled Scraping** | Built-in scheduler for periodic automated scraping with configurable intervals |
| 🔍 **Advanced Filtering** | Search and filter jobs by company, category, location, status, and keywords |
| 📝 **Audit Logging** | Complete audit trail of all system actions for transparency and debugging |
| 🛡️ **Rate Limiting** | Randomized User-Agent rotation and request throttling for respectful scraping |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DEET System Architecture                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ Scraper  │───▶│   NLP    │───▶│    ML    │───▶│    Database      │  │
│  │ Module   │    │ Extractor│    │Classifier│    │   (SQLite)       │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────────────┘  │
│       │                                                   │             │
│       │          ┌──────────┐                             │             │
│       ├─────────▶│Scheduler │                             │             │
│       │          └──────────┘                             ▼             │
│       │                                          ┌──────────────────┐  │
│       │          ┌──────────┐                    │   Flask Web App  │  │
│       └─────────▶│Employer  │───────────────────▶│   (Frontend)     │  │
│                  │Verifier  │                    └──────────────────┘  │
│                  └──────────┘                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. **Scraper** pulls raw job listings from APIs and career pages
2. **NLP Extractor** enriches each job with skills, experience, salary, and category
3. **ML Classifier** detects and flags duplicate postings using TF-IDF + cosine similarity
4. **Database** stores deduplicated, enriched job data
5. **Employer Verifier** validates employer legitimacy automatically
6. **Flask App** serves a real-time dashboard and REST API

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.10+, Flask 3.0 | Web server, REST API, application logic |
| **Database** | SQLite 3 | Persistent storage for jobs, employers, scrape runs, audit logs |
| **Scraping** | Requests, BeautifulSoup4, lxml | HTTP requests and HTML parsing |
| **NLP** | NLTK, Regex patterns | Skill extraction, salary parsing, job classification |
| **ML** | scikit-learn (TF-IDF), NumPy | Duplicate detection via cosine similarity |
| **Scheduling** | Custom SimpleScheduler (threading) | Periodic automated scraping |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) | Dashboard, job listings, employer management, reports |
| **User-Agent** | fake-useragent | Randomized request headers for stealth scraping |

---

## 📁 Project Structure

```
deet_system/
│
├── app.py                    # Main Flask application & route definitions
├── config.py                 # System configuration & constants
├── requirements.txt          # Python dependencies
│
├── database/
│   ├── __init__.py
│   └── db_manager.py         # SQLite CRUD operations (jobs, employers, runs, audit)
│
├── scraper/
│   ├── __init__.py
│   └── career_scraper.py     # Multi-source career page scraper
│
├── nlp/
│   ├── __init__.py
│   └── job_extractor.py      # NLP pipeline (skills, salary, experience, category)
│
├── ml/
│   ├── __init__.py
│   └── classifier.py         # TF-IDF vectorizer & duplicate detection engine
│
├── verification/
│   ├── __init__.py
│   └── employer_verifier.py  # Multi-signal employer verification pipeline
│
├── scheduler/
│   ├── __init__.py
│   └── job_scheduler.py      # Periodic scraping scheduler
│
├── templates/
│   ├── base.html              # Base layout (sidebar, navigation)
│   ├── dashboard.html         # Workforce Intelligence Dashboard
│   ├── jobs.html              # Job Listings with filters
│   ├── employers.html         # Employer verification dashboard
│   ├── monitor.html           # Scrape monitoring & live status
│   └── reports.html           # Analytics & reports
│
├── static/
│   └── css/
│       └── (stylesheets)
│
└── data/
    └── deet_jobs.db           # SQLite database (auto-generated)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed on your system
- **pip** package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd deet_system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**

   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in your browser**
   ```
   http://localhost:5000
   ```

> **Note:** On first launch, the system will automatically:
> - Initialize the SQLite database
> - Seed 10 default employers (Google, Microsoft, Amazon, Apple, Meta, Netflix, IBM, Oracle, Salesforce, Adobe)
> - Run employer verification in the background

---

## 💡 Usage

### Dashboard
The main dashboard (`/`) displays real-time workforce intelligence:
- **Total Jobs**, **Active Jobs**, **Employers**, **Pending Reviews**, **Duplicates Caught**
- Job category distribution chart
- Top hiring companies

### Discover Jobs
Click the **"Discover Jobs"** button on the dashboard (or use the API) to trigger a scrape. The system will:
1. Scrape configured sources (RemoteOK, Arbeitnow, etc.)
2. Process each job through the NLP pipeline
3. Run ML-based deduplication
4. Store new unique jobs in the database
5. Auto-verify any newly discovered employers

### Job Listings
Browse all scraped jobs at `/jobs` with filters for:
- **Search** (keyword)
- **Company**
- **Category** (Software Engineering, Data Science, DevOps, etc.)
- **Location**
- **Status**

### Employers
View employer verification status at `/employers`. Each employer shows:
- Trust score (0–100%)
- Verification status (Verified / Pending / Flagged)
- Domain, career page, and industry info

### Monitor
Track scraping activity at `/monitor`:
- Live scrape progress
- Scrape run history
- Source-by-source results

### Reports
View analytics and insights at `/reports`:
- Skill demand trends
- Category breakdowns
- Hiring velocity

---

## 📡 API Reference

All endpoints return JSON responses.

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/stats` | System-wide statistics and scrape status |

### Jobs
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/jobs` | Paginated job listings (supports `?search=`, `?company=`, `?category=`, `?location=`, `?status=`, `?page=`, `?per_page=`) |
| `GET` | `/api/jobs/<id>` | Single job details |

### Employers
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/employers` | All employers (optional `?status=` filter) |
| `POST` | `/api/employers/<id>/verify` | Manually verify an employer (`{ "status": "verified", "notes": "..." }`) |
| `POST` | `/api/employers/<id>/auto-verify` | Trigger automatic verification for an employer |

### Scraping
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scrape/start` | Start a scrape (`{ "sources": ["remoteok", "arbeitnow"] }`) |
| `GET` | `/api/scrape/status` | Live scrape progress |
| `GET` | `/api/scrape/history` | Past scrape run details |

### Sources & Pages
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/sources` | List all configured scrape sources |
| `GET` | `/api/career-pages` | List monitored career pages |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/skills/summary` | Aggregated skill demand summary |
| `GET` | `/api/audit-logs` | System audit trail |

---

## 🧩 Modules

### 🕷️ Scraper (`scraper/career_scraper.py`)
- Scrapers for **RemoteOK** (REST API), **Arbeitnow** (REST API), **Findwork** (REST API), **GitHub Jobs** (alternative)
- Generic HTML career page scraper using BeautifulSoup
- Randomized User-Agent headers via `fake-useragent`
- Rate limiting between requests
- Supports 10+ configured source endpoints

### 🧠 NLP Extractor (`nlp/job_extractor.py`)
- **Skill Extraction** — Matches against 100+ technical & soft skills across 7 categories (Programming, Web/Mobile, Data, Cloud, DevOps, Security, Soft Skills)
- **Experience Level Detection** — Classifies as Entry, Mid, Senior, or Executive
- **Salary Parsing** — Extracts salary ranges in USD/EUR/GBP with period detection
- **Job Type Detection** — Full-time, Part-time, Contract, Freelance, Internship, Temporary
- **Category Classification** — Maps jobs to 15 categories using regex pattern rules
- **Location Normalization** — Standardizes "Remote", city/state/country formats
- **Confidence Scoring** — Rates data quality (0–1) based on field completeness

### 🔬 ML Classifier (`ml/classifier.py`)
- **TF-IDF Vectorizer** — Converts job text (title + company + description + skills) into 5000-feature vectors
- **Cosine Similarity** — Pairwise similarity matrix for duplicate detection (threshold: 0.85)
- **Fingerprint Matching** — MD5 hash of normalized title + company + location for exact-match deduplication
- **DuplicateTracker** — In-memory set of seen job fingerprints to prevent re-insertion across scrape runs

### ✅ Employer Verifier (`verification/employer_verifier.py`)
Multi-signal verification pipeline:
| Check | Weight | Description |
|---|---|---|
| Domain Reachability | 30% | HTTPS/HTTP HEAD request to company domain |
| Career Page Validation | 20% | Checks for job-related keywords on career page |
| Career Page Keywords | 15% | Scans for terms like "career", "apply", "hiring" |
| Name-Domain Match | 20% | Exact or partial match between company name and domain |
| Job Count Score | 15% | Bonus points for employers with 1+, 3+, 10+ posted jobs |

**Auto-verification** runs on startup and after every scrape. Employers scoring ≥ 40% are auto-verified.

### ⏱️ Scheduler (`scheduler/job_scheduler.py`)
- Configurable interval (default: 60 minutes)
- Runs in a background daemon thread
- Supports multiple callback functions
- Provides status API (running/stopped, last run, next run)

### 💾 Database (`database/db_manager.py`)
SQLite-based storage with tables for:
- **jobs** — Scraped and enriched job listings
- **employers** — Company records with verification status
- **scrape_runs** — Scrape execution history and results
- **career_pages** — Monitored career page URLs
- **audit_log** — Complete system action log
- **verification_history** — Employer verification audit trail

---

## ⚙️ Configuration

All configuration is managed in `config.py`:

```python
# Scraping
SCRAPE_INTERVAL_MINUTES = 60       # Auto-scrape interval
REQUEST_TIMEOUT = 30               # HTTP request timeout (seconds)
MAX_RETRIES = 3                    # Max retry attempts per request
USER_AGENT_ROTATE = True           # Randomize User-Agent headers

# NLP
MIN_DESCRIPTION_LENGTH = 50        # Min chars for NLP processing
SUPPORTED_LANGUAGES = ['en']       # Supported languages

# ML Classification
JOB_CATEGORIES = [                 # 15 job categories
    'Software Engineering', 'Data Science', 'Product Management',
    'Design', 'Marketing', 'Sales', 'Human Resources', 'Finance',
    'Operations', 'Customer Support', 'DevOps', 'Quality Assurance',
    'Business Analysis', 'Project Management', 'Other'
]

# Employer Verification
VERIFICATION_EXPIRY_DAYS = 90      # Re-verify after 90 days
AUTO_VERIFY_THRESHOLD = 0.85       # Trust score threshold

# Server
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True
```

---

## 🖼️ Screenshots

Once the application is running, visit:

| Page | URL |
|---|---|
| Dashboard | `http://localhost:5000/` |
| Job Listings | `http://localhost:5000/jobs` |
| Employers | `http://localhost:5000/employers` |
| Monitor | `http://localhost:5000/monitor` |
| Reports | `http://localhost:5000/reports` |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "Add your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for automated workforce intelligence
</p>
