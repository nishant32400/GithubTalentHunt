import os
import time
import requests
from dotenv import load_dotenv
import utils

load_dotenv()


class GitHubScraper:
    BASE = "https://api.github.com"

    def __init__(self, token=None, per_page=30):
        token = token or os.getenv('GITHUB_TOKEN')
        self.token = token
        self.per_page = min(per_page, 100)
        self.session = requests.Session()
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'github-candidate-scraper/1.0'
        }
        if token:
            headers['Authorization'] = f'token {token}'
        self.session.headers.update(headers)

    def _get(self, url, params=None):
        resp = self.session.get(url, params=params, timeout=15)
        if resp.status_code == 401:
            raise Exception('GitHub API unauthorized: invalid or expired GITHUB_TOKEN. Update .env with a valid token.')
        if resp.status_code == 403:
            raise Exception('GitHub API rate limited or access denied: ' + resp.text)
        resp.raise_for_status()
        return resp.json()

    def search_users(self, query, max_results=100):
        users = []
        page = 1
        per_page = self.per_page or 30
        while len(users) < max_results:
            params = {'q': query, 'per_page': per_page, 'page': page}
            url = f"{self.BASE}/search/users"
            data = self._get(url, params=params)
            items = data.get('items', [])
            if not items:
                break
            for it in items:
                users.append(it.get('login'))
                if len(users) >= max_results:
                    break
            if len(items) < per_page:
                break
            page += 1
            time.sleep(0.1)
        return users

    def build_profile(self, username, fetch_readme=False, max_repos=20):
        user = self._get(f"{self.BASE}/users/{username}")
        repos = []
        page = 1
        per_page = 100
        collected = 0
        while True:
            params = {'per_page': per_page, 'page': page, 'sort': 'pushed'}
            repo_page = self._get(f"{self.BASE}/users/{username}/repos", params=params)
            if not repo_page:
                break
            for r in repo_page:
                repos.append({
                    'name': r.get('name'),
                    'description': r.get('description'),
                    'language': r.get('language'),
                    'html_url': r.get('html_url'),
                    'stargazers_count': r.get('stargazers_count', 0),
                    'forks_count': r.get('forks_count', 0),
                    'created_at': r.get('created_at'),
                    'updated_at': r.get('updated_at')
                })
                collected += 1
                if max_repos and collected >= max_repos:
                    break
            if max_repos and collected >= max_repos:
                break
            if len(repo_page) < per_page:
                break
            page += 1
            time.sleep(0.05)

        lang_counts = {}
        text_corpus = []
        for r in repos:
            lang = r.get('language')
            if lang:
                lang_counts[lang.lower()] = lang_counts.get(lang.lower(), 0) + 1
            text_corpus.append(' '.join(filter(None, [r.get('name') or '', r.get('description') or '', r.get('language') or ''])))
        bio = user.get('bio') or ''
        text_corpus.append(bio)

        skills_detected = utils.detect_known_skills(' '.join(text_corpus))
        top_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
        for lang, _ in top_langs[:5]:
            l = (lang or '').lower()
            if l and l not in skills_detected:
                skills_detected.append(l)

        profile = {
            'username': user.get('login'),
            'name': user.get('name'),
            'bio': user.get('bio'),
            'location': user.get('location'),
            'company': user.get('company'),
            'blog': user.get('blog'),
            'email': user.get('email'),
            'followers': user.get('followers'),
            'public_repos': user.get('public_repos'),
            'created_at': user.get('created_at'),
            'avatar_url': user.get('avatar_url'),
            'html_url': user.get('html_url'),
            'skills': skills_detected,
            'repos': repos
        }
        return profile
