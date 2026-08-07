#!/usr/bin/env python3
"""Generate assets/telemetry.svg — a self-hosted GitHub stats panel.

Reads public data from the GitHub API (GraphQL when GITHUB_TOKEN is set,
REST otherwise) and renders one full-width space-themed SVG: stat tiles,
contribution grid and a language bar. Standard library only.
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "MichelleBudri")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

PALETTE = ["#6c4cf1", "#8fd8ff", "#ff9ec7", "#7ee7c7", "#ffd97a", "#c3b0ff"]
HEAT = ["#141330", "#2a2668", "#4b3fb0", "#7a5cf0", "#a98bff"]


def _req(url, data=None, headers=None):
    hdrs = {"User-Agent": "moon-readme", "Accept": "application/vnd.github+json"}
    if TOKEN:
        hdrs["Authorization"] = f"Bearer {TOKEN}"
    hdrs.update(headers or {})
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=hdrs)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def rest_stats():
    out = {"repos": None, "stars": 0, "followers": None, "languages": {}, "since": None}
    try:
        u = _req(f"https://api.github.com/users/{USER}")
        out["repos"] = u.get("public_repos")
        out["followers"] = u.get("followers")
        out["since"] = (u.get("created_at") or "")[:4]
    except Exception as e:
        print("user endpoint failed:", e)
    try:
        repos = _req(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed")
        for r in repos:
            if r.get("fork"):
                continue
            out["stars"] += r.get("stargazers_count", 0)
            lang = r.get("language")
            if lang:
                out["languages"][lang] = out["languages"].get(lang, 0) + max(r.get("size", 1), 1)
    except Exception as e:
        print("repos endpoint failed:", e)
    return out


GQL = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}"""


