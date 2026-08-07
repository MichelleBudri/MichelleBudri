#!/usr/bin/env python3
"""Generate assets/moon-phase.svg with the Moon's real phase for today.

No dependencies, no external APIs. Run it locally or let the daily
GitHub Action (.github/workflows/orbit.yml) keep it fresh.

The Moon is drawn as seen from the SOUTHERN hemisphere (Brazil).
Set HEMISPHERE = "north" to flip it.
"""

import math
import os
from datetime import datetime, timedelta, timezone

HEMISPHERE = "south"
SYNODIC = 29.530588853
BRT = timezone(timedelta(hours=-3))

NAMES = [
    (0.02, "New Moon"),
    (0.24, "Waxing Crescent"),
    (0.28, "First Quarter"),
    (0.48, "Waxing Gibbous"),
    (0.52, "Full Moon"),
    (0.72, "Waning Gibbous"),
    (0.78, "Last Quarter"),
    (0.98, "Waning Crescent"),
    (1.01, "New Moon"),
]

CYCLE_LABELS = ["New", "W. Cres", "First Q", "W. Gib", "Full", "Wan. Gib", "Last Q", "Wan. Cres"]


def _julian_day(now: datetime) -> float:
    return now.timestamp() / 86400.0 + 2440587.5


def phase_data(now: datetime):
    """Meeus (Astronomical Algorithms, ch. 48) low-precision phase angle."""
    t = (_julian_day(now) - 2451545.0) / 36525.0
    rad = math.radians

    d = 297.8501921 + 445267.1114034 * t - 0.0018819 * t**2   # mean elongation
    m = 357.5291092 + 35999.0502909 * t                       # Sun mean anomaly
    mp = 134.9633964 + 477198.8675055 * t + 0.0087414 * t**2  # Moon mean anomaly
    d, m, mp = d % 360, m % 360, mp % 360

    i = (180 - d
         - 6.289 * math.sin(rad(mp))
         + 2.100 * math.sin(rad(m))
         - 1.274 * math.sin(rad(2 * d - mp))
         - 0.658 * math.sin(rad(2 * d))
         - 0.214 * math.sin(rad(2 * mp))
         - 0.110 * math.sin(rad(d)))

    illum = (1 + math.cos(rad(i))) / 2
    frac = (d % 360) / 360.0
    age = frac * SYNODIC
    name = next(n for limit, n in NAMES if frac < limit)
    return age, frac, illum, name


def next_event(now: datetime, target_frac: float):
    """Days until the Moon next reaches a given point of the cycle."""
    step = timedelta(hours=1)
    probe = now
    prev = (phase_data(probe)[1] - target_frac) % 1.0
    for _ in range(24 * 32):
        probe += step
        cur = (phase_data(probe)[1] - target_frac) % 1.0
        if cur < prev and prev > 0.5:
            return probe
        prev = cur
    return probe


def lit_path(cx, cy, r, frac, illum):
    """SVG path of the illuminated area, northern-hemisphere orientation."""
    rx = abs(r * (2 * illum - 1))
    waxing = frac < 0.5
    if waxing:
        limb, term = 1, (0 if illum < 0.5 else 1)
    else:
        limb, term = 0, (1 if illum < 0.5 else 0)
    top, bottom = cy - r, cy + r
    return (f"M {cx} {top} A {r} {r} 0 0 {limb} {cx} {bottom} "
            f"A {rx:.3f} {r} 0 0 {term} {cx} {top} Z")


def mini_moon(cx, cy, r, frac, active):
    illum = (1 - math.cos(2 * math.pi * frac)) / 2
    path = lit_path(cx, cy, r, frac, illum)
    flip = f'transform="translate({2 * cx},0) scale(-1,1)"' if HEMISPHERE == "south" else ""
    fill = "#fff6da" if active else "#cfc6f2"
    op = "1" if active else ".62"
    ring = (f'<circle cx="{cx}" cy="{cy}" r="{r + 6}" fill="none" stroke="#ffd97a" '
            f'stroke-opacity=".85" stroke-width="1.4"/>') if active else ""
    return (f'<g opacity="{op}">{ring}<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0c0b1e"/>'
            f'<g {flip}><path d="{path}" fill="{fill}"/></g>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#8fd8ff" stroke-opacity=".25"/></g>')


