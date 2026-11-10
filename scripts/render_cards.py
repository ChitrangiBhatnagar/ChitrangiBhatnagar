#!/usr/bin/env python3
"""Render animated SVG profile cards into cards/.

Palette (user board):
  Chinese Black #0C1519 · Dark Jungle Green #162127 · Jet #3A3534
  Coffee #724B39 · Antique Brass #CF9D7B

Motion: one shared keyframe set; page plays hero → graph → bars → tiles → repos.
Set STATIC=1 (or --static) to freeze the final frame for screenshots.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
DATA = ROOT / "data" / "contributions.json"
CACHE = ROOT / ".cache" / "fonts"

# —— palette ——
BG = "#0C1519"          # Chinese Black
CARD = "#162127"        # Dark Jungle Green
JET = "#3A3534"         # Jet
COFFEE = "#724B39"      # Coffee
BRASS = "#CF9D7B"       # Antique Brass
TEXT = "#F2E6DA"
MUTED = "#A89080"
HEAT = ["#162127", "#3A3534", "#724B39", "#A87A5C", "#CF9D7B"]

FONT_DISPLAY = "Cormorant Garamond"
FONT_UI = "Space Grotesk"
FONT_MONO = "JetBrains Mono"

FONT_SOURCES = {
    "Cormorant-Regular.ttf": "https://cdn.jsdelivr.net/fontsource/fonts/cormorant-garamond@5.2.8/latin-400-normal.ttf",
    "Cormorant-Medium.ttf": "https://cdn.jsdelivr.net/fontsource/fonts/cormorant-garamond@5.2.8/latin-500-normal.ttf",
    "Cormorant-Bold.ttf": "https://cdn.jsdelivr.net/fontsource/fonts/cormorant-garamond@5.2.8/latin-700-normal.ttf",
    "SpaceGrotesk-Regular.ttf": "https://cdn.jsdelivr.net/fontsource/fonts/space-grotesk@5.2.8/latin-400-normal.ttf",
    "SpaceGrotesk-Medium.ttf": "https://cdn.jsdelivr.net/fontsource/fonts/space-grotesk@5.2.8/latin-500-normal.ttf",
    "SpaceGrotesk-Bold.ttf": "https://cdn.jsdelivr.net/fontsource/fonts/space-grotesk@5.2.8/latin-700-normal.ttf",
    "JetBrainsMono-Regular.ttf": "https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@v2.304/fonts/ttf/JetBrainsMono-Regular.ttf",
    "JetBrainsMono-Bold.ttf": "https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@v2.304/fonts/ttf/JetBrainsMono-Bold.ttf",
}

NAME_LINES = ["Chitrangi", "Bhatnagar"]
TAGLINE = "AI/ML engineer · RAG · orchestration · full-stack"
STATUS = "Tech Intern at TON Technology Services"

# Page timing: hero → graph → bars → tiles → repos
DELAY = {
    "hero": 0.0,
    "graph": 0.85,
    "chart": 2.15,
    "tile0": 3.35,
    "tile1": 3.55,
    "tile2": 3.75,
    "repo0": 4.55,
    "repo1": 4.80,
    "repo2": 5.05,
}

FEATURED_REPOS = [
    {
        "slug": "agentic-observability",
        "title": "Agentic Observability",
        "repo": "agentic-observability-platform",
        "blurb": "Multi-agent anomaly detection — RL + RAG for cloud threat mitigation.",
        "stack": "Python · LangChain · TensorFlow",
        "url": "https://github.com/ChitrangiBhatnagar/agentic-observability-platform",
        "size": "wide",   # bento: 64%
    },
    {
        "slug": "research-oz",
        "title": "ResearchOZ",
        "repo": "ResearchOZ",
        "blurb": "Research workspace for structured exploration.",
        "stack": "TypeScript · React",
        "url": "https://github.com/ChitrangiBhatnagar/ResearchOZ",
        "size": "tall",   # bento: 34%
    },
]


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "profile-cards/2.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        dest.write_bytes(response.read())
    return dest


def _ensure_fonts() -> dict[str, Path]:
    return {name: _download(url, CACHE / name) for name, url in FONT_SOURCES.items()}


def _subset_woff(ttf: Path, text: str, family: str, weight: str) -> str:
    chars = "".join(sorted(set(text))) or "A"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "subset.woff"
        unicodes = ",".join(f"U+{ord(ch):04X}" for ch in chars)
        cmd = [
            sys.executable,
            "-m",
            "fontTools.subset",
            str(ttf),
            f"--unicodes={unicodes}",
            "--flavor=woff",
            f"--output-file={out}",
            "--ignore-missing-glyphs",
            "--no-hinting",
            "--desubroutinize",
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        b64 = base64.b64encode(out.read_bytes()).decode("ascii")
    return (
        f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;"
        f"src:url('data:font/woff;base64,{b64}') format('woff');}}"
    )


def _font_css(corpus: str) -> str:
    fonts = _ensure_fonts()
    return "\n".join(
        [
            _subset_woff(fonts["Cormorant-Regular.ttf"], corpus, FONT_DISPLAY, "400"),
            _subset_woff(fonts["Cormorant-Medium.ttf"], corpus, FONT_DISPLAY, "500"),
            _subset_woff(fonts["Cormorant-Bold.ttf"], corpus, FONT_DISPLAY, "700"),
            _subset_woff(fonts["SpaceGrotesk-Regular.ttf"], corpus, FONT_UI, "400"),
            _subset_woff(fonts["SpaceGrotesk-Medium.ttf"], corpus, FONT_UI, "500"),
            _subset_woff(fonts["SpaceGrotesk-Bold.ttf"], corpus, FONT_UI, "700"),
            _subset_woff(fonts["JetBrainsMono-Regular.ttf"], corpus, FONT_MONO, "400"),
            _subset_woff(fonts["JetBrainsMono-Bold.ttf"], corpus, FONT_MONO, "700"),
        ]
    )


def _shared_keyframes() -> str:
    """One small shared set used by every card."""
    return """
