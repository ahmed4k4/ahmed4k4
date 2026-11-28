#!/usr/bin/env python3
"""Refresh public GitHub profile metrics for Ahmed4k4.

The comment figure is deliberately labelled as recent public comment events,
not a lifetime number: GitHub's public events API only exposes a limited recent
activity window (up to 300 events with this script).
"""
from __future__ import annotations

import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USERNAME = "ahmed4k4"
ROOT = Path(__file__).resolve().parents[1]
API = "https://api.github.com"
TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")


def api(path: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ahmed4k4-profile-stats",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def collect() -> dict:
    profile = api(f"/users/{USERNAME}")
    repos = []
    for page in range(1, 20):
        batch = api(f"/users/{USERNAME}/repos?type=owner&per_page=100&page={page}&sort=updated")
        repos.extend(batch)
        if len(batch) < 100:
            break
    own = [repo for repo in repos if not repo.get("fork")]
    languages: dict[str, int] = {}
    for repo in own:
        language = repo.get("language")
        if language:
            languages[language] = languages.get(language, 0) + 1

    comments = None
    events_scanned = 0
    try:
        events = []
        for page in range(1, 4):
            batch = api(f"/users/{USERNAME}/events/public?per_page=100&page={page}")
            events.extend(batch)
            if len(batch) < 100:
                break
        events_scanned = len(events)
        comments = sum(1 for event in events if event.get("type") == "IssueCommentEvent")
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f"Recent public comment events unavailable: {exc}", file=sys.stderr)

    return {
        "username": USERNAME,
        "public_repositories": int(profile.get("public_repos", len(own))),
        "followers": int(profile.get("followers", 0)),
        "stars": sum(int(repo.get("stargazers_count", 0)) for repo in own),
        "forks": sum(int(repo.get("forks_count", 0)) for repo in own),
        "open_issues_and_pull_requests": sum(int(repo.get("open_issues_count", 0)) for repo in own),
        "recent_comment_events": comments,
        "events_scanned": events_scanned,
        "since": (profile.get("created_at") or "")[:4] or "—",
        "languages": languages,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "comment_metric_note": "IssueCommentEvent count among the latest up to 300 public account events returned by GitHub; not a lifetime total.",
    }


