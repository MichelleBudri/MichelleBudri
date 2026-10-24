#!/usr/bin/env python3
"""The Moon's real phase for today, drawn for the mission-control panel
(see mission_control.py). No dependencies, no external APIs.

The Moon is drawn as seen from the SOUTHERN hemisphere (Brazil).
Set HEMISPHERE = "north" to flip it.
"""

import math
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


def days(n: int) -> str:
    return "today" if n == 0 else f"in {n} day" if n == 1 else f"in {n} days"


def moon_panel(now: datetime):
    """(defs, body) SVG fragments for the moon quadrant, in a local 500x330 frame."""
    age, frac, illum, name = phase_data(now)
    cx, cy, r = 104, 116, 64
    path = lit_path(cx, cy, r, frac, illum)
    flip = f'transform="translate({2 * cx},0) scale(-1,1)"' if HEMISPHERE == "south" else ""

    local = now.astimezone(BRT)
    date_label = local.strftime("%A, %d %B").replace(" 0", " ")

    full = next_event(now, 0.5)
    new = next_event(now, 0.0)
    d_full = max(0, round((full - now).total_seconds() / 86400))
    d_new = max(0, round((new - now).total_seconds() / 86400))

    tx, tw = 36, 428
    strip = "".join(
        mini_moon(tx + 14 + i * (tw - 28) / 7, 266, 12, i / 8.0, round(frac * 8) % 8 == i)
        for i in range(8)
    )
    marker_x = tx + frac * tw

    defs = f"""
    <radialGradient id="glow" cx="50%" cy="50%">
      <stop offset="0%" stop-color="#fff6d8" stop-opacity="0.34"/>
      <stop offset="100%" stop-color="#fff6d8" stop-opacity="0"/>
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
    <clipPath id="disc"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>"""

    body = f"""
      <g class="float">
        <circle cx="{cx}" cy="{cy}" r="{r + 34}" fill="url(#glow)" class="breathe"/>
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="#12122a"/>
        <g {flip}>
          <path d="{path}" fill="url(#lit)"/>
          <g clip-path="url(#disc)" fill="#c3b49a" opacity=".42">
            <circle cx="{cx - 18}" cy="{cy - 20}" r="11"/>
            <circle cx="{cx + 20}" cy="{cy + 15}" r="8"/>
            <circle cx="{cx - 8}" cy="{cy + 28}" r="5.5"/>
            <circle cx="{cx + 27}" cy="{cy - 24}" r="4.5"/>
            <circle cx="{cx - 36}" cy="{cy + 5}"  r="3.5"/>
          </g>
        </g>
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#8fd8ff" stroke-opacity=".28"/>
      </g>

      <text x="200" y="64" font-size="15" fill="#8fd8ff">{date_label}</text>
      <text x="200" y="96" font-size="25" font-weight="700" fill="#ffffff">{name}</text>
      <text x="200" y="124" font-size="15"><tspan fill="#ffd97a">{illum * 100:.0f}% lit</tspan><tspan fill="#6f6a96">, </tspan><tspan fill="#c3b0ff">{age:.1f} days old</tspan></text>
      <g font-size="15" fill="#a9a3cf">
        <circle cx="205" cy="153" r="3.5" fill="#ffd97a"/>
        <text x="218" y="158">Full moon {days(d_full)}</text>
        <circle cx="205" cy="179" r="3.5" fill="#8fd8ff"/>
        <text x="218" y="184">New moon {days(d_new)}</text>
      </g>

      <rect x="{tx}" y="220" width="{tw}" height="4" rx="2" fill="url(#track)"/>
      <rect x="{tx}" y="220" width="{frac * tw:.1f}" height="4" rx="2" fill="#ffd97a" fill-opacity=".75"/>
      <circle cx="{marker_x:.1f}" cy="222" r="4" fill="#ffd97a"/>
      <circle cx="{marker_x:.1f}" cy="222" r="4" fill="#ffd97a" class="ping"/>
      {strip}
      <text x="{tx}" y="310" font-size="13" fill="#5f5b85">Seen from the southern sky over Brazil</text>
      <text x="{tx + tw}" y="310" font-size="13" text-anchor="end" fill="#6f6a96">day {age:.1f} of {SYNODIC:.1f}</text>"""
    return defs, body, name