@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes pop{0%{opacity:0;transform:translateY(8px) scale(.86)}70%{opacity:1;transform:translateY(-2px) scale(1.06)}100%{opacity:1;transform:translateY(0) scale(1)}}
@keyframes swing{0%{opacity:0;transform:translateY(48px) rotate(-7deg) scale(.92)}62%{opacity:1;transform:translateY(-6px) rotate(1.5deg) scale(1.03)}82%{transform:translateY(2px) rotate(-.4deg) scale(.995)}100%{opacity:1;transform:translateY(0) rotate(0) scale(1)}}
@keyframes nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(4px)}}
@keyframes pulse{0%,100%{opacity:.4;transform:scale(1)}50%{opacity:1;transform:scale(1.35)}}
""".strip()


def _motion_css(static: bool) -> str:
    base = (
        ".rise,.grow,.fade,.pop,.swing{opacity:1;transform:none}"
        ".bar{transform:none}"
        ".cell{opacity:1}"
        ".nudge,.pulse{animation:none}"
    )
    if static:
        return base
    return f"""
{base}
{_shared_keyframes()}
@media (prefers-reduced-motion:no-preference){{
  .rise{{opacity:0;transform:translateY(18px);animation:rise .75s cubic-bezier(.23,1,.32,1) forwards}}
  .grow{{transform-origin:bottom;transform-box:fill-box;transform:scaleY(0);animation:grow .85s cubic-bezier(.23,1,.32,1) forwards}}
  .bar{{transform-origin:bottom;transform-box:fill-box;transform:scaleY(0);animation:grow .85s cubic-bezier(.23,1,.32,1) forwards}}
  .fade{{opacity:0;animation:fade .4s ease forwards}}
  .cell{{opacity:0;animation:fade .35s ease forwards}}
  .pop{{opacity:0;animation:pop .55s cubic-bezier(.34,1.56,.64,1) forwards}}
  .swing{{opacity:0;transform:translateY(48px) rotate(-7deg);animation:swing .95s cubic-bezier(.22,1.2,.36,1) forwards}}
  .nudge{{animation:nudge 2.2s ease-in-out infinite}}
  .pulse{{animation:pulse 1.8s ease-in-out infinite}}
}}
@media (prefers-reduced-motion:reduce){{
  .rise,.grow,.fade,.pop,.swing,.bar,.cell,.nudge,.pulse{{animation:none!important;opacity:1!important;transform:none!important}}
}}
""".strip()


def _style(corpus: str, static: bool, extra: str = "") -> str:
    return (
        f"<style>\n{_font_css(corpus)}\n{_motion_css(static)}\n"
        f".serif{{font-family:'{FONT_DISPLAY}',serif}}"
        f".ui{{font-family:'{FONT_UI}',sans-serif}}"
        f".mono{{font-family:'{FONT_MONO}',monospace}}\n{extra}\n</style>"
    )


def _delay(seconds: float, static: bool) -> str:
    if static:
        return ""
    return f' style="animation-delay:{seconds:.2f}s"'


def _card_shell(width: int, height: int, fill: str = CARD) -> str:
    return (
        f'<rect width="{width}" height="{height}" rx="20" fill="{BG}"/>'
        f'<rect x="1.5" y="1.5" width="{width-3}" height="{height-3}" rx="18.5" '
        f'fill="{fill}" stroke="{JET}" stroke-width="1.25"/>'
    )


# ── hero ─────────────────────────────────────────────────────────────────────

def render_hero(static: bool) -> str:
    corpus = "".join(NAME_LINES) + TAGLINE + STATUS + "AI ML engineer"
    delay = DELAY["hero"]
    w, h = 880, 260

    # Name lines rise one at a time
    name_svg = []
    y = 92
    for i, line in enumerate(NAME_LINES):
        d = delay + i * 0.22
        name_svg.append(
            f'<text class="rise serif" x="48" y="{y}" fill="{TEXT}" font-size="54" '
            f'font-weight="700" letter-spacing="-0.5"{_delay(d, static)}>{_esc(line)}</text>'
        )
        y += 58

    # Shine: SMIL-animated gradientTransform across the name (CSS bg-clip:text can't do SVG text)
    shine = ""
    if not static:
        shine = f"""
  <defs>
    <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="220" y2="0">
      <stop offset="0%" stop-color="{TEXT}" stop-opacity="0"/>
      <stop offset="45%" stop-color="{BRASS}" stop-opacity=".95"/>
      <stop offset="55%" stop-color="{TEXT}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{TEXT}" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate"
        from="-260 0" to="920 0" dur="3.6s" begin="1.2s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>
  <text class="serif" x="48" y="92" fill="url(#shine)" font-size="54" font-weight="700" letter-spacing="-0.5" opacity=".9">{_esc(NAME_LINES[0])}</text>
  <text class="serif" x="48" y="150" fill="url(#shine)" font-size="54" font-weight="700" letter-spacing="-0.5" opacity=".9">{_esc(NAME_LINES[1])}</text>
