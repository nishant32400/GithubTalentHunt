import re

STOPWORDS = set([
    'and', 'or', 'the', 'a', 'an', 'for', 'to', 'in', 'on', 'with', 'by', 'of',
    'is', 'are', 'as', 'be', 'has', 'have', 'that', 'this'
])

# normalized known skills (lowercase); include common variants
KNOWN_SKILLS = [
    'python', 'javascript', 'java', 'go', 'ruby', 'c++', 'c#', 'c', 'typescript', 'rust',
    'php', 'scala', 'kotlin', 'swift', 'sql', 'html', 'css', 'docker', 'aws', 'azure',
    'gcp', 'react', 'node', 'django', 'flask', 'rails', 'spring', 'tensorflow', 'pytorch',
    'nlp', 'ml', 'ai', 'ai/ml', 'data', 'spark', 'hadoop', 'postgres', 'mysql', 'mongo',
    'graphql', 'redis', 'dotnet', 'net', 'csharp'
]


def extract_keywords(text):
    if not text:
        return []
    tokens = re.findall(r"[A-Za-z\+#\.\-]+", text.lower())
    tokens = [t.strip('.#') for t in tokens]
    tokens = [t for t in tokens if t and t not in STOPWORDS and len(t) > 1]
    return tokens


def detect_known_skills(text):
    """Return a sorted, deduplicated list of known skills detected in `text`.

    Detection is case-insensitive and tolerant of common separators.
    """
    text = (text or '').lower()
    # normalize separators to spaces but keep language punctuation like c++, c#
    clean = re.sub(r'[^a-z0-9\+#\.\-]+', ' ', text)
    res = []
    for k in KNOWN_SKILLS:
        kl = k.lower()
        if kl in text or kl in clean:
            res.append(kl)
    return sorted(set(res))
