#!/usr/bin/env python3
"""Generate assets/mission-control.svg — one panel with four quadrants.

  whoami terminal   | currently in orbit
  ------------------+-------------------
  GitHub activity   | moon phase today

The top half is static; activity and moon are recalculated every run.
Run it locally or let the daily GitHub Action (.github/workflows/orbit.yml)
keep it fresh. Standard library only.
"""

import os
from datetime import datetime, timezone

from moon_phase import moon_panel
from telemetry import activity_panel, fmt

W, BAR, TOP, BOTTOM = 1000, 44, 300, 330
H = BAR + TOP + BOTTOM

ORBIT = [
    ("Software architecture", "learning", "#8fd8ff"),
    ("Advanced TypeScript", "leveling up", "#c3b0ff"),
    ("Accessibility", "deep diving", "#ff9ec7"),
    ("Mobile performance", "tuning engines", "#7ee7c7"),
    ("AI engineering", "researching", "#ffd27a"),
]

TERMINAL = """
      <g font-family="SFMono-Regular, Consolas, Menlo, monospace" font-size="15">
        <g class="l1">
          <text x="36" y="52" fill="#7ee7c7">$</text><text x="58" y="52" fill="#8fd8ff">whoami</text>
          <text x="36" y="76" fill="#4f4b70">›</text><text x="58" y="76" fill="#ffffff">Michelle Budri Bognar</text>
        </g>
        <g class="l2">
          <text x="36" y="116" fill="#7ee7c7">$</text><text x="58" y="116" fill="#8fd8ff">locate --home</text>
          <text x="36" y="140" fill="#4f4b70">›</text><text x="58" y="140" fill="#c9c3e8">Brazil, Earth, Milky Way</text>
        </g>
        <g class="l3">
          <text x="36" y="180" fill="#7ee7c7">$</text><text x="58" y="180" fill="#8fd8ff">cat mission.txt</text>
          <text x="36" y="204" fill="#4f4b70">›</text><text x="58" y="204" fill="#c9c3e8">software that feels made for people</text>
        </g>
        <g class="l4">
          <text x="36" y="244" fill="#7ee7c7">$</text><text x="58" y="244" fill="#8fd8ff">status</text>
          <circle cx="63" cy="263" r="4.5" fill="#7ee7c7" class="dot"/>
          <text x="76" y="268" fill="#ffffff">building, learning, researching</text>
          <rect class="cur" x="368" y="255" width="9" height="16" fill="#8fd8ff"/>
        </g>
      </g>"""


def orbit_panel():
    rows = []
    for i, (name, status, color) in enumerate(ORBIT):
        y = 104 + i * 44
        x1 = 54 + len(name) * 9 + 16          # rough text widths for the dotted leader
        x2 = 464 - len(status) * 7.4 - 16
        rows.append(f"""
        <g transform="translate(0,{y})">
          <circle cx="40" cy="-5" r="4.5" fill="{color}" class="orb"/>
          <text x="54" y="0" font-size="16" font-weight="600" fill="#ffffff">{name}</text>
          <line x1="{x1:.0f}" y1="-5" x2="{x2:.0f}" y2="-5" stroke="{color}" stroke-opacity=".45" stroke-width="2" stroke-linecap="round" stroke-dasharray="0 9"/>
          <text class="p{i + 1}" x="464" y="0" font-size="14.5" text-anchor="end" fill="{color}">{status}</text>
        </g>""")
    return ('\n      <text x="36" y="56" font-size="18" font-weight="700" fill="#ffffff">Currently in orbit</text>'
            + "".join(rows))