"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{_esc(' '.join(NAME_LINES))}">
  {_style(corpus, static)}
  {_card_shell(w, h, BG)}
  <rect x="48" y="36" width="36" height="3" rx="1.5" fill="{BRASS}" class="rise"{_delay(delay, static)}/>
  {''.join(name_svg)}
{shine}
  <g class="rise"{_delay(delay + 0.5, static)}>
    <text x="48" y="196" fill="{MUTED}" font-size="15" class="ui">{_esc(TAGLINE)}</text>
    <circle class="pulse" cx="54" cy="222" r="4" fill="{BRASS}"/>
    <text x="68" y="226" fill="{BRASS}" font-size="13" class="mono">{_esc(STATUS)}</text>
  </g>
</svg>
"""


# ── contribution graph ───────────────────────────────────────────────────────

def render_graph(payload: dict, static: bool) -> str:
    days = sorted(payload["days"], key=lambda d: str(d["date"]))
    stats = payload["stats"]
    if not days:
        raise RuntimeError("No contribution days")

    first = datetime.strptime(str(days[0]["date"]), "%Y-%m-%d")
    sunday_offset = (first.weekday() + 1) % 7
    week_count = ((sunday_offset + len(days) - 1) // 7) + 1

    cell, gap = 11, 3
    step = cell + gap
    left, top, right, bottom = 40, 56, 20, 40
    width = left + week_count * step + right
    height = top + 7 * step + bottom
    delay = DELAY["graph"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}

    corpus = (
        f"contribution graph {stats.get('total', 0)} streak {stats.get('current_streak', 0)} "
        f"longest {stats.get('longest_streak', 0)} Less More " + " ".join(months) + "Mon Wed Fri"
    )

    cells = []
    month_labels = []
    last_month = None
    for index, day in enumerate(days):
        date = datetime.strptime(str(day["date"]), "%Y-%m-%d")
        week = (sunday_offset + index) // 7
        row = (sunday_offset + index) % 7
        x = week * step
        y = row * step
        level = max(0, min(int(day.get("level", 0)), len(HEAT) - 1))
        # Sweep left → right
        cell_delay = delay + 0.15 + (week / max(week_count, 1)) * 1.35 + row * 0.008
        cells.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
            f'fill="{HEAT[level]}"{_delay(cell_delay, static)}/>'
        )
        if date.month != last_month and row <= 1:
            month_labels.append(
                f'<text x="{x}" y="-8" fill="{MUTED}" font-size="10" class="mono">{months[date.month - 1]}</text>'
            )
            last_month = date.month

    day_label_svg = "".join(
        f'<text x="-8" y="{row * step + 9}" fill="{MUTED}" font-size="10" text-anchor="end" class="mono">{label}</text>'
        for row, label in day_labels.items()
    )
    legend_x = width - right - 18 * len(HEAT) - 72
    legend_cells = "".join(
        f'<rect x="{36 + i * 16}" y="-10" width="11" height="11" rx="2" fill="{c}"/>'
        for i, c in enumerate(HEAT)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{stats.get('total', 0)} contributions">
  {_style(corpus, static)}
  {_card_shell(width, height, BG)}
  <g class="rise"{_delay(delay, static)}>
    <text x="{left}" y="30" fill="{TEXT}" font-size="18" font-weight="600" class="ui">{stats.get('total', 0)} contributions</text>
    <text x="{left + 190}" y="30" fill="{MUTED}" font-size="12" class="mono">streak {stats.get('current_streak', 0)} · longest {stats.get('longest_streak', 0)}</text>
  </g>
  <g transform="translate({left},{top})">
    {day_label_svg}{''.join(month_labels)}{''.join(cells)}
  </g>
  <g transform="translate({legend_x},{height - 16})" class="rise"{_delay(delay + 1.4, static)}>
    <text x="0" y="0" fill="{MUTED}" font-size="11" class="mono">Less</text>
    {legend_cells}
    <text x="{36 + len(HEAT) * 16 + 4}" y="0" fill="{MUTED}" font-size="11" class="mono">More</text>
  </g>
</svg>
"""


