"""
NLP Job Extractor — Extracts structured data from unstructured job descriptions.
Uses regex patterns, keyword matching, and text analysis for:
- Skill extraction
- Experience level detection
- Salary parsing
- Job type classification
- Location normalization
"""
import re
import json
from collections import Counter

# ── Skill Keywords Database ─────────────────────────────────────────────
SKILL_KEYWORDS = {
    'programming': [
        'python', 'javascript', 'typescript', 'java', 'c++', 'c#', 'go', 'golang',
        'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab',
        'perl', 'lua', 'haskell', 'elixir', 'dart', 'objective-c', 'cobol',
        'fortran', 'assembly', 'sql', 'plsql', 'bash', 'powershell', 'shell'
    ],
    'frontend': [
        'react', 'reactjs', 'angular', 'vue', 'vuejs', 'svelte', 'nextjs',
        'next.js', 'nuxt', 'gatsby', 'html', 'css', 'sass', 'less',
        'tailwind', 'bootstrap', 'material-ui', 'mui', 'webpack', 'vite',
        'jquery', 'redux', 'mobx', 'graphql', 'rest api', 'responsive design'
    ],
    'backend': [
        'node.js', 'nodejs', 'express', 'django', 'flask', 'fastapi',
        'spring', 'spring boot', 'rails', 'ruby on rails', 'laravel',
        'asp.net', '.net', 'microservices', 'api development', 'grpc',
        'rabbitmq', 'kafka', 'celery', 'redis', 'nginx', 'apache'
    ],
    'data': [
        'machine learning', 'deep learning', 'nlp', 'natural language processing',
        'computer vision', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
        'pandas', 'numpy', 'matplotlib', 'tableau', 'power bi', 'looker',
        'data analysis', 'data engineering', 'etl', 'data pipeline',
        'spark', 'hadoop', 'airflow', 'dbt', 'snowflake', 'databricks',
        'statistics', 'a/b testing', 'data visualization'
    ],
    'cloud': [
        'aws', 'azure', 'gcp', 'google cloud', 'cloud computing',
        'ec2', 's3', 'lambda', 'cloudformation', 'terraform',
        'docker', 'kubernetes', 'k8s', 'containerization',
        'ci/cd', 'jenkins', 'github actions', 'gitlab ci',
        'ansible', 'puppet', 'chef', 'helm', 'istio'
    ],
    'database': [
        'mysql', 'postgresql', 'postgres', 'mongodb', 'cassandra',
        'dynamodb', 'firebase', 'elasticsearch', 'sqlite', 'oracle db',
        'sql server', 'mariadb', 'couchdb', 'neo4j', 'influxdb',
        'database design', 'data modeling', 'orm'
    ],
    'mobile': [
        'ios', 'android', 'react native', 'flutter', 'xamarin',
        'swiftui', 'jetpack compose', 'mobile development',
        'app development', 'cordova', 'ionic'
    ],
    'tools': [
        'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence',
        'slack', 'figma', 'sketch', 'adobe xd', 'invision',
        'postman', 'swagger', 'linux', 'unix', 'agile', 'scrum',
        'kanban', 'devops', 'sre', 'monitoring', 'logging'
    ],
    'security': [
        'cybersecurity', 'information security', 'penetration testing',
        'vulnerability assessment', 'soc', 'siem', 'encryption',
        'oauth', 'jwt', 'ssl', 'tls', 'firewall', 'ids', 'ips',
        'compliance', 'gdpr', 'hipaa', 'pci-dss'
    ],
    'soft_skills': [
        'communication', 'leadership', 'teamwork', 'problem solving',
        'critical thinking', 'project management', 'time management',
        'presentation', 'mentoring', 'cross-functional', 'stakeholder management'
    ]
}

# Flatten for quick lookup
ALL_SKILLS = {}
for category, skills in SKILL_KEYWORDS.items():
    for skill in skills:
        ALL_SKILLS[skill.lower()] = category

# ── Experience Level Patterns ─────────────────────────────────────────────
EXPERIENCE_PATTERNS = {
    'Entry-level': [
        r'\b(?:entry[- ]?level|junior|jr\.?|intern|internship|graduate|fresh(?:er)?|0-[12]\s*(?:years?|yrs?))\b',
        r'\b(?:new\s*grad|recent\s*graduate|no\s*experience\s*required)\b'
    ],
    'Mid-level': [
        r'\b(?:mid[- ]?level|intermediate|2-[45]\s*(?:years?|yrs?)|3-[56]\s*(?:years?|yrs?))\b',
        r'\b(?:[2-5]\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience)\b'
    ],
    'Senior': [
        r'\b(?:senior|sr\.?|lead|principal|staff|5-\d+\s*(?:years?|yrs?))\b',
        r'\b(?:[5-9]\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience)\b',
        r'\b(?:1[0-9]\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience)\b'
    ],
    'Executive': [
        r'\b(?:director|vp|vice\s*president|c-level|cto|ceo|cfo|coo|head\s*of)\b',
        r'\b(?:executive|chief|managing\s*director)\b'
    ]
}