def svg(data: dict, compact: bool = False) -> str:
    width, height = (600, 570) if compact else (1200, 380)
    metrics = [
        ("Public repositories", data["public_repositories"]),
        ("Followers", data["followers"]),
        ("Stars", data["stars"]),
        ("Forks", data["forks"]),
        ("Open issues / PRs", data["open_issues_and_pull_requests"]),
        ("Recent comment events", data["recent_comment_events"]),
    ]
    top = sorted(data["languages"].items(), key=lambda item: (-item[1], item[0]))[:6]
    total = sum(value for _, value in top) or 1
    colors = ["#22d3ee", "#8b5cf6", "#34d399", "#fbbf24", "#60a5fa", "#fb7185"]
    esc = lambda value: html.escape(str(value))
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Live GitHub metrics for {USERNAME}">
<title>GitHub activity for {USERNAME}</title><desc>Public repositories, followers, stars, forks, open issues and recent comment events, plus repository primary languages. Updated {esc(data['updated'])}.</desc>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#12121a"/><stop offset="1" stop-color="#0b0b0c"/></linearGradient><linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#22d3ee"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="12" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<style>@keyframes rise{{from{{opacity:0;transform:translateY(13px)}}to{{opacity:1;transform:translateY(0)}}}}@keyframes drift{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(15px,-8px)}}}}@keyframes sweep{{0%{{transform:translateX(-120%)}}100%{{transform:translateX(120%)}}}}.m{{animation:rise .7s ease both}}.glow{{animation:drift 8s ease-in-out infinite}}.sweep{{animation:sweep 7s ease-in-out infinite}}@media(prefers-reduced-motion:reduce){{.m,.glow,.sweep{{animation:none!important}}}}</style>
<rect width="100%" height="100%" rx="24" fill="url(#bg)" stroke="#29283a"/><circle class="glow" cx="{width-35}" cy="20" r="185" fill="#8b5cf6" opacity=".09" filter="url(#glow)"/>
<text x="38" y="43" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="22" font-weight="700">GitHub activity · @{USERNAME}</text><text x="{width-38}" y="43" text-anchor="end" fill="#8a8a98" font-family="Segoe UI,Arial,sans-serif" font-size="12">On GitHub since {esc(data['since'])}</text><path d="M38 60H{width-38}" stroke="#29283a"/><rect class="sweep" x="38" y="59" width="{width*.20}" height="2" fill="url(#line)"/>''']

    if not compact:
        x0 = 38
        cell = (width - 76) / len(metrics)
        for index, (label, value) in enumerate(metrics):
            x = x0 + index * cell
            display = "—" if value is None else f"{value:,}"
            size = 43 if index == 5 else 49
            parts.append(f'<g class="m" style="animation-delay:{index*.1:.2f}s"><text x="{x:.1f}" y="127" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="700">{display}</text><text x="{x+1:.1f}" y="153" fill="#a7a7b5" font-family="Segoe UI,Arial,sans-serif" font-size="13">{esc(label)}</text></g>')
            if index:
                parts.append(f'<path d="M{x-13:.1f} 88V165" stroke="#29283a"/>')
        bar_x, bar_y, bar_w = 40, 220, width - 80
        parts.append(f'<text x="40" y="197" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="16" font-weight="600">Repository primary languages</text><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="13" rx="6.5" fill="#252531"/>')
        cursor = bar_x
        for index, (name, value) in enumerate(top):
            segment = bar_w * value / total
            parts.append(f'<rect x="{cursor:.2f}" y="{bar_y}" width="{max(segment-2,1):.2f}" height="13" rx="5" fill="{colors[index]}"/>')
            cursor += segment
        gap = bar_w / max(len(top), 1)
        for index, (name, value) in enumerate(top):
            x = bar_x + index * gap
            parts.append(f'<circle cx="{x+5:.1f}" cy="278" r="5" fill="{colors[index]}"/><text x="{x+17:.1f}" y="283" fill="#d1d5df" font-family="Segoe UI,Arial,sans-serif" font-size="14">{esc(name)} · {value}</text>')
        note = "Comment events = latest up to 300 public events, not lifetime comments."
        parts.append(f'<text x="40" y="326" fill="#777789" font-family="Segoe UI,Arial,sans-serif" font-size="11">{esc(note)}</text>')
    else:
        for index, (label, value) in enumerate(metrics):
            x = 36 + (index % 2) * 282
            y = 112 + (index // 2) * 88
            display = "—" if value is None else f"{value:,}"
            parts.append(f'<g class="m" style="animation-delay:{index*.1:.2f}s"><text x="{x}" y="{y}" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="43" font-weight="700">{display}</text><text x="{x+2}" y="{y+23}" fill="#a7a7b5" font-family="Segoe UI,Arial,sans-serif" font-size="13">{esc(label)}</text></g>')
        parts.append('<path d="M36 378H564" stroke="#29283a"/><text x="36" y="405" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="16" font-weight="600">Primary repository languages</text><rect x="36" y="422" width="528" height="12" rx="6" fill="#252531"/>')
        cursor = 36
        for index, (name, value) in enumerate(top):
            segment = 528 * value / total
            parts.append(f'<rect x="{cursor:.2f}" y="422" width="{max(segment-2,1):.2f}" height="12" rx="5" fill="{colors[index]}"/>')
            cursor += segment
        for index, (name, value) in enumerate(top[:4]):
            x = 36 + (index % 2) * 280
            y = 468 + (index // 2) * 23
            parts.append(f'<circle cx="{x+6}" cy="{y-5}" r="5" fill="{colors[index]}"/><text x="{x+18}" y="{y}" fill="#d1d5df" font-family="Segoe UI,Arial,sans-serif" font-size="13">{esc(name)} · {value}</text>')
        parts.append('<text x="36" y="525" fill="#777789" font-family="Segoe UI,Arial,sans-serif" font-size="10">Recent comments count up to 300 public activity events, not lifetime.</text>')

    parts.append(f'<text x="{width-36}" y="{height-13}" text-anchor="end" fill="#777789" font-family="Segoe UI,Arial,sans-serif" font-size="10">Updated {esc(data["updated"])} · GitHub REST API</text></svg>')
    return "".join(parts)


def main() -> int:
    try:
        data = collect()
    except Exception as exc:  # keep the last committed metrics if API access fails
        print(f"Could not refresh GitHub stats: {exc}", file=sys.stderr)
        return 1
    (ROOT / "assets" / "github.svg").write_text(svg(data), encoding="utf-8")
    (ROOT / "assets" / "sm" / "github.svg").write_text(svg(data, compact=True), encoding="utf-8")
    public_data = {key: value for key, value in data.items() if key != "languages"}
    public_data["languages"] = data["languages"]
    (ROOT / "assets" / "github-stats.json").write_text(json.dumps(public_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Updated GitHub stats:", json.dumps({key: value for key, value in data.items() if key != "languages"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
