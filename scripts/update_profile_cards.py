#!/usr/bin/env python3
"""Generate the release SVGs used by the GitHub profile README.

The script intentionally uses only Python's standard library so the scheduled
workflow stays small, deterministic, and easy to audit.
"""

from __future__ import annotations

import html
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OWNER = "Zburgers"
ASSET_DIR = Path("assets")
REPOSITORIES = [
    {
        "repo": "vibevoice",
        "name": "VibeVoice",
        "summary": "Local-first desktop dictation with whisper.cpp and Tauri.",
        "signal": "Linux · Windows · macOS",
    },
    {
        "repo": "mdview",
        "name": "mdview",
        "summary": "Fast local-first Markdown reader with Mermaid support.",
        "signal": "Installers · updater · PDF",
    },
    {
        "repo": "FlashRL",
        "name": "FlashRL",
        "summary": "Reproducible DQN research benchmark and policy laboratory.",
        "signal": "Benchmark · checkpoint · demo",
    },
    {
        "repo": "SandlabsX",
        "name": "SandLabX",
        "summary": "Self-hosted browser lab platform built around QEMU/KVM.",
        "signal": "Virtualization · topology · systems",
    },
    {
        "repo": "agent-os",
        "name": "Goofy Agent OS",
        "summary": "Reliable control plane for agent and workflow operations.",
        "signal": "Approvals · idempotency · audit",
    },
    {
        "repo": "cb-connect",
        "name": "cb-connect",
        "summary": "Private, consent-first support and relationship check-ins.",
        "signal": "Privacy · support · product",
    },
]


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def truncate(value: str, limit: int) -> str:
    clean = " ".join(value.split())
    if len(clean) <= limit:
        return clean
    return clean[: max(0, limit - 1)].rstrip() + "…"


def github_json(path: str) -> Any:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Zburgers-profile-card-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urlopen(request, timeout=25) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"GitHub API request failed for {path}: {exc}") from exc


def latest_release(repository: str) -> dict[str, str] | None:
    releases = github_json(f"/repos/{OWNER}/{repository}/releases?per_page=20")
    if not isinstance(releases, list):
        raise RuntimeError(f"Unexpected release response for {repository}")

    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        published = release.get("published_at") or release.get("created_at") or ""
        return {
            "tag": str(release.get("tag_name") or "release"),
            "title": str(release.get("name") or release.get("tag_name") or "Release"),
            "published": str(published),
            "url": str(release.get("html_url") or ""),
        }
    return None


def recently_shipped_svg(items: list[dict[str, Any]]) -> str:
    shipped = [item for item in items if item["release"]]
    shipped.sort(key=lambda item: item["release"]["published"], reverse=True)
    cards = shipped[:3]

    while len(cards) < 3:
        cards.append(
            {
                "name": "Release slot",
                "summary": "The next published project release will appear here.",
                "signal": "Auto-synchronized",
                "release": {"tag": "waiting", "title": "Waiting", "published": ""},
            }
        )

    card_markup: list[str] = []
    for index, item in enumerate(cards):
        x = 28 + index * 296
        release = item["release"]
        card_markup.append(
            f"""
  <rect x="{x}" y="92" width="272" height="164" rx="11" fill="#161B22" stroke="#30363D"/>
  <text x="{x + 20}" y="122" class="mono project">{escape(truncate(item['name'], 24))}</text>
  <text x="{x + 20}" y="146" class="mono version">{escape(truncate(release['tag'], 25))}</text>
  <text x="{x + 20}" y="174" class="mono body">{escape(truncate(item['summary'], 38))}</text>
  <text x="{x + 20}" y="195" class="mono body">{escape(truncate(release['title'], 38))}</text>
  <text x="{x + 20}" y="229" class="mono muted">{escape(truncate(item['signal'], 37))}</text>"""
        )

    return f"""<svg width="920" height="290" viewBox="0 0 920 290" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Recently shipped projects</title>
  <desc id="desc">The three most recent stable GitHub releases across Nakshatra's selected projects.</desc>
  <defs>
    <linearGradient id="frame" x1="0" y1="0" x2="920" y2="290" gradientUnits="userSpaceOnUse">
      <stop stop-color="#2388FF" stop-opacity="0.8"/><stop offset="0.48" stop-color="#30363D"/><stop offset="1" stop-color="#58A6FF" stop-opacity="0.55"/>
    </linearGradient>
    <linearGradient id="scan" x1="0" y1="0" x2="180" y2="0" gradientUnits="userSpaceOnUse">
      <stop stop-color="#58A6FF" stop-opacity="0"/><stop offset="0.5" stop-color="#58A6FF" stop-opacity="0.12"/><stop offset="1" stop-color="#58A6FF" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    .mono {{ font-family: "JetBrains Mono", "SFMono-Regular", Consolas, monospace; }}
    .title {{ fill: #F0F6FC; font-size: 20px; font-weight: 700; }}
    .kicker {{ fill: #58A6FF; font-size: 12px; font-weight: 700; letter-spacing: 1.5px; }}
    .project {{ fill: #F0F6FC; font-size: 17px; font-weight: 700; }}
    .version {{ fill: #79C0FF; font-size: 13px; font-weight: 700; }}
    .body {{ fill: #B1BAC4; font-size: 12.5px; }}
    .muted {{ fill: #8B949E; font-size: 11px; }}
    .scanline {{ animation: travel 8s linear infinite; }}
    .dot {{ animation: pulse 1.8s ease-in-out infinite; transform-origin: center; }}
    @keyframes travel {{ from {{ transform: translateX(-200px); }} to {{ transform: translateX(1120px); }} }}
    @keyframes pulse {{ 0%, 100% {{ opacity: .35; }} 50% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion: reduce) {{ .scanline, .dot {{ animation: none; }} }}
  </style>
  <rect x="0.75" y="0.75" width="918.5" height="288.5" rx="14" fill="#0D1117" stroke="url(#frame)" stroke-width="1.5"/>
  <rect class="scanline" x="0" y="1" width="180" height="288" fill="url(#scan)"/>
  <text x="28" y="38" class="mono kicker">RECENTLY SHIPPED</text>
  <text x="28" y="67" class="mono title">Public releases with runnable artifacts and evidence</text>
  <circle cx="881" cy="31" r="4" fill="#3FB950" class="dot"/>
  <text x="868" y="35" text-anchor="end" class="mono muted">AUTO-SYNC</text>
{''.join(card_markup)}
  <text x="460" y="278" text-anchor="middle" class="mono muted">Synchronized from stable releases published across the selected repositories.</text>
</svg>
"""


