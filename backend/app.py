import argparse
import os

from flask import Flask, render_template, request
from dotenv import load_dotenv
from scrapers.github_scraper import GitHubScraper
from ranker import rank_candidates
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

TEMPLATES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, 'frontend')
)

app = Flask(__name__, template_folder=TEMPLATES_DIR)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').strip()
    location = request.form.get('location', '').strip()
    max_results = int(request.form.get('max_results', 10))
    search_size = int(request.form.get('search_size', 100))
    if not query:
        return render_template('index.html', error='Please enter job requirements or keywords.')
    gh_query = query
    if location:
        gh_query = f"{query} location:{location}"
    scraper = GitHubScraper(token=GITHUB_TOKEN)
    try:
        users = scraper.search_users(gh_query, max_results=search_size)
    except Exception as e:
        return render_template('index.html', error=str(e))

    profiles = []
    # parallelize profile building to reduce latency
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(scraper.build_profile, u, False, 20): u for u in users}
        for fut in as_completed(futures):
            u = futures[fut]
            try:
                profiles.append(fut.result())
            except Exception as e:
                print(f"Error building profile for {u}: {e}")
    ranked = rank_candidates(profiles, query, top_n=max_results)
    return render_template('results.html', candidates=ranked, query=query, location=location)


@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.get_json() or {}
    query = data.get('query', '')
    location = data.get('location', '')
    max_results = int(data.get('max_results', 10))
    search_size = int(data.get('search_size', 100))
    if not query:
        return {"error": "query required"}, 400
    gh_query = query
    if location:
        gh_query = f"{query} location:{location}"
    scraper = GitHubScraper(token=GITHUB_TOKEN)
    try:
        users = scraper.search_users(gh_query, max_results=search_size)
    except Exception as e:
        return {"error": str(e)}, 500

    profiles = []
    # parallelize profile building to reduce latency
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(scraper.build_profile, u, False, 20): u for u in users}
        for fut in as_completed(futures):
            u = futures[fut]
            try:
                profiles.append(fut.result())
            except Exception as e:
                print(f"Error building profile for {u}: {e}")
    ranked = rank_candidates(profiles, query, top_n=max_results)
    return {"results": ranked}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Flask web scraper app.')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to.')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', 3000)), help='Port to bind the server to.')
    parser.add_argument('--debug', action='store_true', help='Run the server in debug mode.')
    args = parser.parse_args()

    app.run(debug=args.debug or True, host=args.host, port=args.port)
