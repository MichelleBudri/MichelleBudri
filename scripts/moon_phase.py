#!/usr/bin/env python3
"""Generate assets/moon-phase.svg with the Moon's real phase for today.

No dependencies, no external APIs. Run it locally or let the daily
GitHub Action (.github/workflows/moon-phase.yml) keep it fresh.

The Moon is drawn as seen from the SOUTHERN hemisphere (Brazil).
Set HEMISPHERE = "north" to flip it.
"""

import math
import os
from datetime import datetime, timedelta, timezone

HEMISPHERE = "south"
SYNODIC = 29.530588853

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


def _julian_day(now: datetime) -> float:
    return now.timestamp() / 86400.0 + 2440587.5


def phase_data(now: datetime):
    """Meeus (Astronomical Algorithms, ch. 48) low-precision phase angle."""
    t = (_julian_day(now) - 2451545.0) / 36525.0
    rad = math.radians

    # mean elongation of the Moon
    d = 297.8501921 + 445267.1114034 * t - 0.0018819 * t**2
    # Sun's mean anomaly
    m = 357.5291092 + 35999.0502909 * t
    # Moon's mean anomaly
    mp = 134.9633964 + 477198.8675055 * t + 0.0087414 * t**2

    d, m, mp = d % 360, m % 360, mp % 360

    i = (180 - d
         - 6.289 * math.sin(rad(mp))
         + 2.100 * math.sin(rad(m))
         - 1.274 * math.sin(rad(2 * d - mp))
         - 0.658 * math.sin(rad(2 * d))
         - 0.214 * math.sin(rad(2 * mp))
         - 0.110 * math.sin(rad(d)))

    illum = (1 + math.cos(rad(i))) / 2          # illuminated fraction
    frac = (d % 360) / 360.0                    # 0 = new, .5 = full
    age = frac * SYNODIC
    name = next(n for limit, n in NAMES if frac < limit)
    return age, frac, illum, name


def lit_path(cx, cy, r, frac, illum):
    """SVG path of the illuminated area, northern-hemisphere orientation."""
    rx = abs(r * (2 * illum - 1))
    waxing = frac < 0.5

    if waxing:
        limb = 1                       # right limb lit
        term = 0 if illum < 0.5 else 1
    else:
        limb = 0                       # left limb lit
        term = 1 if illum < 0.5 else 0

    top, bottom = cy - r, cy + r
    return (
        f"M {cx} {top} "
        f"A {r} {r} 0 0 {limb} {cx} {bottom} "
        f"A {rx:.3f} {r} 0 0 {term} {cx} {top} Z"
    )


def build_svg(now: datetime) -> str:
    age, frac, illum, name = phase_data(now)
    cx, cy, r = 130, 130, 92
    path = lit_path(cx, cy, r, frac, illum)
    flip = f'transform="translate({2 * cx},0) scale(-1,1)"' if HEMISPHERE == "south" else ""
    local = now.astimezone(timezone(timedelta(hours=-3)))   # Brasília time
    date_label = local.strftime("%b %d, %Y").upper()

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 260" width="520" height="260" role="img" aria-label="Moon phase today: {name}, {illum * 100:.0f}% illuminated">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#05060f"/>
      <stop offset="100%" stop-color="#160e33"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%">
      <stop offset="0%" stop-color="#fff6d8" stop-opacity="0.40"/>
      <stop offset="100%" stop-color="#fff6d8" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="lit" cx="38%" cy="32%">
      <stop offset="0%" stop-color="#fffdf3"/>
      <stop offset="65%" stop-color="#f0e7d3"/>
      <stop offset="100%" stop-color="#cfc0a4"/>
    </radialGradient>
    <clipPath id="disc"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>
    <clipPath id="card"><rect width="520" height="260" rx="16"/></clipPath>
    <style>
      .tw {{ animation: tw 3s ease-in-out infinite }}
      .b {{ animation-delay: .8s }} .c {{ animation-delay: 1.6s }} .d {{ animation-delay: 2.3s }}
      @keyframes tw {{ 0%,100% {{ opacity:.2 }} 50% {{ opacity:1 }} }}
      .breathe {{ animation: breathe 6s ease-in-out infinite }}
      @keyframes breathe {{ 0%,100% {{ opacity:.5 }} 50% {{ opacity:1 }} }}
    </style>
  </defs>

  <g clip-path="url(#card)">
    <rect width="520" height="260" fill="url(#bg)"/>
    <g fill="#fff">
      <circle class="tw"   cx="292" cy="42"  r="1.4"/>
      <circle class="tw b" cx="346" cy="96"  r="1"/>
      <circle class="tw c" cx="404" cy="52"  r="1.6"/>
      <circle class="tw d" cx="462" cy="118" r="1.2"/>
      <circle class="tw b" cx="330" cy="196" r="1.3"/>
      <circle class="tw c" cx="486" cy="212" r="1"/>
      <circle class="tw"   cx="42"  cy="34"  r="1.2"/>
      <circle class="tw d" cx="28"  cy="216" r="1.4"/>
      <circle class="tw c" cx="232" cy="230" r="1"/>
    </g>

    <circle cx="{cx}" cy="{cy}" r="{r + 46}" fill="url(#glow)" class="breathe"/>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="#12122a"/>
    <g {flip}>
      <path d="{path}" fill="url(#lit)"/>
      <g clip-path="url(#disc)" fill="#c3b49a" opacity=".45">
        <circle cx="{cx - 26}" cy="{cy - 30}" r="16"/>
        <circle cx="{cx + 30}" cy="{cy + 22}" r="12"/>
        <circle cx="{cx - 12}" cy="{cy + 40}" r="8"/>
        <circle cx="{cx + 40}" cy="{cy - 34}" r="7"/>
        <circle cx="{cx - 52}" cy="{cy + 8}"  r="5"/>
      </g>
    </g>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#8fd8ff" stroke-opacity=".28"/>

    <g font-family="Segoe UI, Helvetica Neue, Arial, sans-serif">
      <text x="260" y="76"  font-size="11" letter-spacing="3.5" fill="#8fd8ff">{date_label}</text>
      <text x="260" y="112" font-size="25" font-weight="700" fill="#ffffff">{name}</text>
      <text x="260" y="148" font-size="14" fill="#c9c3e8">Illumination · {illum * 100:.0f}%</text>
      <text x="260" y="172" font-size="14" fill="#c9c3e8">Moon age · {age:.1f} days</text>
      <text x="260" y="204" font-size="11" letter-spacing="2" fill="#6f6a96">SEEN FROM THE SOUTHERN SKY</text>
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