def build_svg(now: datetime) -> str:
    age, frac, illum, name = phase_data(now)
    cx, cy, r = 150, 132, 92
    path = lit_path(cx, cy, r, frac, illum)
    flip = f'transform="translate({2 * cx},0) scale(-1,1)"' if HEMISPHERE == "south" else ""

    local = now.astimezone(BRT)
    date_label = local.strftime("%A · %d %B %Y").upper()

    full = next_event(now, 0.5)
    new = next_event(now, 0.0)
    d_full = max(0, round((full - now).total_seconds() / 86400))
    d_new = max(0, round((new - now).total_seconds() / 86400))

    strip = "".join(
        mini_moon(650 + i * 42, 178, 13, i / 8.0, round(frac * 8) % 8 == i)
        for i in range(8)
    )
    marker_x = 648 + frac * 306

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 264" width="1000" height="264" role="img" aria-label="Moon phase today: {name}, {illum * 100:.0f}% illuminated">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#04050f"/>
      <stop offset="55%" stop-color="#0a0922"/>
      <stop offset="100%" stop-color="#190f36"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%">
      <stop offset="0%" stop-color="#fff6d8" stop-opacity="0.34"/>
      <stop offset="100%" stop-color="#fff6d8" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="neb" cx="50%" cy="50%">
      <stop offset="0%" stop-color="#7b4dff" stop-opacity="0.40"/>
      <stop offset="100%" stop-color="#7b4dff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="lit" cx="36%" cy="30%">
      <stop offset="0%" stop-color="#fffdf3"/>
      <stop offset="62%" stop-color="#f2e9d5"/>
      <stop offset="100%" stop-color="#cbbb9d"/>
    </radialGradient>
    <linearGradient id="track" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#8fd8ff" stop-opacity=".15"/>
      <stop offset="50%" stop-color="#8fd8ff" stop-opacity=".55"/>
      <stop offset="100%" stop-color="#8fd8ff" stop-opacity=".15"/>
    </linearGradient>
    <clipPath id="disc"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>
    <clipPath id="card"><rect width="1000" height="264" rx="20"/></clipPath>
    <style>
      .tw {{ animation: tw 3s ease-in-out infinite }}
      .b {{ animation-delay:.8s }} .c {{ animation-delay:1.6s }} .d {{ animation-delay:2.3s }}
      @keyframes tw {{ 0%,100% {{ opacity:.2 }} 50% {{ opacity:1 }} }}
      .breathe {{ animation: breathe 6s ease-in-out infinite }}
      @keyframes breathe {{ 0%,100% {{ opacity:.5 }} 50% {{ opacity:1 }} }}
      .float {{ animation: float 9s ease-in-out infinite }}
      @keyframes float {{ 0%,100% {{ transform: translateY(0) }} 50% {{ transform: translateY(-7px) }} }}
      .ping {{ animation: ping 2.6s ease-out infinite }}
      @keyframes ping {{ 0% {{ r:4; opacity:.9 }} 100% {{ r:15; opacity:0 }} }}
    </style>
  </defs>

  <g clip-path="url(#card)">
    <rect width="1000" height="264" fill="url(#bg)"/>
    <ellipse cx="120" cy="40" rx="280" ry="150" fill="url(#neb)"/>
    <rect x="0" y="0" width="1000" height="264" rx="20" fill="none" stroke="#8fd8ff" stroke-opacity=".18"/>

    <g fill="#fff">
      <circle class="tw"   cx="352" cy="42"  r="1.4"/><circle class="tw b" cx="430" cy="96"  r="1"/>
      <circle class="tw c" cx="510" cy="52"  r="1.5"/><circle class="tw d" cx="600" cy="118" r="1.2"/>
      <circle class="tw b" cx="700" cy="46"  r="1.3"/><circle class="tw c" cx="840" cy="82"  r="1"/>
      <circle class="tw"   cx="930" cy="42"  r="1.2"/><circle class="tw d" cx="60"  cy="226" r="1.4"/>
      <circle class="tw c" cx="300" cy="232" r="1"/>  <circle class="tw b" cx="960" cy="212" r="1.2"/>
      <circle class="tw d" cx="46"  cy="36"  r="1.1"/><circle class="tw" cx="268" cy="88" r="1"/>
    </g>

    <g class="float">
      <circle cx="{cx}" cy="{cy}" r="{r + 46}" fill="url(#glow)" class="breathe"/>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="#12122a"/>
      <g {flip}>
        <path d="{path}" fill="url(#lit)"/>
        <g clip-path="url(#disc)" fill="#c3b49a" opacity=".42">
          <circle cx="{cx - 26}" cy="{cy - 30}" r="16"/>
          <circle cx="{cx + 30}" cy="{cy + 22}" r="12"/>
          <circle cx="{cx - 12}" cy="{cy + 40}" r="8"/>
          <circle cx="{cx + 40}" cy="{cy - 34}" r="7"/>
          <circle cx="{cx - 52}" cy="{cy + 8}"  r="5"/>
        </g>
      </g>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#8fd8ff" stroke-opacity=".28"/>
    </g>

    <g font-family="Segoe UI, Helvetica Neue, Arial, sans-serif">
      <text x="288" y="62" font-size="11" letter-spacing="3.2" fill="#8fd8ff">{date_label}</text>
      <text x="288" y="106" font-size="31" font-weight="700" fill="#ffffff">{name}</text>

      <g font-size="12.5" font-family="SFMono-Regular, Consolas, Menlo, monospace">
        <rect x="288" y="128" width="132" height="28" rx="14" fill="#ffffff" fill-opacity=".05" stroke="#ffd97a" stroke-opacity=".30"/>
        <text x="304" y="147" fill="#ffd97a">ILLUM · {illum * 100:.0f}%</text>
        <rect x="430" y="128" width="152" height="28" rx="14" fill="#ffffff" fill-opacity=".05" stroke="#b39bff" stroke-opacity=".30"/>
        <text x="446" y="147" fill="#c3b0ff">AGE · {age:.1f} DAYS</text>
      </g>

      <g font-size="12" font-family="SFMono-Regular, Consolas, Menlo, monospace" fill="#8f89b8">
        <circle cx="294" cy="180" r="3.5" fill="#ffd97a"/>
        <text x="306" y="184">NEXT FULL MOON IN {d_full} DAYS</text>
        <circle cx="294" cy="206" r="3.5" fill="#8fd8ff"/>
        <text x="306" y="210">NEXT NEW MOON IN {d_new} DAYS</text>
      </g>

      <text x="288" y="236" font-size="10.5" letter-spacing="2" fill="#5f5b85">SEEN FROM THE SOUTHERN SKY · BRAZIL</text>

      <text x="648" y="62" font-size="11" letter-spacing="3.2" fill="#8fd8ff">LUNAR CYCLE</text>
      <text x="648" y="92" font-size="12" fill="#6f6a96" font-family="SFMono-Regular, Consolas, Menlo, monospace">day {age:.1f} of {SYNODIC:.1f}</text>

      <rect x="648" y="118" width="306" height="4" rx="2" fill="url(#track)"/>
      <rect x="648" y="118" width="{frac * 306:.1f}" height="4" rx="2" fill="#ffd97a" fill-opacity=".75"/>
      <circle cx="{marker_x:.1f}" cy="120" r="4" fill="#ffd97a"/>
      <circle cx="{marker_x:.1f}" cy="120" r="4" fill="#ffd97a" class="ping"/>
      {strip}
    </g>
  </g>
</svg>
"""


if __name__ == "__main__":
    out = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "moon-phase.svg",
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_svg(datetime.now(timezone.utc)))
    print(f"wrote {out}")
