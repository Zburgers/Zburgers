#!/usr/bin/env python3
"""Build public profile artwork. Network failures leave the last good snapshot intact."""
import html
import json
import os
import textwrap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
OWNER = 'Zburgers'
PROJECTS = [
    ('vibevoice', 'VibeVoice', 'A quieter way to talk to your computer.', 'Local dictation, developer-term cleanup and native desktop releases.', 'Rust / Tauri / whisper.cpp', 'voice', '#e4be89'),
    ('mdview', 'mdview', 'Markdown, with room to think.', 'Local files, safe rendering, Mermaid diagrams and native updates.', 'TypeScript / Tauri', 'document', '#a5c4d4'),
    ('SandlabsX', 'SandLabX', 'An entire network, inside a browser.', 'Repeatable VM labs, copy-on-write disks and browser consoles.', 'QEMU / KVM / PostgreSQL', 'network', '#b5c8a5'),
    ('FlashRL', 'FlashRL', 'Make the experiment repeatable.', 'Five training seeds. 500 held-out episodes. A policy you can inspect.', 'Python / PyTorch / Gymnasium', 'chart', '#d3b2a7'),
    ('crip-wallet', 'Crip Wallet', 'Give agents a budget. Keep control.', 'Atomic budgets, approvals, revocation and recovery. Local test network.', 'TypeScript / policy / audit', 'wallet', '#cab9d8'),
    ('agent-os', 'Agent OS', 'Automation that remembers what happened.', 'Durable workflows, approval boundaries, idempotency and audit trails.', 'Node.js / PostgreSQL', 'flow', '#91bfba'),
]

def api(path, payload=None):
    headers={'Accept':'application/vnd.github+json','User-Agent':'Zburgers-profile'}
    token=os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN')
    if token: headers['Authorization']=f'Bearer {token}'
    data=json.dumps(payload).encode() if payload else None
    with urlopen(Request('https://api.github.com'+path,data=data,headers=headers),timeout=30) as response:
        result=json.load(response)
    if isinstance(result,dict) and result.get('errors'): raise RuntimeError('GitHub returned an incomplete GraphQL response')
    return result

def esc(value): return html.escape(str(value),quote=True)

