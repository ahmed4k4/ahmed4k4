#!/usr/bin/env python3
"""Generate self-hosted animated GitHub profile statistics for Ahmed4k4.
Uses only the GitHub REST API and Python's standard library. The language mix
counts each repository's primary language (not the number of source bytes).
"""
import html, json, os, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

USERNAME = 'ahmed4k4'
ROOT = Path(__file__).resolve().parents[1]
API = 'https://api.github.com'
TOKEN = os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')

def api(path):
    headers = {'Accept':'application/vnd.github+json','User-Agent':'ahmed4k4-profile-stats'}
    if TOKEN: headers['Authorization'] = f'Bearer {TOKEN}'
    req = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)

def collect():
    profile = api(f'/users/{USERNAME}')
    repos=[]; page=1
    while True:
        batch=api(f'/users/{USERNAME}/repos?type=owner&per_page=100&page={page}&sort=updated')
        repos.extend(batch)
        if len(batch)<100: break
        page += 1
    own=[r for r in repos if not r.get('fork')]
    langs={}
    for repo in own:
        lang=repo.get('language')
        if lang: langs[lang]=langs.get(lang,0)+1
    return {
      'repos': int(profile.get('public_repos', len(own))),
      'followers': int(profile.get('followers',0)),
      'stars': sum(int(r.get('stargazers_count',0)) for r in own),
      'forks': sum(int(r.get('forks_count',0)) for r in own),
      'since': (profile.get('created_at') or '')[:4] or '—',
      'langs': langs,
      'updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
    }

def svg(data, compact=False):
    W,H=(600,480) if compact else (1200,330)
    labels=[('Public repositories',data['repos']),('Followers',data['followers']),('Stars',data['stars']),('Forks',data['forks'])]
    top=sorted(data['langs'].items(), key=lambda x:(-x[1],x[0]))[:6]
    total=sum(v for _,v in top) or 1
    colors=['#22d3ee','#8b5cf6','#34d399','#fbbf24','#60a5fa','#fb7185']
    def esc(x): return html.escape(str(x))
    out=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Live GitHub public profile metrics for {USERNAME}">
<title>GitHub activity for {USERNAME}</title><desc>Public repositories, followers, stars, forks and repository primary languages. Updated {esc(data['updated'])}.</desc>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#12121a"/><stop offset="1" stop-color="#0b0b0c"/></linearGradient><linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#22d3ee"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient><filter id="glow"><feGaussianBlur stdDeviation="12" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<style>@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}@keyframes drift{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(18px,-9px)}}}}@keyframes sweep{{0%{{transform:translateX(-120%)}}100%{{transform:translateX(120%)}}}}.m{{animation:rise .75s ease both}}.glow{{animation:drift 8s ease-in-out infinite}}.sweep{{animation:sweep 7s ease-in-out infinite}}@media(prefers-reduced-motion:reduce){{.m,.glow,.sweep{{animation:none!important}}}}</style>
<rect width="100%" height="100%" rx="24" fill="url(#bg)" stroke="#29283a"/><circle class="glow" cx="{W-35}" cy="20" r="185" fill="#8b5cf6" opacity=".09" filter="url(#glow)"/>
<text x="42" y="48" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="23" font-weight="700">GitHub activity · @{USERNAME}</text>
<text x="{W-42}" y="48" text-anchor="end" fill="#8a8a98" font-family="Segoe UI,Arial,sans-serif" font-size="13">On GitHub since {esc(data['since'])}</text>
<path d="M42 66H{W-42}" stroke="#29283a"/><rect class="sweep" x="42" y="65" width="{W*.22}" height="2" fill="url(#line)"/>
''']
    if not compact:
        x0=46; cell=(W-92)/4
        for i,(label,val) in enumerate(labels):
            x=x0+i*cell
            out.append(f'<g class="m" style="animation-delay:{i*.12:.2f}s"><text x="{x}" y="133" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="58" font-weight="700">{val:,}</text><text x="{x+2}" y="161" fill="#a7a7b5" font-family="Segoe UI,Arial,sans-serif" font-size="17">{esc(label)}</text></g>')
            if i: out.append(f'<path d="M{x-20} 94V170" stroke="#29283a"/>')
        base=225; x=48; barw=W-96
        out.append(f'<text x="48" y="207" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="17" font-weight="600">Repository primary languages</text>')
        out.append(f'<rect x="48" y="226" width="{barw}" height="13" rx="6.5" fill="#252531"/>')
        x=48
        for i,(name,val) in enumerate(top):
            w=barw*val/total
            out.append(f'<rect x="{x:.2f}" y="226" width="{max(w-2,1):.2f}" height="13" rx="5" fill="{colors[i]}"/>'); x+=w
        gap=barw/max(len(top),1)
        for i,(name,val) in enumerate(top):
            x=48+i*gap
            out.append(f'<circle cx="{x+6}" cy="278" r="5" fill="{colors[i]}"/><text x="{x+18}" y="283" fill="#d1d5df" font-family="Segoe UI,Arial,sans-serif" font-size="15">{esc(name)} · {val}</text>')
    else:
        for i,(label,val) in enumerate(labels):
            x=36+(i%2)*282; y=115+(i//2)*90
            out.append(f'<g class="m" style="animation-delay:{i*.12:.2f}s"><text x="{x}" y="{y}" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="48" font-weight="700">{val:,}</text><text x="{x+2}" y="{y+25}" fill="#a7a7b5" font-family="Segoe UI,Arial,sans-serif" font-size="16">{esc(label)}</text></g>')
        out.append('<path d="M36 300H564" stroke="#29283a"/><text x="36" y="332" fill="#f4f4f6" font-family="Segoe UI,Arial,sans-serif" font-size="17" font-weight="600">Primary repository languages</text>')
        x=36; y=354; barw=528
        out.append(f'<rect x="{x}" y="{y}" width="{barw}" height="12" rx="6" fill="#252531"/>')
        cur=x
        for i,(name,val) in enumerate(top):
            w=barw*val/total; out.append(f'<rect x="{cur:.2f}" y="{y}" width="{max(w-2,1):.2f}" height="12" rx="5" fill="{colors[i]}"/>'); cur+=w
        for i,(name,val) in enumerate(top[:4]):
            x=36+(i%2)*280; y=397+(i//2)*24
            out.append(f'<circle cx="{x+6}" cy="{y-5}" r="5" fill="{colors[i]}"/><text x="{x+18}" y="{y}" fill="#d1d5df" font-family="Segoe UI,Arial,sans-serif" font-size="14">{esc(name)} · {val}</text>')
    out.append(f'<text x="{W-36}" y="{H-16}" text-anchor="end" fill="#777789" font-family="Segoe UI,Arial,sans-serif" font-size="11">Updated {esc(data["updated"])} · GitHub REST API</text></svg>')
    return ''.join(out)

def main():
    try: data=collect()
    except Exception as exc:
        print(f'Could not refresh live GitHub stats: {exc}',file=sys.stderr); return 1
    (ROOT/'assets'/'github.svg').write_text(svg(data),'utf-8')
    (ROOT/'assets'/'sm'/'github.svg').write_text(svg(data,True),'utf-8')
    print('Updated GitHub stats:',json.dumps({k:v for k,v in data.items() if k!='langs'}))
    return 0
if __name__=='__main__': raise SystemExit(main())
