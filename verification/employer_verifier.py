"""
Employer Verification Module — Validates employer legitimacy.
Checks domain existence, career page validity, and company information.
"""
import re
import hashlib
import requests
from datetime import datetime
from urllib.parse import urlparse

def verify_domain(domain):
    """Check if a domain exists and is reachable."""
    score = 0.0
    details = {}

    try:
        resp = requests.head(f"https://{domain}", timeout=10, allow_redirects=True)
        if resp.status_code < 400:
            score += 0.3
            details['domain_reachable'] = True
            details['status_code'] = resp.status_code
        else:
            details['domain_reachable'] = False
            details['status_code'] = resp.status_code
    except requests.exceptions.SSLError:
        # Try HTTP if HTTPS fails
        try:
            resp = requests.head(f"http://{domain}", timeout=10, allow_redirects=True)
            if resp.status_code < 400:
                score += 0.15  # Lower score without SSL
                details['domain_reachable'] = True
                details['ssl'] = False
        except:
            details['domain_reachable'] = False
    except:
        details['domain_reachable'] = False

    return score, details


def verify_career_page(career_url):
    """Check if the career page exists and contains job-related content."""
    score = 0.0
    details = {}

    try:
        resp = requests.get(career_url, timeout=15, allow_redirects=True,
                          headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            score += 0.2
            details['career_page_exists'] = True

            content = resp.text.lower()
            job_keywords = ['career', 'job', 'position', 'opening', 'vacancy',
                          'apply', 'opportunity', 'hiring', 'work with us']
            found_keywords = [kw for kw in job_keywords if kw in content]
            if found_keywords:
                score += 0.15
                details['job_keywords_found'] = found_keywords
        else:
            details['career_page_exists'] = False
    except:
        details['career_page_exists'] = False

    return score, details


def verify_company_name(name, domain):
    """Check if the company name matches the domain."""
    score = 0.0
    details = {}

    if not name or not domain:
        return score, details

    name_clean = re.sub(r'[^a-z0-9]', '', name.lower())
    domain_clean = re.sub(r'[^a-z0-9]', '', domain.split('.')[0].lower())

    if name_clean == domain_clean:
        score += 0.2
        details['name_domain_match'] = 'exact'
    elif name_clean in domain_clean or domain_clean in name_clean:
        score += 0.15
        details['name_domain_match'] = 'partial'
    else:
        details['name_domain_match'] = 'no_match'

    return score, details


def verify_job_count(job_count):
    """Score based on number of jobs posted."""
    score = 0.0
    if job_count > 0:
        score += 0.05
    if job_count >= 3:
        score += 0.05
    if job_count >= 10:
        score += 0.05
    return score


def run_full_verification(employer_data):
    """
    Run the complete verification pipeline for an employer.
    Returns overall score (0-1) and detailed breakdown.
    """
    total_score = 0.0
    breakdown = {}

    # Domain verification
    domain = employer_data.get('domain', '')
    if domain:
        d_score, d_details = verify_domain(domain)
        total_score += d_score
        breakdown['domain'] = {'score': d_score, 'details': d_details}

    # Career page verification
    career_url = employer_data.get('career_url', '')
    if career_url:
        c_score, c_details = verify_career_page(career_url)
        total_score += c_score
        breakdown['career_page'] = {'score': c_score, 'details': c_details}

    # Company name consistency
    name = employer_data.get('name', '')
    if name and domain:
        n_score, n_details = verify_company_name(name, domain)
        total_score += n_score
        breakdown['name_consistency'] = {'score': n_score, 'details': n_details}

    # Job count score
    job_count = employer_data.get('job_count', 0)
    j_score = verify_job_count(job_count)
    total_score += j_score
    breakdown['job_count'] = {'score': j_score, 'count': job_count}

    # Cap at 1.0
    total_score = min(total_score, 1.0)

    # Determine recommended status
    if total_score >= 0.7:
        recommended_status = 'verified'
    elif total_score >= 0.4:
        recommended_status = 'pending'
    else:
        recommended_status = 'flagged'

    return {
        'overall_score': round(total_score, 2),
        'recommended_status': recommended_status,
        'breakdown': breakdown,
        'verified_at': datetime.utcnow().isoformat()
    }


def quick_verify(domain):
    """Quick domain-only verification. Returns True/False."""
    try:
        resp = requests.head(f"https://{domain}", timeout=5, allow_redirects=True)
        return resp.status_code < 400
    except:
        return False
