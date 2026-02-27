"""
Database Manager — SQLite CRUD operations for DEET System
Manages jobs, employers, scrape runs, and audit logs.
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'deet_jobs.db')

def ensure_data_dir():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

@contextmanager
def get_connection():
    ensure_data_dir()
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize all database tables."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS employers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                domain TEXT UNIQUE,
                career_url TEXT,
                industry TEXT DEFAULT 'Technology',
                description TEXT,
                logo_url TEXT,
                verification_status TEXT DEFAULT 'pending',
                verification_score REAL DEFAULT 0.0,
                verified_at TEXT,
                verified_by TEXT,
                rejection_reason TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                employer_id INTEGER,
                location TEXT,
                job_type TEXT,
                experience_level TEXT,
                salary_range TEXT,
                description TEXT,
                requirements TEXT,
                skills TEXT,
                category TEXT DEFAULT 'Other',
                source_url TEXT,
                apply_url TEXT,
                status TEXT DEFAULT 'active',
                is_duplicate INTEGER DEFAULT 0,
                duplicate_of INTEGER,
                confidence_score REAL DEFAULT 0.0,
                posted_date TEXT,
                discovered_at TEXT DEFAULT (datetime('now')),
                last_seen TEXT DEFAULT (datetime('now')),
                scrape_run_id INTEGER,
                FOREIGN KEY (employer_id) REFERENCES employers(id),
                FOREIGN KEY (duplicate_of) REFERENCES jobs(id)
            );

            CREATE TABLE IF NOT EXISTS scrape_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employer_id INTEGER,
                company_name TEXT,
                career_url TEXT,
                status TEXT DEFAULT 'running',
                jobs_found INTEGER DEFAULT 0,
                jobs_new INTEGER DEFAULT 0,
                jobs_duplicate INTEGER DEFAULT 0,
                errors TEXT,
                started_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT,
                duration_seconds REAL,
                FOREIGN KEY (employer_id) REFERENCES employers(id)
            );

            CREATE TABLE IF NOT EXISTS career_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employer_id INTEGER,
                url TEXT NOT NULL,
                company_name TEXT,
                is_active INTEGER DEFAULT 1,
                last_scraped TEXT,
                last_change_detected TEXT,
                scrape_frequency_minutes INTEGER DEFAULT 60,
                page_hash TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (employer_id) REFERENCES employers(id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,
                user_agent TEXT DEFAULT 'system',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS verification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employer_id INTEGER NOT NULL,
                previous_status TEXT,
                new_status TEXT,
                action_by TEXT DEFAULT 'system',
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (employer_id) REFERENCES employers(id)
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
            CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category);
            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_jobs_discovered ON jobs(discovered_at);
            CREATE INDEX IF NOT EXISTS idx_employers_status ON employers(verification_status);
            CREATE INDEX IF NOT EXISTS idx_employers_domain ON employers(domain);
        """)

def add_employer(name, domain, career_url, industry='Technology', description=''):
    """Add or update an employer."""
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM employers WHERE domain = ?", (domain,)).fetchone()
        if existing:
            conn.execute("""
                UPDATE employers SET name=?, career_url=?, industry=?, description=?, updated_at=datetime('now')
                WHERE domain=?
            """, (name, career_url, industry, description, domain))
            return existing['id']
        else:
            cursor = conn.execute("""
                INSERT INTO employers (name, domain, career_url, industry, description)
                VALUES (?, ?, ?, ?, ?)
            """, (name, domain, career_url, industry, description))
            return cursor.lastrowid

