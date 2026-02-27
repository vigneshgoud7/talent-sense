"""
ML Classifier — TF-IDF + ML classification for job categorization and duplicate detection.
Uses scikit-learn for text vectorization and classification.
"""
import re
import hashlib
import json
from collections import defaultdict

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("[ML] scikit-learn not available. Using fallback methods.")


class JobClassifier:
    """TF-IDF based job classifier and deduplication engine."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        ) if ML_AVAILABLE else None
        self.job_vectors = None
        self.job_ids = []
        self.job_fingerprints = {}

    def _create_fingerprint(self, job):
        """Create a normalized fingerprint for a job listing."""
        title = re.sub(r'[^a-z0-9\s]', '', (job.get('title', '') or '').lower()).strip()
        company = re.sub(r'[^a-z0-9\s]', '', (job.get('company', '') or '').lower()).strip()
        location = re.sub(r'[^a-z0-9\s]', '', (job.get('location', '') or '').lower()).strip()

        text = f"{title}|{company}|{location}"
        return hashlib.md5(text.encode()).hexdigest()

    def _create_text_repr(self, job):
        """Create text representation for TF-IDF vectorization."""
        parts = [
            job.get('title', '') or '',
            job.get('company', '') or '',
            job.get('description', '') or '',
            job.get('location', '') or '',
        ]
        skills = job.get('skills', [])
        if isinstance(skills, str):
            try:
                skills = json.loads(skills)
            except:
                skills = [s.strip() for s in skills.split(',')]
        if isinstance(skills, list):
            parts.extend(skills)
        return ' '.join(parts)

    def detect_duplicates(self, jobs, similarity_threshold=0.85):
        """
        Detect duplicate jobs using both fingerprint matching and TF-IDF cosine similarity.
        Returns list of jobs with is_duplicate flag and duplicate_group markers.
        """
        if not jobs:
            return jobs

        # Phase 1: Exact fingerprint matching
        fingerprint_groups = defaultdict(list)
        for idx, job in enumerate(jobs):
            fp = self._create_fingerprint(job)
            fingerprint_groups[fp].append(idx)

        duplicate_flags = [False] * len(jobs)
        duplicate_of_map = {}

        for fp, indices in fingerprint_groups.items():
            if len(indices) > 1:
                primary = indices[0]
                for dup_idx in indices[1:]:
                    duplicate_flags[dup_idx] = True
                    duplicate_of_map[dup_idx] = primary

        # Phase 2: TF-IDF cosine similarity (if scikit-learn available)
        if ML_AVAILABLE and len(jobs) > 1:
            texts = [self._create_text_repr(job) for job in jobs]
            try:
                tfidf_matrix = self.vectorizer.fit_transform(texts)
                similarity_matrix = cosine_similarity(tfidf_matrix)

                for i in range(len(jobs)):
                    if duplicate_flags[i]:
                        continue
                    for j in range(i + 1, len(jobs)):
                        if duplicate_flags[j]:
                            continue
                        if similarity_matrix[i][j] >= similarity_threshold:
                            duplicate_flags[j] = True
                            duplicate_of_map[j] = i
            except Exception as e:
                print(f"[ML] TF-IDF similarity error: {e}")

        # Mark duplicates on jobs
        result = []
        for idx, job in enumerate(jobs):
            enriched = {**job}
            enriched['is_duplicate'] = duplicate_flags[idx]
            if idx in duplicate_of_map:
                enriched['duplicate_of_idx'] = duplicate_of_map[idx]
            result.append(enriched)

        dup_count = sum(1 for f in duplicate_flags if f)
        print(f"[ML] Duplicate detection: {dup_count} duplicates found in {len(jobs)} jobs")
        return result

    def compute_similarity_score(self, job1, job2):
        """Compute similarity between two jobs."""
        if not ML_AVAILABLE:
            fp1 = self._create_fingerprint(job1)
            fp2 = self._create_fingerprint(job2)
            return 1.0 if fp1 == fp2 else 0.0

        text1 = self._create_text_repr(job1)
        text2 = self._create_text_repr(job2)
        try:
            vectors = self.vectorizer.fit_transform([text1, text2])
            sim = cosine_similarity(vectors[0:1], vectors[1:2])
            return float(sim[0][0])
        except:
            return 0.0


class DuplicateTracker:
    """Tracks seen jobs to prevent re-insertion of duplicates."""

    def __init__(self):
        self.seen_fingerprints = set()
        self.seen_titles = set()

    def is_seen(self, job):
        """Check if this job has been seen before."""
        fp = self._fingerprint(job)
        if fp in self.seen_fingerprints:
            return True

        title_key = f"{(job.get('title', '') or '').lower().strip()}|{(job.get('company', '') or '').lower().strip()}"
        if title_key in self.seen_titles:
            return True

        return False

    def mark_seen(self, job):
        """Mark a job as seen."""
        fp = self._fingerprint(job)
        self.seen_fingerprints.add(fp)
        title_key = f"{(job.get('title', '') or '').lower().strip()}|{(job.get('company', '') or '').lower().strip()}"
        self.seen_titles.add(title_key)

    def _fingerprint(self, job):
        title = re.sub(r'[^a-z0-9]', '', (job.get('title', '') or '').lower())
        company = re.sub(r'[^a-z0-9]', '', (job.get('company', '') or '').lower())
        return hashlib.md5(f"{title}{company}".encode()).hexdigest()


# Global instances
classifier = JobClassifier()
duplicate_tracker = DuplicateTracker()
