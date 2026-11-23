#!/usr/bin/env python3
"""Generate GitHub profile statistics from the GitHub REST API (stdlib only)."""
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
API = "https://api.github.com"
PALETTE = {
    "C": "#a5b4fc", "C++": "#f472b6", "Python": "#38bdf8",
    "JavaScript": "#fbbf24", "TypeScript": "#60a5fa", "HTML": "#fb7185",
    "CSS": "#a78bfa", "PHP": "#818cf8", "Java": "#f59e0b",
    "CMake": "#64748b", "Shell": "#86efac", "Jupyter Notebook": "#f97316",
}

def get(path, params=None):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "ahmed4k4-profile-stats"},
    )
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=25) as response:
        return __import__("json").load(response)

def collect(user):
    profile = get(f"/users/{user}")
    repositories, page = [], 1
    while True:
        batch = get(f"/users/{user}/repos", {"per_page": 100, "type": "owner", "page": page})
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    owned = [repo for repo in repositories if not repo.get("fork")]
    languages = {}
    for repo in owned[:100]:
        try:
            for language, size in get(f"/repos/{user}/{repo['name']}/languages").items():
                languages[language] = languages.get(language, 0) + size
        except Exception:
            pass
    commits = None
    try:
        commits = get("/search/commits", {"q": f"author:{user}", "per_page": 1}).get("total_count")
    except Exception:
        pass
    return {
        "repos": profile.get("public_repos", len(owned)),
        "stars": sum(repo.get("stargazers_count", 0) for repo in owned),
        "followers": profile.get("followers", 0),
        "commits": commits,
        "since": datetime.strptime(profile["created_at"], "%Y-%m-%dT%H:%M:%SZ").year,
        "langs": languages,
    }

def render(data):
    items = [
        ("Public repositories", data["repos"]),
        ("Public commits", data["commits"]),
        ("Stars earned", data["stars"]),
        ("Followers", data["followers"]),
    ]
    languages = sorted(data["langs"].items(), key=lambda item: item[1], reverse=True)[:6]
    total = sum(size for _, size in languages) or 1
    parts = []
    for index, (label, value) in enumerate(items):
        x = 40 + index * 230
        shown = "N/A" if value is None else f"{value:,}"
        parts.append(
            f'<g><text x="{x}" y="80" fill="#f8fafc" font-family="Arial,sans-serif" '
            f'font-size="38" font-weight="700">{shown}</text>'
            f'<text x="{x}" y="110" fill="#9db8c9" font-family="Arial,sans-serif" '
            f'font-size="15">{label}</text></g>'
        )
    bar_x, bar_y, bar_w = 40, 139, 900
    parts.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="12" rx="6" fill="#24465b"/>')
    cursor = bar_x
    for language, size in languages:
        width = bar_w * size / total
        color = PALETTE.get(language, "#22d3ee")
        parts.append(f'<rect x="{cursor:.2f}" y="{bar_y}" width="{max(width - 2, 1):.2f}" height="12" rx="4" fill="{color}"/>')
        cursor += width
    legend = "  •  ".join(f"{name} {size / total * 100:.1f}%" for name, size in languages)
    if not legend:
        legend = "Language data not available yet"
    parts.append(f'<text x="40" y="184" fill="#bed0dc" font-family="Arial,sans-serif" font-size="14">{legend}</text>')
    parts.append(f'<text x="960" y="184" text-anchor="end" fill="#718da0" font-family="Arial,sans-serif" font-size="12">GitHub since {data["since"]}</text>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 210" role="img" aria-labelledby="t d">'
        '<title id="t">Ahmed4k4 GitHub statistics</title>'
        '<desc id="d">Repository, commit, star, follower and top language data fetched from GitHub.</desc>'
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop stop-color="#081b2b"/><stop offset="1" stop-color="#12334a"/></linearGradient></defs>'
        '<rect width="1000" height="210" rx="18" fill="url(#bg)" stroke="#24465b"/>'
        '<path d="M24 20H976" stroke="#22d3ee" stroke-opacity=".35"/>'
        + "".join(parts)
        + "</svg>"
    )

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1].startswith("--"):
        raise SystemExit("Usage: python scripts/generate_stats.py <github-username>")
    try:
        data = collect(sys.argv[1])
        ASSETS.mkdir(exist_ok=True)
        (ASSETS / "github.svg").write_text(render(data), encoding="utf-8")
        print("Updated assets/github.svg from GitHub API")
    except Exception as exc:
        raise SystemExit(f"GitHub statistics were not refreshed; the non-numeric placeholder remains: {exc}")