def release_strip_svg(items: list[dict[str, Any]]) -> str:
    pills: list[str] = []
    for index, item in enumerate(items):
        row, column = divmod(index, 3)
        x = 24 + column * 298
        y = 45 + row * 60
        tag = item["release"]["tag"] if item["release"] else "active development"
        pills.append(
            f"""
  <g transform="translate({x} {y})">
    <rect width="276" height="45" rx="9" fill="#161B22" stroke="#30363D"/>
    <text x="14" y="19" class="mono name">{escape(truncate(item['name'], 24))}</text>
    <text x="14" y="36" class="mono tag">{escape(truncate(tag, 30))}</text>
  </g>"""
        )

    return f"""<svg width="920" height="168" viewBox="0 0 920 168" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Live release radar</title>
  <desc id="desc">Stable release status across Nakshatra's selected public projects.</desc>
  <style>
    .mono {{ font-family: "JetBrains Mono", "SFMono-Regular", Consolas, monospace; }}
    .heading {{ fill: #8B949E; font-size: 11px; font-weight: 700; letter-spacing: 1.7px; }}
    .name {{ fill: #F0F6FC; font-size: 13px; font-weight: 700; }}
    .tag {{ fill: #79C0FF; font-size: 12px; }}
    .live {{ animation: pulse 1.8s ease-in-out infinite; transform-origin: center; }}
    @keyframes pulse {{ 0%, 100% {{ opacity: .35; transform: scale(.85); }} 50% {{ opacity: 1; transform: scale(1.15); }} }}
    @media (prefers-reduced-motion: reduce) {{ .live {{ animation: none; }} }}
  </style>
  <rect x="0.75" y="0.75" width="918.5" height="166.5" rx="13" fill="#0D1117" stroke="#30363D" stroke-width="1.5"/>
  <text x="24" y="28" class="mono heading">LIVE RELEASE RADAR · AUTO-REFRESHED DAILY</text>
  <circle cx="888" cy="24" r="4" fill="#3FB950" class="live"/>
{''.join(pills)}
</svg>
"""


def write_if_changed(path: Path, content: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        print(f"unchanged: {path}")
        return
    path.write_text(content, encoding="utf-8")
    print(f"updated: {path}")


def main() -> None:
    items: list[dict[str, Any]] = []
    for config in REPOSITORIES:
        release = latest_release(config["repo"])
        items.append({**config, "release": release})

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    write_if_changed(ASSET_DIR / "recently-shipped.svg", recently_shipped_svg(items))
    write_if_changed(ASSET_DIR / "release-strip.svg", release_strip_svg(items))


if __name__ == "__main__":
    main()