# ── monthly bars ─────────────────────────────────────────────────────────────

def _month_totals(days: list[dict]) -> list[tuple[str, int]]:
    totals: Counter[str] = Counter()
    for day in days:
        totals[str(day["date"])[:7]] += int(day["count"])
    return sorted(totals.items())[-12:]


def _active_days(days: list[dict]) -> int:
    return sum(1 for day in days if int(day["count"]) > 0)


def render_chart(payload: dict, static: bool) -> str:
    days = payload["days"]
    stats = payload["stats"]
    months = _month_totals(days)
    active = _active_days(days)
    streak = int(stats.get("current_streak", 0))
    best = stats.get("best_day", {})
    best_label = f"{best.get('date', '—')} · {best.get('count', 0)}"
    delay = DELAY["chart"]
    w, h = 880, 340
    chart_x, chart_y, chart_w, chart_h = 48, 100, 784, 168
    max_count = max((c for _, c in months), default=1) or 1
    best_month_i = max(range(len(months)), key=lambda i: months[i][1]) if months else 0
    bar_gap = 10
    bar_w = (chart_w - bar_gap * max(len(months) - 1, 0)) / max(len(months), 1)

    corpus = (
        f"Contributions per month streak {streak} active {active} busiest {best_label} "
        + " ".join(f"{m}{c}" for m, c in months)
        + "JanFebMarAprMayJunJulAugSepOctNovDec0123456789"
    )

    bars, labels, pop = [], [], ""
    for i, (month, count) in enumerate(months):
        x = chart_x + i * (bar_w + bar_gap)
        bh = max(6, (count / max_count) * chart_h)
        y = chart_y + chart_h - bh
        short = datetime.strptime(month + "-01", "%Y-%m-%d").strftime("%b")
        bar_delay = delay + 0.2 + i * 0.07
        fill = BRASS if i == best_month_i else COFFEE
        bars.append(
            f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
            f'rx="7" fill="{fill}"{_delay(bar_delay, static)}/>'
        )
        labels.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{chart_y + chart_h + 22}" text-anchor="middle" '
            f'fill="{MUTED}" font-size="11" class="mono">{short}</text>'
        )
        if i == best_month_i:
            pop = (
                f'<text class="pop mono" x="{x + bar_w / 2:.1f}" y="{y - 10:.1f}" '
                f'text-anchor="middle" fill="{BRASS}" font-size="14" font-weight="700"'
                f'{_delay(bar_delay + 0.55, static)}>{count}</text>'
            )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Monthly contributions">
  {_style(corpus, static)}
  {_card_shell(w, h, BG)}
  <g class="rise"{_delay(delay, static)}>
    <text x="48" y="42" fill="{TEXT}" font-size="22" font-weight="600" class="ui">Contributions / month</text>
    <text x="48" y="68" fill="{MUTED}" font-size="12" class="mono">last {len(months)} months · antique brass</text>
  </g>
  {''.join(bars)}
  {pop}
  {''.join(labels)}
  <g class="rise"{_delay(delay + 0.9, static)}>
    <text x="48" y="318" fill="{BRASS}" font-size="13" font-weight="700" class="mono">streak {streak}d</text>
    <text x="200" y="318" fill="{TEXT}" font-size="13" class="mono">active {active}d</text>
    <text x="380" y="318" fill="{MUTED}" font-size="13" class="mono">busiest {_esc(best_label)}</text>
  </g>