# ── Salary Patterns ─────────────────────────────────────────────────────
SALARY_PATTERNS = [
    r'\$[\d,]+(?:\s*[-–]\s*\$[\d,]+)?(?:\s*(?:per|/)\s*(?:year|yr|annum|month|hr|hour))?',
    r'(?:USD|EUR|GBP)\s*[\d,]+(?:\s*[-–]\s*[\d,]+)?',
    r'[\d,]+\s*[-–]\s*[\d,]+\s*(?:USD|EUR|GBP|per\s*(?:year|month))',
    r'(?:salary|compensation|pay)[\s:]*\$?[\d,]+(?:\s*[-–]\s*\$?[\d,]+)?',
]

# ── Job Type Patterns ────────────────────────────────────────────────────
JOB_TYPE_MAP = {
    'Full-time': [r'\bfull[- ]?time\b', r'\bpermanent\b', r'\bfte\b'],
    'Part-time': [r'\bpart[- ]?time\b'],
    'Contract': [r'\bcontract\b', r'\bfreelance\b', r'\bconsultant\b', r'\b1099\b'],
    'Remote': [r'\bremote\b', r'\bwork from home\b', r'\bwfh\b', r'\btelecommute\b'],
    'Internship': [r'\bintern(?:ship)?\b', r'\bco-?op\b'],
    'Temporary': [r'\btemporary\b', r'\btemp\b', r'\bseasonal\b'],
}

# ── Category Classification Rules ────────────────────────────────────────
CATEGORY_RULES = {
    'Software Engineering': [
        r'\b(?:software|backend|frontend|full[- ]?stack|web)\s*(?:engineer|developer|dev)\b',
        r'\b(?:swe|sde|programmer|coder)\b',
        r'\b(?:react|angular|vue|node|java|python|c\+\+|golang)\s*(?:engineer|developer|dev)\b'
    ],
    'Data Science': [
        r'\b(?:data\s*scientist|machine\s*learning|ml\s*engineer|ai\s*engineer)\b',
        r'\b(?:deep\s*learning|nlp|computer\s*vision|data\s*analyst)\b',
        r'\b(?:research\s*scientist|applied\s*scientist)\b'
    ],
    'DevOps': [
        r'\b(?:devops|sre|site\s*reliability|infrastructure|platform)\s*engineer\b',
        r'\b(?:cloud\s*engineer|systems?\s*engineer|release\s*engineer)\b'
    ],
    'Product Management': [
        r'\b(?:product\s*manager|pm|product\s*owner|product\s*lead)\b',
        r'\b(?:technical\s*program\s*manager|tpm)\b'
    ],
    'Design': [
        r'\b(?:ux|ui|user\s*experience|user\s*interface|product)\s*designer\b',
        r'\b(?:graphic\s*designer|visual\s*designer|interaction\s*designer)\b'
    ],
    'Marketing': [
        r'\b(?:marketing|growth|seo|sem|content)\s*(?:manager|specialist|analyst|lead)\b',
        r'\b(?:digital\s*marketing|brand\s*manager|social\s*media)\b'
    ],
    'Sales': [
        r'\b(?:sales|account|business\s*development)\s*(?:manager|representative|executive|lead)\b',
        r'\b(?:bdr|sdr|ae|enterprise\s*sales)\b'
    ],
    'Human Resources': [
        r'\b(?:hr|human\s*resources|recruiter|talent\s*acquisition)\b',
        r'\b(?:people\s*operations|people\s*partner|hrbp)\b'
    ],
    'Finance': [
        r'\b(?:finance|financial|accountant|accounting|controller|treasury)\b',
        r'\b(?:fp&a|financial\s*analyst|cpa|auditor)\b'
    ],
    'Quality Assurance': [
        r'\b(?:qa|quality\s*assurance|test|tester|sdet)\b',
        r'\b(?:automation\s*engineer|test\s*engineer)\b'
    ],
    'Customer Support': [
        r'\b(?:customer\s*(?:support|success|service)|technical\s*support)\b',
        r'\b(?:help\s*desk|support\s*engineer|solutions?\s*engineer)\b'
    ],
    'Project Management': [
        r'\b(?:project\s*manager|program\s*manager|scrum\s*master)\b',
        r'\b(?:delivery\s*manager|pmo)\b'
    ],
    'Business Analysis': [
        r'\b(?:business\s*analyst|ba|systems?\s*analyst|requirements\s*analyst)\b'
    ],
    'Operations': [
        r'\b(?:operations?\s*manager|operations?\s*analyst|logistics)\b',
        r'\b(?:supply\s*chain|procurement|warehouse)\b'
    ]
}