def add_job(job_data):
    """Insert a new job listing. Returns job ID or None if duplicate."""
    with get_connection() as conn:
        # Check for duplicates based on title + company + location
        existing = conn.execute("""
            SELECT id FROM jobs 
            WHERE title = ? AND company = ? AND location = ? AND is_duplicate = 0
        """, (job_data.get('title', ''), job_data.get('company', ''), job_data.get('location', ''))).fetchone()

        if existing:
            # Update last_seen
            conn.execute("UPDATE jobs SET last_seen = datetime('now') WHERE id = ?", (existing['id'],))
            return None  # Duplicate

        cursor = conn.execute("""
            INSERT INTO jobs (external_id, title, company, employer_id, location, job_type,
                experience_level, salary_range, description, requirements, skills,
                category, source_url, apply_url, status, confidence_score,
                posted_date, scrape_run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_data.get('external_id'),
            job_data.get('title', 'Untitled'),
            job_data.get('company', 'Unknown'),
            job_data.get('employer_id'),
            job_data.get('location', 'Remote'),
            job_data.get('job_type', 'Full-time'),
            job_data.get('experience_level', 'Mid-level'),
            job_data.get('salary_range'),
            job_data.get('description', ''),
            job_data.get('requirements', ''),
            json.dumps(job_data.get('skills', [])),
            job_data.get('category', 'Other'),
            job_data.get('source_url', ''),
            job_data.get('apply_url', ''),
            job_data.get('status', 'active'),
            job_data.get('confidence_score', 0.0),
            job_data.get('posted_date'),
            job_data.get('scrape_run_id')
        ))
        return cursor.lastrowid

def get_jobs(filters=None, page=1, per_page=20):
    """Get paginated job listings with optional filters."""
    with get_connection() as conn:
        query = "SELECT * FROM jobs WHERE is_duplicate = 0"
        params = []

        if filters:
            if filters.get('company'):
                query += " AND company LIKE ?"
                params.append(f"%{filters['company']}%")
            if filters.get('category'):
                query += " AND category = ?"
                params.append(filters['category'])
            if filters.get('location'):
                query += " AND location LIKE ?"
                params.append(f"%{filters['location']}%")
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            if filters.get('search'):
                query += " AND (title LIKE ? OR description LIKE ? OR skills LIKE ?)"
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term, search_term])

        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        total = conn.execute(count_query, params).fetchone()[0]

        query += " ORDER BY discovered_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])

        jobs = conn.execute(query, params).fetchall()
        return {
            'jobs': [dict(j) for j in jobs],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }

def get_job_by_id(job_id):
    with get_connection() as conn:
        job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(job) if job else None

def get_employers(status=None):
    with get_connection() as conn:
        if status:
            employers = conn.execute(
                "SELECT * FROM employers WHERE verification_status = ? ORDER BY created_at DESC", (status,)
            ).fetchall()
        else:
            employers = conn.execute("SELECT * FROM employers ORDER BY created_at DESC").fetchall()
        return [dict(e) for e in employers]

def update_employer_verification(employer_id, status, notes='', action_by='admin', score=None):
    with get_connection() as conn:
        emp = conn.execute("SELECT verification_status FROM employers WHERE id = ?", (employer_id,)).fetchone()
        prev_status = emp['verification_status'] if emp else 'unknown'

        if score is not None:
            conn.execute("""
                UPDATE employers SET verification_status=?, verification_score=?, verified_at=datetime('now'),
                verified_by=?, updated_at=datetime('now') WHERE id=?
            """, (status, score, action_by, employer_id))
        else:
            conn.execute("""
                UPDATE employers SET verification_status=?, verified_at=datetime('now'),
                verified_by=?, updated_at=datetime('now') WHERE id=?
            """, (status, action_by, employer_id))

        conn.execute("""
            INSERT INTO verification_history (employer_id, previous_status, new_status, action_by, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (employer_id, prev_status, status, action_by, notes))

        # Inline audit log to avoid opening a second connection (prevents 'database is locked')
        conn.execute("""
            INSERT INTO audit_logs (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
        """, ('verification_update', 'employer', employer_id,
              f"Status changed: {prev_status} -> {status}. {notes}"))

def start_scrape_run(company_name, career_url, employer_id=None):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO scrape_runs (employer_id, company_name, career_url, status)
            VALUES (?, ?, ?, 'running')
        """, (employer_id, company_name, career_url))
        return cursor.lastrowid

def complete_scrape_run(run_id, jobs_found, jobs_new, jobs_duplicate, errors=None):
    with get_connection() as conn:
        run = conn.execute("SELECT started_at FROM scrape_runs WHERE id = ?", (run_id,)).fetchone()
        duration = 0
        if run:
            started = datetime.fromisoformat(run['started_at'])
            duration = (datetime.utcnow() - started).total_seconds()

        conn.execute("""
            UPDATE scrape_runs SET status='completed', jobs_found=?, jobs_new=?,
            jobs_duplicate=?, errors=?, completed_at=datetime('now'), duration_seconds=?
            WHERE id=?
        """, (jobs_found, jobs_new, jobs_duplicate, errors, duration, run_id))

def get_scrape_runs(limit=20):
    with get_connection() as conn:
        runs = conn.execute(
            "SELECT * FROM scrape_runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in runs]

def get_dashboard_stats():
    with get_connection() as conn:
        stats = {}
        stats['total_jobs'] = conn.execute("SELECT COUNT(*) FROM jobs WHERE is_duplicate = 0").fetchone()[0]
        stats['active_jobs'] = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status = 'active' AND is_duplicate = 0"
        ).fetchone()[0]
        stats['total_employers'] = conn.execute("SELECT COUNT(*) FROM employers").fetchone()[0]
        stats['verified_employers'] = conn.execute(
            "SELECT COUNT(*) FROM employers WHERE verification_status = 'verified'"
        ).fetchone()[0]
        stats['pending_verification'] = conn.execute(
            "SELECT COUNT(*) FROM employers WHERE verification_status = 'pending'"
        ).fetchone()[0]

        today = datetime.utcnow().strftime('%Y-%m-%d')
        stats['jobs_today'] = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE DATE(discovered_at) = ? AND is_duplicate = 0", (today,)
        ).fetchone()[0]

        stats['total_scrape_runs'] = conn.execute("SELECT COUNT(*) FROM scrape_runs").fetchone()[0]
        stats['duplicates_caught'] = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE is_duplicate = 1"
        ).fetchone()[0]

        # Category distribution
        cats = conn.execute("""
            SELECT category, COUNT(*) as count FROM jobs 
            WHERE is_duplicate = 0 GROUP BY category ORDER BY count DESC
        """).fetchall()
        stats['categories'] = {r['category']: r['count'] for r in cats}

        # Top companies
        companies = conn.execute("""
            SELECT company, COUNT(*) as count FROM jobs 
            WHERE is_duplicate = 0 GROUP BY company ORDER BY count DESC LIMIT 10
        """).fetchall()
        stats['top_companies'] = {r['company']: r['count'] for r in companies}

        # Jobs per day (last 7 days)
        daily = conn.execute("""
            SELECT DATE(discovered_at) as day, COUNT(*) as count FROM jobs
            WHERE is_duplicate = 0 AND discovered_at >= datetime('now', '-7 days')
            GROUP BY DATE(discovered_at) ORDER BY day
        """).fetchall()
        stats['daily_trend'] = {r['day']: r['count'] for r in daily}

        # Recent jobs
        recent = conn.execute("""
            SELECT id, title, company, location, category, discovered_at 
            FROM jobs WHERE is_duplicate = 0 ORDER BY discovered_at DESC LIMIT 5
        """).fetchall()
        stats['recent_jobs'] = [dict(r) for r in recent]

        return stats

def log_audit(action, entity_type=None, entity_id=None, details=None):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO audit_logs (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
        """, (action, entity_type, entity_id, details))

def get_audit_logs(limit=50):
    with get_connection() as conn:
        logs = conn.execute(
            "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(l) for l in logs]

def add_career_page(url, company_name, employer_id=None, frequency=60):
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM career_pages WHERE url = ?", (url,)).fetchone()
        if existing:
            return existing['id']
        cursor = conn.execute("""
            INSERT INTO career_pages (employer_id, url, company_name, scrape_frequency_minutes)
            VALUES (?, ?, ?, ?)
        """, (employer_id, url, company_name, frequency))
        return cursor.lastrowid

def get_career_pages(active_only=True):
    with get_connection() as conn:
        if active_only:
            pages = conn.execute(
                "SELECT * FROM career_pages WHERE is_active = 1 ORDER BY company_name"
            ).fetchall()
        else:
            pages = conn.execute("SELECT * FROM career_pages ORDER BY company_name").fetchall()
        return [dict(p) for p in pages]

def get_verification_history(employer_id):
    with get_connection() as conn:
        history = conn.execute("""
            SELECT * FROM verification_history WHERE employer_id = ? ORDER BY created_at DESC
        """, (employer_id,)).fetchall()
        return [dict(h) for h in history]