</svg>
"""


# ── tiles (biggest entrance + count-up) ───────────────────────────────────────

def _count_up_frames(final: int, x: int, y: int, begin: float, static: bool) -> str:
    """18 SMIL frames — CSS can't change text content."""
    if static or final <= 0:
        return (
            f'<text x="{x}" y="{y}" fill="{BRASS}" font-size="42" font-weight="700" '
            f'class="serif">{final}</text>'
        )

    steps = 18
    frame_dur = 0.05
    values = [int(round(final * i / (steps - 1))) for i in range(steps)]
    # Collapse consecutive duplicates so we don't stack identical glyphs
    frames: list[tuple[int, int]] = []
    for val in values:
        if frames and frames[-1][0] == val:
            frames[-1] = (val, frames[-1][1] + 1)
        else:
            frames.append((val, 1))

    parts = []
    cursor = begin
    for i, (val, hold) in enumerate(frames):
        dur = frame_dur * hold
        is_last = i == len(frames) - 1
        fill = "freeze" if is_last else "remove"
        parts.append(
            f'<text x="{x}" y="{y}" fill="{BRASS}" font-size="42" font-weight="700" '
            f'class="serif" opacity="0">{val}'
            f'<set attributeName="opacity" to="1" begin="{cursor:.3f}s" dur="{dur:.3f}s" fill="{fill}"/>'
            f'</text>'
        )
        cursor += dur
    return "\n".join(parts)


def _tile_ring(cx: float, cy: float, begin: float, static: bool) -> str:
    """Corner pulse ring via SMIL — clipped, never overflows into neighbour tiles."""
    if static:
        return f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{BRASS}"/>'
    return f"""
    <circle cx="{cx}" cy="{cy}" r="3.5" fill="{BRASS}"/>
    <circle cx="{cx}" cy="{cy}" r="5" fill="none" stroke="{BRASS}" stroke-width="1.25" opacity="0">
      <animate attributeName="r" values="5;16" dur="2.2s" begin="{begin:.2f}s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.7;0" dur="2.2s" begin="{begin:.2f}s" repeatCount="indefinite"/>
    </circle>
"""


