# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import requests
# from collections import defaultdict
# from datetime import datetime, timedelta
# from dotenv import load_dotenv
# import os

# load_dotenv()  # take environment variables from .env.
# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# app = Flask(__name__)
# CORS(app)  # Enable CORS for frontend access
# GITHUB_API = "https://api.github.com"

# @app.route('/api/validate_repo', methods=['POST'])
# def validate_repo():
#     # Get the URL from the request body
#     url = request.json.get('url')
#     if not url:
#         return jsonify({"valid": False, "error": "No URL provided"}), 400
    
#     try:
#         # Extract owner and repo from the URL (e.g., https://github.com/owner/repo)
#         parts = url.split('/')
#         owner, repo = parts[-2], parts[-1]
        
#         # Make a request to GitHub API to check repository
#         response = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=HEADERS)
        
#         if response.status_code == 200:
#             return jsonify({"valid": True})
#         elif response.status_code == 404:
#             return jsonify({"valid": False, "error": "Repository not found or private"})
#         else:
#             return jsonify({"valid": False, "error": f"Unexpected status code: {response.status_code}"}), 500
#     except Exception as e:
#         return jsonify({"valid": False, "error": str(e)}), 500

# @app.route('/api/repo', methods=['POST'])
# def get_repo_data():
#     url = request.json.get('url')
#     if not url:
#         return jsonify({"error": "No URL provided"}), 400
#     parts = url.split('/')
#     owner, repo = parts[-2], parts[-1]
#     response = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}")
#     if response.status_code != 200:
#         return jsonify({"error": "Invalid repo or API limit reached"}), 400
#     data = response.json()
#     repo_info = {
#         "name": data["name"],
#         "stars": data["stargazers_count"],
#         "forks": data["forks_count"],
#         "watchers": data["watchers_count"]
#     }
#     return jsonify(repo_info)

# @app.route('/api/commits', methods=['POST'])
# def get_commits():
#     url = request.json.get('url')
#     frequency = request.json.get('frequency', 'day')  # Default to 'day'
#     if not url:
#         return jsonify({"error": "No URL provided"}), 400
#     parts = url.split('/')
#     owner, repo = parts[-2], parts[-1]
    
#     # Fetch commits from GitHub API
#     response = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits")
#     if response.status_code != 200:
#         return jsonify({"error": "Failed to fetch commits"}), 400
#     commits = response.json()
    
#     # Determine grouping format based on frequency
#     if frequency == 'day':
#         group_format = '%Y-%m-%d'
#     elif frequency == 'week':
#         group_format = '%Y-%W'
#     elif frequency == 'month':
#         group_format = '%Y-%m'
#     else:
#         return jsonify({"error": "Invalid frequency"}), 400
    
#     # Group commits by the specified frequency
#     commit_counts = defaultdict(int)
#     for commit in commits:
#         date_str = commit['commit']['author']['date']
#         date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
#         key = date.strftime(group_format)
#         commit_counts[key] += 1
    
#     return jsonify({"commit_frequency": dict(commit_counts)})
    
# @app.route('/api/contributors', methods=['POST'])
# def get_contributors():
#     url = request.json.get('url')
#     parts = url.split('/')
#     owner, repo = parts[-2], parts[-1]
#     response = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/contributors")
#     if response.status_code != 200:
#         return jsonify({"error": "Failed to fetch contributors"}), 400
#     data = response.json()
#     contributors = [{"login": c["login"], "commits": c["contributions"]} for c in data]
#     return jsonify(contributors)

# @app.route('/api/languages', methods=['POST'])
# def get_languages():
#     url = request.json.get('url')
#     if not url:
#         return jsonify({"error": "No URL provided"}), 400
#     parts = url.split('/')
#     owner, repo = parts[-2], parts[-1]
#     response = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/languages")
#     if response.status_code != 200:
#         return jsonify({"error": "Failed to fetch languages"}), 400
#     languages = response.json()  # e.g., {"Python": 5000, "JavaScript": 2000}
#     total_bytes = sum(languages.values())
#     language_percentages = {
#         lang: round((count / total_bytes) * 100, 2) if total_bytes > 0 else 0
#         for lang, count in languages.items()
#     }
#     return jsonify({
#         "bytes": languages,
#         "percentages": language_percentages
#     })

# @app.route('/api/code_frequency', methods=['POST'])
# def get_code_frequency():
#     url = request.json.get('url')
#     if not url:
#         return jsonify({"error": "No URL provided"}), 400
#     parts = url.split('/')
#     owner, repo = parts[-2], parts[-1]
#     response = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/stats/code_frequency")
#     if response.status_code == 202:
#         return jsonify({"message": "GitHub is generating statistics. Please try again after a few seconds."}), 202
#     if response.status_code != 200:
#         return jsonify({"error": "Failed to fetch code frequency"}), 400
#     code_frequency = response.json()
#     if not code_frequency:
#         return jsonify({"message": "No code frequency data available yet. Please try again later."}), 204

