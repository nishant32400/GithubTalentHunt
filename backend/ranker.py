"""Simple ranking based on keyword overlap and heuristics."""
import utils


def rank_candidates(profiles, query, top_n=10):
    query_keywords = set(utils.extract_keywords(query))
    scored = []
    for p in profiles:
        skills = set([s.lower() for s in p.get('skills', [])])
        bio = (p.get('bio') or '').lower()
        repo_text = ' '.join([((r.get('description') or '') + ' ' + (r.get('name') or '')) for r in p.get('repos', [])]).lower()
        skill_matches = len([k for k in query_keywords if k in skills])
        bio_matches = sum(1 for k in query_keywords if k in bio)
        repo_matches = sum(1 for k in query_keywords if k in repo_text)
        followers = p.get('followers', 0) or 0
        score = skill_matches * 3 + repo_matches * 1.5 + bio_matches * 1 + followers * 0.01
        p2 = p.copy()
        p2['score'] = score
        scored.append(p2)
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:top_n]