def graphql_contributions():
    if not TOKEN:
        return None
    try:
        r = _req("https://api.github.com/graphql",
                 {"query": GQL, "variables": {"login": USER}},
                 {"Accept": "application/json"})
        return r["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    except Exception as e:
        print("graphql failed:", e)
        return None


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    cur = 0
    for i, d in enumerate(reversed(days)):
        if d["contributionCount"] > 0:
            cur += 1
        elif i == 0:
            continue          # today may still be in progress
        else:
            break
    return cur, longest


def fmt(n):
    if n is None:
        return "—"
    if n >= 1000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


def tile(x, y, label, value, color):
    return f"""
    <g>
      <rect x="{x}" y="{y}" width="215" height="82" rx="14" fill="#ffffff" fill-opacity=".04" stroke="{color}" stroke-opacity=".28"/>
      <circle cx="{x + 22}" cy="{y + 26}" r="4" fill="{color}"/>
      <text x="{x + 36}" y="{y + 30}" font-size="10.5" letter-spacing="2.2" fill="{color}">{label}</text>
      <text x="{x + 20}" y="{y + 66}" font-size="27" font-weight="700" fill="#ffffff">{value}</text>
    </g>"""


def build_svg():
    rest = rest_stats()
    cal = graphql_contributions()

    total = cal["totalContributions"] if cal else None
    weeks = cal["weeks"][-52:] if cal else []
    days = [d for w in weeks for d in w["contributionDays"]]
    cur, longest = streaks(days) if days else (None, None)
    peak = max((d["contributionCount"] for d in days), default=0) or 1

    cells = []
    cw, gap, x0, y0 = 13, 4, 60, 186
    for wi, w in enumerate(weeks):
        for d in w["contributionDays"]:
            di = datetime.strptime(d["date"], "%Y-%m-%d").weekday()
            di = (di + 1) % 7
            lvl = 0 if d["contributionCount"] == 0 else min(4, 1 + int(3 * d["contributionCount"] / peak))
            cells.append(f'<rect x="{x0 + wi * (cw + gap)}" y="{y0 + di * (cw + gap)}" '
                         f'width="{cw}" height="{cw}" rx="3.5" fill="{HEAT[lvl]}"/>')
    if not weeks:
        for wi in range(52):
            for di in range(7):
                cells.append(f'<rect x="{x0 + wi * (cw + gap)}" y="{y0 + di * (cw + gap)}" '
                             f'width="{cw}" height="{cw}" rx="3.5" fill="{HEAT[0]}"/>')

    langs = sorted(rest["languages"].items(), key=lambda kv: -kv[1])[:6]
    tot = sum(v for _, v in langs) or 1
    bar, legend, bx = [], [], 60
    for i, (name, size) in enumerate(langs):
        w = max(10, round(880 * size / tot))
        bar.append(f'<rect x="{bx}" y="336" width="{w}" height="12" rx="6" fill="{PALETTE[i % 6]}"/>')
        legend.append(f'<circle cx="{60 + i * 155}" cy="376" r="4.5" fill="{PALETTE[i % 6]}"/>'
                      f'<text x="{74 + i * 155}" y="380" font-size="12" fill="#c9c3e8">{name}'
                      f' <tspan fill="#6f6a96">{100 * size / tot:.0f}%</tspan></text>')
        bx += w + 3
    if not langs:
        bar.append('<rect x="60" y="336" width="880" height="12" rx="6" fill="#ffffff" fill-opacity=".07"/>')

    pending = ("" if rest["repos"] is not None else
               '<text x="500" y="250" text-anchor="middle" font-size="13" fill="#6f6a96">'
               'waiting for the first telemetry sync ✦ run the orbit workflow</text>')
    stamp = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC").upper()

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 404" width="1000" height="404" role="img" aria-label="GitHub telemetry for {USER}">
  <defs>
    <linearGradient id="bgT" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#04050f"/><stop offset="55%" stop-color="#0a0922"/><stop offset="100%" stop-color="#170e33"/>
    </linearGradient>
    <radialGradient id="nT"><stop offset="0%" stop-color="#7b4dff" stop-opacity="0.30"/><stop offset="100%" stop-color="#7b4dff" stop-opacity="0"/></radialGradient>
    <radialGradient id="nT2"><stop offset="0%" stop-color="#31d0ff" stop-opacity="0.22"/><stop offset="100%" stop-color="#31d0ff" stop-opacity="0"/></radialGradient>
    <clipPath id="cardT"><rect width="1000" height="404" rx="20"/></clipPath>
    <style>
      .tw{{animation:tw 3.4s ease-in-out infinite}}.a1{{animation-delay:.6s}}.a2{{animation-delay:1.3s}}
      @keyframes tw{{0%,100%{{opacity:.2}}50%{{opacity:1}}}}
      .fade{{animation:fade 1.2s ease-out both}}@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
    </style>
  </defs>
  <g clip-path="url(#cardT)">
    <rect width="1000" height="404" fill="url(#bgT)"/>
    <ellipse cx="120" cy="10" rx="320" ry="150" fill="url(#nT)"/>
    <ellipse cx="920" cy="400" rx="300" ry="150" fill="url(#nT2)"/>
    <rect x="0" y="0" width="1000" height="404" rx="20" fill="none" stroke="#8fd8ff" stroke-opacity=".18"/>
    <g fill="#fff">
      <circle class="tw" cx="500" cy="18" r="1.1"/><circle class="tw a1" cx="880" cy="24" r="1.2"/>
      <circle class="tw a2" cx="40" cy="396" r="1"/><circle class="tw a1" cx="620" cy="392" r="1.1"/>
    </g>

    <g font-family="Segoe UI, Helvetica Neue, Arial, sans-serif" class="fade">
      {tile(60, 34, "REPOSITORIES", fmt(rest["repos"]), "#8fd8ff")}
      {tile(287, 34, "STARS EARNED", fmt(rest["stars"]), "#ffd97a")}
      {tile(514, 34, "FOLLOWERS", fmt(rest["followers"]), "#ff9ec7")}
      {tile(741, 34, "CONTRIBUTIONS", fmt(total), "#7ee7c7")}

      <text x="60" y="156" font-size="10.5" letter-spacing="2.5" fill="#8fd8ff">ACTIVITY MAP · LAST 52 WEEKS</text>
      <text x="940" y="156" font-size="11.5" text-anchor="end" fill="#9c96c4" font-family="SFMono-Regular, Consolas, Menlo, monospace">streak {fmt(cur)}d · best {fmt(longest)}d</text>
      {"".join(cells)}

      <text x="60" y="322" font-size="10.5" letter-spacing="2.5" fill="#8fd8ff">LANGUAGE MIX</text>
      {"".join(bar)}
      {"".join(legend)}
      {pending}
      <text x="940" y="322" font-size="10" text-anchor="end" fill="#4f4b70" font-family="SFMono-Regular, Consolas, Menlo, monospace">updated {stamp}</text>
    </g>
  </g>
</svg>
"""


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "telemetry.svg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_svg())
    print(f"wrote {out}")
