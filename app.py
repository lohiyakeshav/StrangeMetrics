from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import httpx
from time import time

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

# Middleware: Log request durations
@app.middleware("http")
async def log_request_duration(request, call_next):
    start = time()
    response = await call_next(request)
    duration = time() - start
    print(f"{request.method} {request.url.path} took {duration:.2f}s")
    return response

# Health check endpoint
@app.get("/ping")
async def ping():
    return {"message": "pong"}

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

# Add rate limit checking function
async def check_rate_limit():
    """Check current GitHub API rate limit status"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{GITHUB_API}/rate_limit", headers=HEADERS)
        if resp.status_code == 200:
            data = resp.json()
            core_rate = data.get("resources", {}).get("core", {})
            remaining = core_rate.get("remaining", 0)
            reset_time = datetime.fromtimestamp(core_rate.get("reset", 0))
            now = datetime.now()
            minutes_to_reset = max(0, int((reset_time - now).total_seconds() / 60))
            return {
                "remaining": remaining,
                "limit": core_rate.get("limit", 60),
                "reset_time": reset_time.strftime("%Y-%m-%d %H:%M:%S"),
                "minutes_to_reset": minutes_to_reset
            }
        return {"error": "Could not fetch rate limit information"}

# Endpoint: Validate repository existence and visibility
@app.post("/api/validate_repo")
async def validate_repo(request: RepoRequest):
    try:
        owner, repo = parse_github_url(str(request.url))
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=HEADERS)
            
            if resp.status_code == 403 and "rate limit exceeded" in resp.text.lower():
                # Get rate limit info to include in the error
                rate_info = await check_rate_limit()
                error_msg = f"GitHub API rate limit exceeded. "
                if "minutes_to_reset" in rate_info:
                    error_msg += f"Limits will reset in {rate_info['minutes_to_reset']} minutes."
                return {"valid": False, "error": error_msg, "rate_limit_info": rate_info}
                
            if resp.status_code == 200:
                return {"valid": True}
            if resp.status_code == 404:
                return {"valid": False, "error": "Repository not found or private"}
                
            return {"valid": False, "error": f"Unexpected status code: {resp.status_code}"}
    except Exception as e:
        print(f"Exception in validate_repo: {str(e)}")
        return {"valid": False, "error": f"An unexpected error occurred: {str(e)}"}

# Endpoint: Basic repository info
@app.post("/api/repo")
async def get_repo_data(request: RepoRequest):
    try:
        owner, repo = parse_github_url(str(request.url))
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=HEADERS)
            
            if resp.status_code == 403 and "rate limit exceeded" in resp.text.lower():
                # Get rate limit info to include in the error
                rate_info = await check_rate_limit()
                error_msg = f"GitHub API rate limit exceeded. "
                if "minutes_to_reset" in rate_info:
                    error_msg += f"Limits will reset in {rate_info['minutes_to_reset']} minutes."
                return {"error": error_msg, "rate_limit_info": rate_info}
                
            if resp.status_code != 200:
                return {"error": "Invalid repo or API limit reached", "status_code": resp.status_code}
                
            data = resp.json()
            return {
                "name": data.get("name"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "watchers": data.get("watchers_count"),
            }
    except Exception as e:
        print(f"Exception in get_repo_data: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

# Endpoint: Commit frequency grouping
@app.post("/api/commits")
async def get_commits(request: CommitsRequest):
    owner, repo = parse_github_url(str(request.url))
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits", headers=HEADERS)
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
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/contributors", headers=HEADERS)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch contributors")
    return [
        {"login": c["login"], "commits": c.get("contributions")} for c in resp.json()
    ]

# Endpoint: Languages breakdown
@app.post("/api/languages")
async def get_languages(request: RepoRequest):
    owner, repo = parse_github_url(str(request.url))
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/languages", headers=HEADERS)
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
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/stats/code_frequency", headers=HEADERS)
            
            # Special handling for 202 (processing)
            if resp.status_code == 202:
                return {"message": "GitHub is generating the statistics. Please try again in a moment."}
            
            # Handle other errors gracefully
            if resp.status_code != 200:
                print(f"Error from GitHub API: {resp.status_code} - {resp.text}")
                return []
            
            stats = resp.json()
            if not stats:
                return []
                
            result = []
            for week in stats:
                dt = datetime.utcfromtimestamp(week[0]).strftime('%Y-%m-%d')
                result.append({"Date": dt, "Code Additions": week[1], "Code Deletions": week[2]})
            return result
            
    except Exception as e:
        print(f"Exception in code_frequency: {str(e)}")
        return []  # Return empty list instead of raising exception

# Utility: Fetch all PRs with pagination
async def fetch_all_prs(owner: str, repo: str, state: str) -> List[Dict[str, Any]]:
    all_prs, page = [], 1
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            resp = await client.get(
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
    try:
        owner, repo = parse_github_url(str(request.url))
        open_prs = await fetch_all_prs(owner, repo, "open")
        closed_prs = await fetch_all_prs(owner, repo, "closed")
        merged = sum(1 for pr in closed_prs if pr.get("merged_at"))
        closed_unmerged = len(closed_prs) - merged
        return {"open": len(open_prs), "closed_unmerged": closed_unmerged, "merged": merged}
    except Exception as e:
        print(f"Exception in pull_requests: {str(e)}")
        return {"open": 0, "closed_unmerged": 0, "merged": 0}

# Endpoint: Contribution heatmap data
@app.post("/api/contribution_heatmap")
async def get_contribution_heatmap(request: RepoRequest):
    owner, repo = parse_github_url(str(request.url))
    commits_url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
    params = {"per_page": 100, "page": 1}
    counts = defaultdict(int)
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            resp = await client.get(commits_url, headers=HEADERS, params=params)
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            for c in data:
                dt = datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
                counts[dt.strftime("%Y-%m-%d")] += 1
            if len(data) < 100:
                break
            params["page"] += 1

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

# Add a new rate limit info endpoint
@app.get("/api/rate_limit")
async def get_rate_limit():
    """Get the current GitHub API rate limit status"""
    return await check_rate_limit()

# ————————————————
# Root route for Render health checks
@app.get("/")
async def root():
    return {"message": "Service is up!"}

# Optional: self-ping to avoid free-tier idle sleep
@app.on_event("startup")
async def schedule_keep_alive():
    import asyncio, os, httpx

    async def keep_awake():
        # replace with your Render public URL, or set EXTERNAL_URL in env
        url = os.getenv("EXTERNAL_URL", "https://strangemetrics.onrender.com/")
        while True:
            await asyncio.sleep(60 * 2)        # every 2 minutes
            try:
                await httpx.get(url, timeout=10)
                print("✅ Self-ping successful")
            except Exception as e:
                print("⚠️ Keep-alive ping failed:", e)

    # fire & forget
    asyncio.create_task(keep_awake())

# Entry point for uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