def svg(body,width,height,title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title"><title id="title">{esc(title)}</title>
<style>text{{font-family:Arial,Helvetica,sans-serif}}.mono{{font-family:Consolas,monospace}}.motion{{animation:drift 5s ease-in-out infinite}}@keyframes drift{{50%{{opacity:.45;transform:translateY(-3px)}}}}@media(prefers-reduced-motion:reduce){{.motion{{animation:none}}}}</style>
<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="14" fill="#111a27" stroke="#344151"/>{body}</svg>'''

def motif(kind,color):
    if kind=='voice':
        shapes=''.join(f'<rect class="motion" style="animation-delay:{i*.13}s" x="{i*9}" y="{30-h/2}" width="4" height="{h}" rx="2"/>' for i,h in enumerate([10,22,38,52,28,44,18,32,10]))
    elif kind=='document': shapes='<g fill="none" stroke-width="2"><rect x="14" y="3" width="45" height="55" rx="4"/><path d="M24 16h24M24 25h16M24 34h24M24 44h12"/></g>'
    elif kind=='network': shapes='<g fill="none" stroke-width="2"><path d="M10 15 40 36 70 10M40 36 66 58M40 36 8 58"/><circle cx="10" cy="15" r="6"/><circle cx="40" cy="36" r="9"/><circle cx="70" cy="10" r="6"/><circle cx="66" cy="58" r="6"/><circle cx="8" cy="58" r="6"/></g>'
    elif kind=='chart': shapes='<g fill="none" stroke-width="2"><path d="M0 56H76M0 5V56" opacity=".4"/><path class="motion" d="m4 49 10-4 9 3 9-16 10 3 9-19 11 4L74 6"/><path d="M4 44 18 40 30 42 42 37 54 39 74 30" opacity=".35"/></g>'
    elif kind=='wallet': shapes='<g fill="none" stroke-width="2"><rect x="4" y="12" width="68" height="43" rx="7"/><path d="M55 24h22v20H55zM14 12V5h47v7"/><circle cx="63" cy="34" r="2"/></g>'
    else: shapes='<g fill="none" stroke-width="2"><rect x="0" y="20" width="18" height="20" rx="3"/><rect x="31" y="20" width="18" height="20" rx="3"/><rect x="62" y="20" width="18" height="20" rx="3"/><path d="M18 30h13M49 30h13M71 20V8H9v12"/></g>'
    return f'<g transform="translate(347 22)" fill="{color}" stroke="{color}" opacity=".8">{shapes}</g>'

def project_card(config,repo,release):
    name,title,tagline,description,stack,kind,color=config
    body=motif(kind,color)
    body+=f'<text x="24" y="35" fill="{color}" font-size="11" class="mono">{esc(stack)}</text><text x="24" y="73" fill="#f0ece3" font-size="27" font-weight="700">{title}</text>'
    body+=f'<text x="24" y="108" fill="#e0e5eb" font-size="16">{esc(tagline)}</text>'
    for i,line in enumerate(textwrap.wrap(description,51)):
        body+=f'<text x="24" y="137" dy="{i*19}" fill="#a9b6c6" font-size="14">{esc(line)}</text>'
    label=f"release {release['tag_name']}" if release else f"updated {repo['pushed_at'][:10]}"
    body+=f'<path d="M24 180h392" stroke="#2d3c4e"/><text x="24" y="207" fill="{color}" font-size="12" class="mono">{esc(label[:40])}</text><text x="416" y="207" text-anchor="end" fill="#a9b6c6" font-size="17">↗</text>'
    return svg(body,440,228,f'{title}: {tagline} {description} {label}')

def snapshot(repos,merged,contributions,languages,now):
    originals=[r for r in repos if not r['fork'] and not r['archived']]
    metrics=[('CONTRIBUTIONS · LAST YEAR',contributions),('PUBLIC REPOSITORIES',len(repos)),('MERGED PUBLIC PRS',merged),('STARS · ORIGINAL REPOS',sum(r['stargazers_count'] for r in originals))]
    body=f'<text x="24" y="32" font-size="12" fill="#d9c39d" class="mono">ON GITHUB</text><text x="896" y="32" text-anchor="end" font-size="11" fill="#9baabd">{now:%d %b %Y} UTC</text>'
    for i,(label,value) in enumerate(metrics):
        x=24+i*225
        body+=f'<text x="{x}" y="83" font-size="32" font-weight="700" fill="#f1ede5">{value:,}</text><text x="{x}" y="108" font-size="10" fill="#a9b6c6" class="mono">{label}</text>'
    total=sum(languages.values()) or 1
    top=languages.most_common(5)
    if sum(v for _,v in top)<total: top.append(('Other',total-sum(v for _,v in top)))
    cursor=24
    palette=['#d8b98d','#9abed0','#b5c79e','#c9b0ce','#cf9f91','#546479']
    for i,((language,value),color) in enumerate(zip(top,palette)):
        width=872*value/total
        body+=f'<rect x="{cursor:.2f}" y="142" width="{width:.2f}" height="10" fill="{color}"/>'
        cursor+=width
        x=24+(i%3)*295;y=184+(i//3)*26
        body+=f'<circle cx="{x+4}" cy="{y-4}" r="4" fill="{color}"/><text x="{x+17}" y="{y}" font-size="13" fill="#c3ccd8">{esc(language)} · {value/total:.1%}</text>'
    body+='<text x="24" y="240" font-size="11" fill="#91a1b4">Language share by bytes in original, non-archived public repositories.</text>'
    return svg(body,920,260,'GitHub activity and public repository languages')

def main():
    repos=[];page=1
    while True:
        batch=api(f'/users/{OWNER}/repos?per_page=100&type=owner&page={page}')
        repos.extend(batch)
        if len(batch)<100: break
        page+=1
    by_name={r['name'].lower():r for r in repos}
    assert all(p[0].lower() in by_name for p in PROJECTS)
    pending={}
    for config in PROJECTS:
        releases=api(f'/repos/{OWNER}/{config[0]}/releases?per_page=20')
        release=next((r for r in releases if not r['draft'] and not r['prerelease']),None)
        pending[f'project-{config[0].lower()}.svg']=project_card(config,by_name[config[0].lower()],release)
    languages=Counter()
    for repo in repos:
        if not repo['fork'] and not repo['archived']:
            languages.update(api(f'/repos/{OWNER}/{repo["name"]}/languages'))
    merged=api(f'/search/issues?q=type%3Apr+author%3A{OWNER}+is%3Amerged+is%3Apublic&per_page=1')['total_count']
    query='{user(login:"Zburgers"){contributionsCollection{contributionCalendar{totalContributions}}}}'
    contributions=api('/graphql',{'query':query})['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions']
    pending['github-snapshot.svg']=snapshot(repos,merged,contributions,languages,datetime.now(timezone.utc))
    # Fetch and validate everything before replacing the last successful snapshot.
    OUT.mkdir(exist_ok=True)
    for filename,content in pending.items():
        temp=OUT/(filename+'.tmp');temp.write_text(content,encoding='utf-8');temp.replace(OUT/filename)
    print(f'Updated {len(pending)} assets from {len(repos)} public repositories.')

if __name__=='__main__': main()
