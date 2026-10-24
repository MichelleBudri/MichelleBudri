#!/usr/bin/env python3
"""GitHub activity for the mission-control panel (see mission_control.py).

Reads the contribution calendar from the GitHub GraphQL API (needs GITHUB_TOKEN)
and renders the activity quadrant: a year of contributions, the current
streak and the last 26 weeks of the contribution grid. Standard library only.
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


def activity_panel():
    """SVG fragment for the activity quadrant, in a local 500x330 frame."""
    cal = graphql_contributions()

    total = cal["totalContributions"] if cal else None
    all_days = [d for w in cal["weeks"] for d in w["contributionDays"]] if cal else []
    cur, longest = streaks(all_days) if all_days else (None, None)
    weeks = cal["weeks"][-26:] if cal else []
    peak = max((d["contributionCount"] for w in weeks for d in w["contributionDays"]), default=0) or 1

    cells = []
    cw, gap, x0, y0 = 13, 3.5, 36, 134
    for wi in range(26):
        days = weeks[wi]["contributionDays"] if wi < len(weeks) else []
        for d in days:
            di = (datetime.strptime(d["date"], "%Y-%m-%d").weekday() + 1) % 7
            lvl = 0 if d["contributionCount"] == 0 else min(4, 1 + int(3 * d["contributionCount"] / peak))
            cells.append(f'<rect x="{x0 + wi * (cw + gap)}" y="{y0 + di * (cw + gap)}" '
                         f'width="{cw}" height="{cw}" rx="3.5" fill="{HEAT[lvl]}"/>')
        if not days:
            cells += [f'<rect x="{x0 + wi * (cw + gap)}" y="{y0 + di * (cw + gap)}" '
                      f'width="{cw}" height="{cw}" rx="3.5" fill="{HEAT[0]}"/>' for di in range(7)]

    if cal:
        streak = (f'<text x="464" y="62" font-size="15" text-anchor="end" fill="#c9c3e8">'
                  f'{plural(cur, "day") + " in a row" if cur else "Ready for a new streak"}</text>'
                  f'<text x="464" y="86" font-size="14" text-anchor="end" fill="#6f6a96">'
                  f'longest run: {plural(longest, "day")}</text>')
    else:
        streak = ('<text x="464" y="62" font-size="14" text-anchor="end" fill="#9c96c4">'
                  'Waiting for the first sync</text>')
    stamp = datetime.now(timezone.utc).strftime("%d %b %Y").lstrip("0")

    return f"""
      <text x="34" y="84" font-size="48" font-weight="700" fill="#ffffff">{fmt(total)}</text>
      <text x="36" y="110" font-size="15" fill="#9c96c4">contributions in the last year</text>
      {streak}
      {"".join(cells)}
      <text x="36" y="296" font-size="13" fill="#6f6a96">Last 26 weeks</text>
      <text x="464" y="296" font-size="13" text-anchor="end" fill="#4f4b70">Updated {stamp}</text>""", total