def render_tile(
    slug: str,
    label: str,
    sub: str,
    number: int,
    href_hint: str,
    index: int,
    static: bool,
) -> str:
    corpus = f"{label}{sub}{number}0123456789→{href_hint}"
    delay = DELAY[f"tile{index}"]
    w, h = 280, 168
    cx, cy = w - 28, 28

    count = _count_up_frames(number, 28, 78, delay + 0.35, static)
    ring = _tile_ring(cx, cy, delay + 0.9, static)

    shine_defs = ""
    shine_rect = ""
    if not static:
        shine_defs = f"""
    <linearGradient id="tileShine{index}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="120" y2="0">
      <stop offset="0%" stop-color="{BRASS}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{BRASS}" stop-opacity=".28"/>
      <stop offset="100%" stop-color="{BRASS}" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate"
        from="-140 0" to="320 0" dur="4s" begin="{delay + 1.4:.2f}s" repeatCount="indefinite"/>
    </linearGradient>
"""
        shine_rect = (
            f'<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="18" '
            f'fill="url(#tileShine{index})" pointer-events="none"/>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{_esc(label)} {number}">
  {_style(corpus, static)}
  <defs>
    <clipPath id="tileClip{index}"><rect width="{w}" height="{h}" rx="20"/></clipPath>
    {shine_defs}
  </defs>
  <g class="swing" clip-path="url(#tileClip{index})"{_delay(delay, static)}>
    {_card_shell(w, h, CARD)}
    {shine_rect}
    {ring}
    {count}
    <text x="28" y="108" fill="{TEXT}" font-size="16" font-weight="600" class="ui">{_esc(label)}</text>
    <text x="28" y="132" fill="{MUTED}" font-size="12" class="mono">{_esc(sub)}</text>
    <g class="nudge"{_delay(delay + 1.0, static)}>
      <path d="M{w-48} {h-36}h18m0 0l-5-5m5 5l-5 5" fill="none" stroke="{BRASS}" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
    </g>
  </g>
</svg>
"""


# ── featured repos (bento sizes) ─────────────────────────────────────────────

def render_repo(repo: dict, index: int, static: bool) -> str:
    size = repo.get("size", "full")
    if size == "wide":
        w, h = 560, 200
    elif size == "tall":
        w, h = 300, 200
    else:
        w, h = 880, 150

    corpus = f"{repo['title']}{repo['blurb']}{repo['stack']}{repo['repo']}featured→"
    delay = DELAY[f"repo{index}"]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{_esc(repo['title'])}">
  {_style(corpus, static)}
  <g class="rise"{_delay(delay, static)}>
    {_card_shell(w, h, CARD)}
    <rect x="0" y="28" width="5" height="{h - 56}" rx="2.5" fill="{BRASS}"/>
    <text x="28" y="48" fill="{COFFEE}" font-size="11" font-weight="500" class="mono">featured / {_esc(repo['repo'])}</text>
    <text x="28" y="82" fill="{TEXT}" font-size="{'22' if size != 'tall' else '18'}" font-weight="700" class="serif">{_esc(repo['title'])}</text>
    <text x="28" y="112" fill="{MUTED}" font-size="13" class="ui">{_esc(repo['blurb'])}</text>
    <text x="28" y="{h - 28}" fill="{BRASS}" font-size="12" class="mono">{_esc(repo['stack'])}</text>
    <g class="nudge"{_delay(delay + 0.4, static)}>
      <path d="M{w-40} {h-36}h16m0 0l-4-4m4 4l-4 4" fill="none" stroke="{BRASS}" stroke-width="1.5" stroke-linecap="round"/>
    </g>
  </g>
</svg>
"""


# ── orchestration ────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = re.sub(r"\n{3,}", "\n\n", content.strip()) + "\n"
    path.write_text(cleaned, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


def render_all(static: bool, data_path: Path) -> None:
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    stats = payload["stats"]
    days = payload["days"]
    CARDS.mkdir(parents=True, exist_ok=True)

    _write(CARDS / "hero.svg", render_hero(static))
    _write(CARDS / "graph.svg", render_graph(payload, static))
    _write(CARDS / "chart.svg", render_chart(payload, static))

    tiles = [
        ("streak", "Streak", "current day streak", int(stats.get("current_streak", 0)), "github"),
        ("contribs", "Contributions", "last 12 months", int(stats.get("total", 0)), "portfolio"),
        ("active", "Active days", "days with commits", _active_days(days), "linkedin"),
    ]
    for i, (slug, label, sub, number, hint) in enumerate(tiles):
        _write(CARDS / f"tile-{slug}.svg", render_tile(slug, label, sub, number, hint, i, static))

    for i, repo in enumerate(FEATURED_REPOS):
        _write(CARDS / f"repo-{repo['slug']}.svg", render_repo(repo, i, static))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render animated SVG profile cards.")
    parser.add_argument("--input", type=Path, default=DATA)
    parser.add_argument("--static", action="store_true")
    args = parser.parse_args()
    static = args.static or os.environ.get("STATIC") == "1"
    if not args.input.exists():
        raise SystemExit(f"Missing {args.input} — run scripts/fetch_contributions.py first")
    render_all(static=static, data_path=args.input)
    print(f"done (static={static})")


if __name__ == "__main__":
    main()
