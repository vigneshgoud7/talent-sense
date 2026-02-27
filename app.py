"""
DEET Portal — Flask Web Application
Automated Job Vacancy Discovery System
"""
import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import (
    init_database, add_employer, add_job, get_jobs, get_job_by_id,
    get_employers, update_employer_verification, start_scrape_run,
    complete_scrape_run, get_scrape_runs, get_dashboard_stats,
    log_audit, get_audit_logs, add_career_page, get_career_pages
)
from scraper.career_scraper import scrape_all_sources, scrape_single_source, SCRAPE_SOURCES
from nlp.job_extractor import process_job, batch_process_jobs, get_skill_summary
from ml.classifier import classifier, duplicate_tracker
from verification.employer_verifier import run_full_verification
from scheduler.job_scheduler import scheduler

app = Flask(__name__)
app.secret_key = 'deet-secret-key-2026'

# ── Initialize Database ─────────────────────────────────────────────────
init_database()

# ── Seed Default Employers ──────────────────────────────────────────────
def seed_employers():
    """Seed default employer companies."""
    default_companies = [
        ('Google', 'google.com', 'https://careers.google.com', 'Technology'),
        ('Microsoft', 'microsoft.com', 'https://careers.microsoft.com', 'Technology'),
        ('Amazon', 'amazon.com', 'https://www.amazon.jobs', 'Technology'),
        ('Apple', 'apple.com', 'https://jobs.apple.com', 'Technology'),
        ('Meta', 'meta.com', 'https://www.metacareers.com', 'Technology'),
        ('Netflix', 'netflix.com', 'https://jobs.netflix.com', 'Entertainment'),
        ('IBM', 'ibm.com', 'https://www.ibm.com/careers', 'Technology'),
        ('Oracle', 'oracle.com', 'https://www.oracle.com/careers', 'Technology'),
        ('Salesforce', 'salesforce.com', 'https://careers.salesforce.com', 'Technology'),
        ('Adobe', 'adobe.com', 'https://careers.adobe.com', 'Technology'),
    ]
    for name, domain, url, industry in default_companies:
        employer_id = add_employer(name, domain, url, industry)
        add_career_page(url, name, employer_id)

seed_employers()
log_audit('system_startup', details='DEET System initialized')

# ── Auto-Verify All Employers ────────────────────────────────────────────
def auto_verify_all_employers():
    """Automatically verify all pending employers. No manual work needed."""
    try:
        employers = get_employers()
        for emp in employers:
            if emp.get('verification_status') == 'pending':
                try:
                    result = run_full_verification(emp)
                    new_status = result['recommended_status']
                    score = result['overall_score']
                    # Auto-set status based on score
                    if score >= 0.4:
                        new_status = 'verified'
                    update_employer_verification(
                        emp['id'], new_status,
                        f"Auto-verified. Score: {score:.0%}", 'auto_system',
                        score=score
                    )
                    print(f"[Auto-Verify] {emp['name']}: {new_status} (score: {score:.0%})")
                except Exception as e:
                    print(f"[Auto-Verify] {emp['name']}: Error - {e}")
    except Exception as e:
        print(f"[Auto-Verify] Failed: {e}")

# Run auto-verification on startup (background thread so it doesn't block)
def _startup_verify():
    import time
    time.sleep(2)  # Wait for server to be ready
    print("[Auto-Verify] Running automatic employer verification...")
    auto_verify_all_employers()
    print("[Auto-Verify] Complete!")

threading.Thread(target=_startup_verify, daemon=True).start()

# ── Global scrape state ──────────────────────────────────────────────────
scrape_status = {
    'is_running': False,
    'current_source': None,
    'progress': 0,
    'total_sources': 0,
    'results': {},
    'started_at': None,
    'completed_at': None,
    'total_jobs_found': 0,
    'total_new_jobs': 0,
    'total_duplicates': 0,
}

# ── Routes: Pages ────────────────────────────────────────────────────────
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/jobs')
def jobs_page():
    return render_template('jobs.html')

@app.route('/employers')
def employers_page():
    return render_template('employers.html')

@app.route('/monitor')
def monitor_page():
    return render_template('monitor.html')

@app.route('/reports')
def reports_page():
    return render_template('reports.html')

# ── API Routes ───────────────────────────────────────────────────────────

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    stats = get_dashboard_stats()
    stats['scrape_status'] = scrape_status
    return jsonify(stats)

@app.route('/api/jobs')
def api_get_jobs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    filters = {}
    if request.args.get('search'):
        filters['search'] = request.args['search']
    if request.args.get('company'):
        filters['company'] = request.args['company']
    if request.args.get('category'):
        filters['category'] = request.args['category']
    if request.args.get('location'):
        filters['location'] = request.args['location']
    if request.args.get('status'):
        filters['status'] = request.args['status']

    result = get_jobs(filters, page, per_page)
    # Parse skills JSON
    for job in result['jobs']:
        if isinstance(job.get('skills'), str):
            try:
                job['skills'] = json.loads(job['skills'])
            except:
                job['skills'] = []
    return jsonify(result)