#     # Convert Unix timestamps to human-readable dates
#     readable_code_frequency = []
#     for week_data in code_frequency:
#         week_start = datetime.utcfromtimestamp(week_data[0]).strftime('%Y-%m-%d')
#         additions = week_data[1]
#         deletions = week_data[2]
#         readable_code_frequency.append({
#             "Date": week_start,
#             "Code Additions": additions,
#             "Code Deletions": deletions
#         })

#     return jsonify(readable_code_frequency)

# def parse_github_url(url):
#     # Remove trailing slash and .git if present
#     url = url.rstrip('/')
#     if url.endswith('.git'):
#         url = url[:-4]
#     parts = url.split('/')
#     if len(parts) < 2:
#         return None, None
#     owner, repo = parts[-2], parts[-1]
#     return owner, repo

#     prs = []
#     page = 1
#     while True:
#         url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls?state={state}&per_page=100&page={page}"
#         response = requests.get(url, headers=HEADERS)
#         print(f"Fetching {url} - Status: {response.status_code}")  # Debug
#         if response.status_code != 200:
#             print(f"Error: {response.status_code}, {response.text}")
#             return None
#         page_data = response.json()
#         print(f"Page {page} returned {len(page_data)} PRs")  # Debug
#         if not page_data:
#             break
#         prs.extend(page_data)
#         if len(page_data) < 100:
#             break
#         page += 1
#     return prs
# def fetch_all_prs(owner, repo, state):
#     prs = []
#     page = 1
#     while True:
#         url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
#         params = {"state": state, "per_page": 100, "page": page}
#         response = requests.get(url, headers=HEADERS, params=params)
#         print(f"Fetching {url} page {page} - Status: {response.status_code}")
#         if response.status_code != 200:
#             print("Error:", response.status_code, response.text)
#             return None
#         page_data = response.json()
#         if not isinstance(page_data, list):
#             print("Unexpected API response:", page_data)
#             return None
#         if not page_data:
#             break
#         prs.extend(page_data)
#         if len(page_data) < 100:
#             break
#         page += 1
#     return prs

# @app.route('/api/pull_requests', methods=['POST'])
# def get_pull_requests():
#     url = request.json.get('url')
#     if not url:
#         return jsonify({"error": "No URL provided"}), 400
#     owner, repo = parse_github_url(url)
#     if not owner or not repo:
#         return jsonify({"error": "Invalid GitHub URL"}), 400

#     open_prs = fetch_all_prs(owner, repo, "open")
#     closed_prs = fetch_all_prs(owner, repo, "closed")
#     if open_prs is None or closed_prs is None:
#         return jsonify({"error": "Failed to fetch pull requests"}), 400

#     merged_count = sum(1 for pr in closed_prs if pr.get("merged_at"))
#     closed_unmerged_count = len(closed_prs) - merged_count

#     print(f"Open: {len(open_prs)}, Closed (not merged): {closed_unmerged_count}, Merged: {merged_count}")

#     return jsonify({
#         "open": len(open_prs),
#         "closed_unmerged": closed_unmerged_count,
#         "merged": merged_count
#     })

# @app.route('/api/contribution_heatmap', methods=['POST'])
# def get_contribution_heatmap():
#     url = request.json.get('url')
#     if not url:
#         return jsonify({"error": "No URL provided"}), 400
#     parts = url.split('/')
#     owner, repo = parts[-2], parts[-1]
#     # Step 1: Find the first and last commit dates
#     commits_url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
#     params = {"per_page": 100, "page": 1}
#     all_commits = []
#     while True:
#         response = requests.get(commits_url, headers=HEADERS, params=params)
#         if response.status_code != 200:
#             break
#         page_commits = response.json()
#         if not page_commits:
#             break
#         all_commits.extend(page_commits)
#         if len(page_commits) < 100:
#             break
#         params["page"] += 1
 
#     # Step 2: Group commits by day
#     daily_counts = defaultdict(int)
#     for commit in all_commits:
#         date_str = commit["commit"]["author"]["date"]
#         date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
#         day_str = date_obj.strftime("%Y-%m-%d")
#         daily_counts[day_str] += 1
 
#     # Step 3: Fill in days with zero commits
#     if daily_counts:
#         min_day = min(daily_counts)
#         max_day = max(daily_counts)
#         current_day = datetime.fromisoformat(min_day)
#         last_day = datetime.fromisoformat(max_day)
#         result = []
#         while current_day <= last_day:
#             day_str = current_day.strftime("%Y-%m-%d")
#             result.append({
#              "date": day_str,
#              "commits": daily_counts.get(day_str, 0)
#             })
#             current_day += timedelta(days=1)
#     else:
#         result = []
 
#     return jsonify(result)

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)






from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import requests

