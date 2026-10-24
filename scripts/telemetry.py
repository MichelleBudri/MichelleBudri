#!/usr/bin/env python3
"""Generate assets/telemetry.svg — a self-hosted GitHub stats panel.

Reads the contribution calendar from the GitHub GraphQL API (needs GITHUB_TOKEN)
and renders one full-width space-themed SVG: a year of contributions, the
current streak and the contribution grid. Standard library only.
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "MichelleBudri")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

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


def plural(n, word):
    return f"{fmt(n)} {word}" + ("" if n == 1 else "s")


def build_svg():
    cal = graphql_contributions()

    total = cal["totalContributions"] if cal else None
    weeks = cal["weeks"][-52:] if cal else []
    days = [d for w in weeks for d in w["contributionDays"]]
    cur, longest = streaks(days) if days else (None, None)
    peak = max((d["contributionCount"] for d in days), default=0) or 1

    cells = []
    cw, gap, x0, y0 = 13, 4, 60, 118
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

    if cal:
        streak = (f'<text x="940" y="60" font-size="13" text-anchor="end" fill="#c9c3e8">'
                  f'{plural(cur, "day") + " in a row right now" if cur else "Ready for a new streak"}</text>'
                  f'<text x="940" y="84" font-size="13" text-anchor="end" fill="#6f6a96">'
                  f'longest run: {plural(longest, "day")}</text>')
        pending = ""
    else:
        streak = ""
        pending = ('<text x="500" y="182" text-anchor="middle" font-size="13" fill="#9c96c4">'
                   'Waiting for the first sync. Run the orbit workflow to fill this in.</text>')
    stamp = datetime.now(timezone.utc).strftime("%d %b %Y").lstrip("0")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 284" width="1000" height="284" role="img" aria-label="GitHub activity for {USER}: {fmt(total)} contributions in the last year">
  <defs>
    <linearGradient id="bgT" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#04050f"/><stop offset="55%" stop-color="#0a0922"/><stop offset="100%" stop-color="#170e33"/>
    </linearGradient>
    <radialGradient id="nT"><stop offset="0%" stop-color="#7b4dff" stop-opacity="0.30"/><stop offset="100%" stop-color="#7b4dff" stop-opacity="0"/></radialGradient>
    <radialGradient id="nT2"><stop offset="0%" stop-color="#31d0ff" stop-opacity="0.22"/><stop offset="100%" stop-color="#31d0ff" stop-opacity="0"/></radialGradient>
    <clipPath id="cardT"><rect width="1000" height="284" rx="20"/></clipPath>
    <style>
      .tw{{animation:tw 3.4s ease-in-out infinite}}.a1{{animation-delay:.6s}}.a2{{animation-delay:1.3s}}
      @keyframes tw{{0%,100%{{opacity:.2}}50%{{opacity:1}}}}
      @media (prefers-reduced-motion: reduce){{.tw{{animation:none}}}}
    </style>
  </defs>
  <g clip-path="url(#cardT)">
    <rect width="1000" height="284" fill="url(#bgT)"/>
    <ellipse cx="120" cy="10" rx="320" ry="150" fill="url(#nT)"/>
    <ellipse cx="920" cy="284" rx="300" ry="150" fill="url(#nT2)"/>
    <rect x="0" y="0" width="1000" height="284" rx="20" fill="none" stroke="#8fd8ff" stroke-opacity=".18"/>
    <g fill="#fff">
      <circle class="tw" cx="500" cy="18" r="1.1"/><circle class="tw a1" cx="880" cy="24" r="1.2"/>
      <circle class="tw a2" cx="40" cy="270" r="1"/><circle class="tw a1" cx="620" cy="272" r="1.1"/>
    </g>

    <g font-family="Segoe UI, Helvetica Neue, Arial, sans-serif">
      <text x="60" y="78" font-size="44" font-weight="700" fill="#ffffff">{fmt(total)}</text>
      <text x="60" y="100" font-size="13" fill="#9c96c4">contributions in the last year</text>
      {streak}
      {"".join(cells)}
      {pending}
      <text x="940" y="258" font-size="11" text-anchor="end" fill="#4f4b70">Updated {stamp}</text>
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