@app.route('/api/jobs/<int:job_id>')
def api_get_job(job_id):
    job = get_job_by_id(job_id)
    if job:
        if isinstance(job.get('skills'), str):
            try:
                job['skills'] = json.loads(job['skills'])
            except:
                job['skills'] = []
        return jsonify(job)
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/employers')
def api_get_employers():
    status = request.args.get('status')
    employers = get_employers(status)
    return jsonify(employers)

@app.route('/api/employers/<int:employer_id>/verify', methods=['POST'])
def api_verify_employer(employer_id):
    data = request.json or {}
    status = data.get('status', 'verified')
    notes = data.get('notes', '')
    update_employer_verification(employer_id, status, notes)
    return jsonify({'success': True})

@app.route('/api/employers/<int:employer_id>/auto-verify', methods=['POST'])
def api_auto_verify(employer_id):
    employers = get_employers()
    employer = next((e for e in employers if e['id'] == employer_id), None)
    if not employer:
        return jsonify({'error': 'Employer not found'}), 404

    result = run_full_verification(employer)
    new_status = result['recommended_status']
    score = result['overall_score']
    if score >= 0.4:
        new_status = 'verified'
    update_employer_verification(employer_id, new_status,
        f"Auto-verified. Score: {score:.0%}", 'auto_system',
        score=score)
    return jsonify(result)

@app.route('/api/scrape/start', methods=['POST'])
def api_start_scrape():
    global scrape_status
    if scrape_status['is_running']:
        return jsonify({'error': 'Scrape already in progress'}), 409

    data = request.json or {}
    sources = data.get('sources', ['remoteok', 'arbeitnow'])

    def run_scrape():
        global scrape_status
        scrape_status = {
            'is_running': True,
            'current_source': None,
            'progress': 0,
            'total_sources': len(sources),
            'results': {},
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': None,
            'total_jobs_found': 0,
            'total_new_jobs': 0,
            'total_duplicates': 0,
        }

        all_jobs = []

        for idx, source in enumerate(sources):
            scrape_status['current_source'] = source
            scrape_status['progress'] = int((idx / len(sources)) * 100)

            source_info = next((s for s in SCRAPE_SOURCES if s['id'] == source), None)
            source_name = source_info['name'] if source_info else source

            run_id = start_scrape_run(source_name, source_info['url'] if source_info else '')

            try:
                jobs = scrape_single_source(source)
                # NLP processing
                processed_jobs = batch_process_jobs(jobs)
                # Deduplicate
                deduped = classifier.detect_duplicates(processed_jobs)

                new_count = 0
                dup_count = 0
                for job in deduped:
                    if job.get('is_duplicate'):
                        dup_count += 1
                        continue
                    if not duplicate_tracker.is_seen(job):
                        job_id = add_job(job)
                        if job_id:
                            new_count += 1
                            duplicate_tracker.mark_seen(job)
                        else:
                            dup_count += 1
                    else:
                        dup_count += 1

                complete_scrape_run(run_id, len(jobs), new_count, dup_count)
                scrape_status['results'][source] = {
                    'status': 'success',
                    'jobs_found': len(jobs),
                    'new_jobs': new_count,
                    'duplicates': dup_count
                }
                scrape_status['total_jobs_found'] += len(jobs)
                scrape_status['total_new_jobs'] += new_count
                scrape_status['total_duplicates'] += dup_count

                all_jobs.extend(deduped)

            except Exception as e:
                complete_scrape_run(run_id, 0, 0, 0, str(e))
                scrape_status['results'][source] = {
                    'status': 'error',
                    'error': str(e)
                }

            time.sleep(1)  # Rate limiting between sources

        scrape_status['is_running'] = False
        scrape_status['progress'] = 100
        scrape_status['completed_at'] = datetime.utcnow().isoformat()
        scrape_status['current_source'] = None

        log_audit('scrape_completed', details=json.dumps({
            'total_found': scrape_status['total_jobs_found'],
            'new': scrape_status['total_new_jobs'],
            'duplicates': scrape_status['total_duplicates']
        }))

        # Auto-verify any new employers discovered during scraping
        print("[Auto-Verify] Running post-scrape employer verification...")
        auto_verify_all_employers()

    thread = threading.Thread(target=run_scrape, daemon=True)
    thread.start()

    return jsonify({'message': 'Scraping started', 'sources': sources})

@app.route('/api/scrape/status')
def api_scrape_status():
    return jsonify(scrape_status)

@app.route('/api/scrape/history')
def api_scrape_history():
    runs = get_scrape_runs(20)
    return jsonify(runs)

@app.route('/api/sources')
def api_get_sources():
    return jsonify(SCRAPE_SOURCES)

@app.route('/api/career-pages')
def api_career_pages():
    pages = get_career_pages(active_only=False)
    return jsonify(pages)

@app.route('/api/audit-logs')
def api_audit_logs():
    logs = get_audit_logs(50)
    return jsonify(logs)

@app.route('/api/skills/summary')
def api_skill_summary():
    result = get_jobs(per_page=500)
    jobs = result['jobs']
    for j in jobs:
        if isinstance(j.get('skills'), str):
            try:
                j['skills'] = json.loads(j['skills'])
            except:
                j['skills'] = []
    return jsonify(get_skill_summary(jobs))


# ── Run ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🏛️  DEET Job Vacancy Discovery System")
    print("  📡  http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