def extract_skills(text):
    """Extract technical and soft skills from text using keyword matching."""
    if not text:
        return []
    text_lower = text.lower()
    found_skills = set()

    for skill in ALL_SKILLS:
        # Use word boundary matching for short skills
        if len(skill) <= 3:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        elif skill in text_lower:
            found_skills.add(skill)

    return sorted(list(found_skills))


def detect_experience_level(text):
    """Detect experience level from job description text."""
    if not text:
        return 'Mid-level'
    text_lower = text.lower()

    for level, patterns in EXPERIENCE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return level

    return 'Mid-level'  # Default


def extract_salary(text):
    """Extract salary information from text."""
    if not text:
        return None
    for pattern in SALARY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def detect_job_type(text):
    """Detect job type (full-time, part-time, contract, etc.)."""
    if not text:
        return 'Full-time'
    text_lower = text.lower()

    for job_type, patterns in JOB_TYPE_MAP.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return job_type

    return 'Full-time'  # Default


def classify_category(title, description=''):
    """Classify job into a category based on title and description."""
    combined = f"{title} {description}".lower()

    for category, patterns in CATEGORY_RULES.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return category

    return 'Other'


def normalize_location(location):
    """Normalize location strings."""
    if not location:
        return 'Not Specified'

    location = location.strip()

    # Common normalizations
    remote_patterns = [r'\bremote\b', r'\banywhere\b', r'\bwork from home\b', r'\bwfh\b']
    for pattern in remote_patterns:
        if re.search(pattern, location, re.IGNORECASE):
            # Check if it's "Remote - Location" or just "Remote"
            location_clean = re.sub(pattern, '', location, flags=re.IGNORECASE).strip(' -,/')
            if location_clean:
                return f"Remote ({location_clean})"
            return 'Remote'

    return location


def process_job(job_data):
    """
    Full NLP processing pipeline for a single job.
    Takes raw scraped data and enriches it with extracted features.
    """
    title = job_data.get('title', '')
    description = job_data.get('description', '')
    combined_text = f"{title} {description}"

    # Extract existing skills and merge with NLP-detected ones
    existing_skills = job_data.get('skills', [])
    nlp_skills = extract_skills(combined_text)
    all_skills = sorted(list(set(
        [s.lower() for s in existing_skills] + nlp_skills
    )))

    # Enrich the job data
    processed = {**job_data}
    processed['skills'] = all_skills
    processed['experience_level'] = detect_experience_level(combined_text)
    processed['job_type'] = detect_job_type(combined_text) or job_data.get('job_type', 'Full-time')
    processed['category'] = classify_category(title, description)
    processed['location'] = normalize_location(job_data.get('location', ''))
    processed['salary_range'] = extract_salary(combined_text) or job_data.get('salary_range')
    processed['confidence_score'] = calculate_confidence(processed)

    return processed


def calculate_confidence(job_data):
    """Calculate a data quality/confidence score (0-1) for a processed job."""
    score = 0.0
    weights = {
        'title': 0.2,
        'company': 0.15,
        'description': 0.2,
        'location': 0.1,
        'skills': 0.15,
        'salary_range': 0.1,
        'apply_url': 0.1
    }

    if job_data.get('title') and len(job_data['title']) > 5:
        score += weights['title']
    if job_data.get('company') and job_data['company'] != 'Unknown':
        score += weights['company']
    if job_data.get('description') and len(job_data['description']) > 50:
        score += weights['description']
    if job_data.get('location') and job_data['location'] not in ('Not Specified', ''):
        score += weights['location']
    if job_data.get('skills') and len(job_data['skills']) > 0:
        score += weights['skills']
    if job_data.get('salary_range'):
        score += weights['salary_range']
    if job_data.get('apply_url') and job_data['apply_url'].startswith('http'):
        score += weights['apply_url']

    return round(score, 2)


def batch_process_jobs(jobs_list):
    """Process a batch of jobs through the NLP pipeline."""
    processed = []
    for job in jobs_list:
        try:
            processed.append(process_job(job))
        except Exception as e:
            print(f"[NLP] Error processing job '{job.get('title', 'unknown')}': {e}")
            processed.append(job)  # Return unprocessed if error
    return processed


def get_skill_summary(jobs_list):
    """Generate a summary of skills across all jobs."""
    skill_counter = Counter()
    for job in jobs_list:
        skills = job.get('skills', [])
        if isinstance(skills, str):
            try:
                skills = json.loads(skills)
            except:
                skills = [s.strip() for s in skills.split(',')]
        for skill in skills:
            skill_counter[skill.lower()] += 1
    return dict(skill_counter.most_common(30))
