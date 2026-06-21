"""CLI for searching GitHub profiles and ranking candidates for a job query."""
import argparse
import os
import json
from dotenv import load_dotenv
from scrapers.github_scraper import GitHubScraper
from ranker import rank_candidates
from concurrent.futures import ThreadPoolExecutor, as_completed


def parse_args():
    parser = argparse.ArgumentParser(description='Find top candidates on GitHub for a job query.')
    parser.add_argument('--query', '-q', required=True, help='Job requirement keywords, e.g. "python backend django"')
    parser.add_argument('--max-results', '-n', type=int, default=10, help='Number of top candidates to return')
    parser.add_argument('--search-size', '-s', type=int, default=100, help='How many users to fetch from GitHub search to consider')
    parser.add_argument('--out', '-o', default='results.json', help='Output JSON file')
    return parser.parse_args()


def main():
    args = parse_args()
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    scraper = GitHubScraper(token=token)
    print(f"Searching GitHub for: {args.query} (scanning up to {args.search_size} users)")
    users = scraper.search_users(args.query, max_results=args.search_size)
    print(f"Fetched {len(users)} candidate usernames; building profiles...")
    profiles = []
    # fetch profiles in parallel to reduce runtime
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(scraper.build_profile, u, False, 20): u for u in users}
        for i, fut in enumerate(as_completed(futures), start=1):
            u = futures[fut]
            try:
                p = fut.result()
                profiles.append(p)
                print(f"[{i}/{len(users)}] {u} -> {p.get('name') or ''} ({len(p.get('skills', []))} skills)")
            except Exception as e:
                print(f"Error fetching {u}: {e}")
    ranked = rank_candidates(profiles, args.query, top_n=args.max_results)
    print(f"Top {len(ranked)} candidates:")
    for r in ranked:
        print(f"- {r['username']} ({r.get('name')}) score={r['score']:.2f} skills={', '.join(r.get('skills', [])[:5])}")
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(ranked, f, indent=2)
    print(f"Results saved to {args.out}")


if __name__ == '__main__':
    main()