def build_svg(now):
    moon_defs, moon_body, phase = moon_panel(now)
    activity, total = activity_panel()
    mid = BAR + TOP

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Mission control. Michelle Budri Bognar, software developer in Brazil, building software that feels made for people. Currently learning software architecture, advanced TypeScript, accessibility, mobile performance and AI engineering. {fmt(total)} GitHub contributions in the last year. Moon today: {phase}.">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#04050f"/><stop offset="55%" stop-color="#0a0922"/><stop offset="100%" stop-color="#170e33"/>
    </linearGradient>
    <radialGradient id="nA"><stop offset="0%" stop-color="#7b4dff" stop-opacity="0.30"/><stop offset="100%" stop-color="#7b4dff" stop-opacity="0"/></radialGradient>
    <radialGradient id="nB"><stop offset="0%" stop-color="#31d0ff" stop-opacity="0.20"/><stop offset="100%" stop-color="#31d0ff" stop-opacity="0"/></radialGradient>
    <radialGradient id="nC"><stop offset="0%" stop-color="#ff5fa2" stop-opacity="0.18"/><stop offset="100%" stop-color="#ff5fa2" stop-opacity="0"/></radialGradient>
    {moon_defs}
    <clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
    <style>
      .tw{{animation:tw 3.4s ease-in-out infinite}}.a1{{animation-delay:.6s}}.a2{{animation-delay:1.3s}}.a3{{animation-delay:2s}}
      @keyframes tw{{0%,100%{{opacity:.2}}50%{{opacity:1}}}}
      .l1{{animation:in .5s ease-out .2s both}}.l2{{animation:in .5s ease-out .7s both}}
      .l3{{animation:in .5s ease-out 1.2s both}}.l4{{animation:in .5s ease-out 1.7s both}}
      @keyframes in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
      .cur{{animation:blink 1.1s steps(1) 2.2s infinite both}}
      @keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
      .dot,.orb{{animation:pulse 3.5s ease-in-out infinite}}
      @keyframes pulse{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
      .p1{{animation:pop 1.8s ease-out .3s both}}.p2{{animation:pop 1.8s ease-out .45s both}}
      .p3{{animation:pop 1.8s ease-out .6s both}}.p4{{animation:pop 1.8s ease-out .75s both}}
      .p5{{animation:pop 1.8s ease-out .9s both}}
      @keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}
      .breathe{{animation:breathe 6s ease-in-out infinite}}
      @keyframes breathe{{0%,100%{{opacity:.5}}50%{{opacity:1}}}}
      .float{{animation:float 9s ease-in-out infinite}}
      @keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-6px)}}}}
      .ping{{animation:ping 2.6s ease-out infinite}}
      @keyframes ping{{0%{{r:4;opacity:.9}}100%{{r:15;opacity:0}}}}
      @media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
    </style>
  </defs>

  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <ellipse cx="900" cy="40" rx="320" ry="170" fill="url(#nA)"/>
    <ellipse cx="80" cy="{H - 20}" rx="320" ry="170" fill="url(#nB)"/>
    <ellipse cx="560" cy="{mid}" rx="260" ry="140" fill="url(#nC)"/>
    <rect width="{W}" height="{H}" rx="20" fill="none" stroke="#8fd8ff" stroke-opacity=".18"/>
    <g fill="#fff">
      <circle class="tw" cx="420" cy="96" r="1.1"/><circle class="tw a1" cx="960" cy="320" r="1.2"/>
      <circle class="tw a2" cx="470" cy="420" r="1"/><circle class="tw a3" cx="530" cy="640" r="1.1"/>
      <circle class="tw a1" cx="30" cy="330" r="1"/><circle class="tw a2" cx="960" cy="560" r="1.2"/>
    </g>

    <path d="M0 0 h{W} v{BAR} h-{W} z" fill="#ffffff" fill-opacity=".04"/>
    <g stroke="#8fd8ff" stroke-opacity=".14">
      <path d="M0 {BAR} h{W}"/>
      <path d="M24 {mid} h{W - 48}"/>
      <path d="M500 {BAR + 24} v{TOP + BOTTOM - 48}"/>
    </g>
    <circle cx="28" cy="22" r="5.5" fill="#ff5f57"/><circle cx="48" cy="22" r="5.5" fill="#febc2e"/><circle cx="68" cy="22" r="5.5" fill="#28c840"/>
    <text x="500" y="27" text-anchor="middle" font-size="13" fill="#8f89b8" font-family="SFMono-Regular, Consolas, Menlo, monospace">michelle@orbit: ~/mission-control</text>

    <g font-family="Segoe UI, Helvetica Neue, Arial, sans-serif">
      <g transform="translate(0,{BAR})">{TERMINAL}</g>
      <g transform="translate(500,{BAR})">{orbit_panel()}</g>
      <g transform="translate(0,{mid})">{activity}</g>
      <g transform="translate(500,{mid})">{moon_body}</g>
    </g>
  </g>
</svg>
"""


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "mission-control.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_svg(datetime.now(timezone.utc)))
    print(f"wrote {out}")