# Load environment variables
dotenv_path = os.getenv("DOTENV_PATH", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
GITHUB_API = "https://api.github.com"

# FastAPI app initialization
app = FastAPI()

# Enable CORS for all origins (configure origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request bodies
class RepoRequest(BaseModel):
    url: HttpUrl

class CommitsRequest(RepoRequest):
    frequency: Optional[str] = 'day'

# Utility to parse GitHub URL
def parse_github_url(url: str) -> Tuple[str, str]:
    clean = url.rstrip('/')
    if clean.endswith('.git'):
        clean = clean[:-4]
    parts = clean.split('/')
    if len(parts) < 2:
        raise ValueError("Invalid GitHub URL")
    return parts[-2], parts[-1]

# Endpoint: Validate repository existence and visibility
@app.post("/api/validate_repo")
async def validate_repo(request: RepoRequest):
    owner, repo = parse_github_url(str(request.url))
    resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=HEADERS)
    if resp.status_code == 200:
        return {"valid": True}
    if resp.status_code == 404:
        return {"valid": False, "error": "Repository not found or private"}
    raise HTTPException(status_code=500, detail=f"Unexpected status code: {resp.status_code}")

# Endpoint: Basic repository info
@app.post("/api/repo")
async def get_repo_data(request: RepoRequest):
    owner, repo = parse_github_url(str(request.url))
    resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=HEADERS)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid repo or API limit reached")
    data = resp.json()
    return {
        "name": data.get("name"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "watchers": data.get("watchers_count"),
    }

# Endpoint: Commit frequency grouping
@app.post("/api/commits")
async def get_commits(request: CommitsRequest):
    owner, repo = parse_github_url(str(request.url))
    resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits", headers=HEADERS)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch commits")
    commits = resp.json()

    fmt = {
        'day': '%Y-%m-%d',
        'week': '%Y-%W',
        'month': '%Y-%m'
    }.get(request.frequency)
    if fmt is None:
        raise HTTPException(status_code=400, detail="Invalid frequency")

    counts = defaultdict(int)
    for c in commits:
        dt = datetime.strptime(c['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ')
        counts[dt.strftime(fmt)] += 1
    return {"commit_frequency": counts}

# Endpoint: Contributors list
@app.post("/api/contributors")
async def get_contributors(request: RepoRequest):
    owner, repo = parse_github_url(str(request.url))
    resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/contributors", headers=HEADERS)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch contributors")
    return [
        {"login": c["login"], "commits": c.get("contributions")} for c in resp.json()
    ]

# Endpoint: Languages breakdown
@app.post("/api/languages")
async def get_languages(request: RepoRequest):
    owner, repo = parse_github_url(str(request.url))
    resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/languages", headers=HEADERS)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch languages")
    data = resp.json()
    total = sum(data.values()) or 1
    percentages = {lang: round(count/total*100, 2) for lang, count in data.items()}
    return {"bytes": data, "percentages": percentages}

# Endpoint: Code frequency stats
@app.post("/api/code_frequency")
async def get_code_frequency(request: RepoRequest):
    owner, repo = parse_github_url(str(request.url))
    resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/stats/code_frequency", headers=HEADERS)
    if resp.status_code == 202:
        raise HTTPException(status_code=202, detail="Generating statistics. Try again shortly.")
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch code frequency")
    stats = resp.json()
    if not stats:
        return []
    result = []
    for week in stats:
        dt = datetime.utcfromtimestamp(week[0]).strftime('%Y-%m-%d')
        result.append({"Date": dt, "Code Additions": week[1], "Code Deletions": week[2]})
    return result

# Utility: Fetch all PRs with pagination

def fetch_all_prs(owner: str, repo: str, state: str) -> List[Dict[str, Any]]:
    all_prs, page = [], 1
    while True:
        resp = requests.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/pulls",
            headers=HEADERS,
            params={"state": state, "per_page": 100, "page": page}
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        if not isinstance(data, list) or not data:
            break
        all_prs.extend(data)
        if len(data) < 100:
            break
        page += 1
    return all_prs

# Endpoint: Pull request counts
@app.post("/api/pull_requests")
async def get_pull_requests(request: RepoRequest):
    owner, repo = parse_github_url(str(request.url))
    open_prs = fetch_all_prs(owner, repo, "open")
    closed_prs = fetch_all_prs(owner, repo, "closed")
    merged = sum(1 for pr in closed_prs if pr.get("merged_at"))
    closed_unmerged = len(closed_prs) - merged
    return {"open": len(open_prs), "closed_unmerged": closed_unmerged, "merged": merged}

# Endpoint: Contribution heatmap data
@app.post("/api/contribution_heatmap")
async def get_contribution_heatmap(request: RepoRequest):
    owner, repo = parse_github_url(str(request.url))
    # paginated commit fetch
    commits_url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
    params = {"per_page": 100, "page": 1}
    all_commits = []
    while True:
        resp = requests.get(commits_url, headers=HEADERS, params=params)
        if resp.status_code != 200:
            break
        data = resp.json()
        if not data:
            break
        all_commits.extend(data)
        if len(data) < 100:
            break
        params["page"] += 1

    counts = defaultdict(int)
    for c in all_commits:
        dt = datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
        counts[dt.strftime("%Y-%m-%d")] += 1

    result = []
    if counts:
        start = min(counts)
        end = max(counts)
        curr = datetime.fromisoformat(start)
        last = datetime.fromisoformat(end)
        while curr <= last:
            day = curr.strftime("%Y-%m-%d")
            result.append({"date": day, "commits": counts.get(day, 0)})
            curr += timedelta(days=1)
    return result

# Entry point for uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
