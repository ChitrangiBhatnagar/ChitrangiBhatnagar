#!/usr/bin/env python3
"""Render animated SVG profile cards into cards/.

Brand tokens match chitrangi-ai-nexus (Space Grotesk + JetBrains Mono,
neural black + cyan). Set STATIC=1 (or --static) to freeze the final frame.
"""

from __future__ import annotations

import argparse
import base64
import html
import io
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
PORTRAIT_CANDIDATES = [
    ROOT / "assets" / "persona-photo.jpg",
    ROOT / "me.jpg",
]

# Website design tokens (chitrangi-ai-nexus)
BG = "#151413"
CARD = "#1A1D24"
PANEL = "#22262F"
TEXT = "#E6FFFF"
MUTED = "#9BA3AF"
BRAND = "#00BFFF"
BRAND_DIM = "#007A99"
BORDER = "#2C3340"
HEAT = ["#0D2A33", "#0A4A5C", "#067A96", "#00A0CC", "#00BFFF"]

FONT_DISPLAY = "Space Grotesk"
FONT_MONO = "JetBrains Mono"

FONT_SOURCES = {
    "SpaceGrotesk-Regular.ttf": "https://cdn.jsdelivr.net/fontsource/fonts/space-grotesk@5.2.8/latin-400-normal.ttf",
    "SpaceGrotesk-Medium.ttf": "https://cdn.jsdelivr.net/fontsource/fonts/space-grotesk@5.2.8/latin-500-normal.ttf",
    "SpaceGrotesk-Bold.ttf": "https://cdn.jsdelivr.net/fontsource/fonts/space-grotesk@5.2.8/latin-700-normal.ttf",
    "JetBrainsMono-Regular.ttf": "https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@v2.304/fonts/ttf/JetBrainsMono-Regular.ttf",
    "JetBrainsMono-Bold.ttf": "https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@v2.304/fonts/ttf/JetBrainsMono-Bold.ttf",
}

NAME = "Chitrangi Bhatnagar"
TAGLINE = "AI engineer building production LLM systems — RAG, orchestration, full-stack."
LOCATION = "Bengaluru · Open to internships & full-time roles"

TILES = [
    {
        "slug": "linkedin",
        "label": "LinkedIn",
        "sub": "connect / career",
        "href": "https://www.linkedin.com/in/chitrangi-bhatnagar-2a591b255",
        "glyph": "in",
    },
    {
        "slug": "portfolio",
        "label": "Portfolio",
        "sub": "chitrangi-ai-nexus",
        "href": "https://chitrangibhatnagar.github.io/chitrangi-ai-nexus/",
        "glyph": "◇",
    },
    {
        "slug": "email",
        "label": "Email",
        "sub": "say hello",
        "href": "mailto:chitrangibhatnagar@gmail.com",
        "glyph": "@",
    },
]

FEATURED_REPOS = [
    {
        "slug": "agentic-observability",
        "title": "Agentic Observability",
        "repo": "agentic-observability-platform",
        "blurb": "Multi-agent anomaly detection for cloud systems — RL + RAG threat mitigation.",
        "stack": "Python · LangChain · TensorFlow",
        "url": "https://github.com/ChitrangiBhatnagar/agentic-observability-platform",
    },
    {
        "slug": "research-oz",
        "title": "ResearchOZ",
        "repo": "ResearchOZ",
        "blurb": "Research workspace UI for structured exploration and desktop-first workflows.",
        "stack": "TypeScript · React · Vite",
        "url": "https://github.com/ChitrangiBhatnagar/ResearchOZ",
    },
    {
        "slug": "ai-nexus",
        "title": "chitrangi-ai-nexus",
        "repo": "chitrangi-ai-nexus",
        "blurb": "Personal portfolio with neural-theme motion, CI/CD, and GitHub Pages deploy.",
        "stack": "React 18 · TypeScript · Vite",
        "url": "https://github.com/ChitrangiBhatnagar/chitrangi-ai-nexus",
    },
]

# Stagger: page plays top → bottom (seconds)
DELAY = {
    "hero": 0.0,
    "tile0": 0.45,
    "tile1": 0.60,
    "tile2": 0.75,
    "chart": 1.05,
    "repo0": 1.55,
    "repo1": 1.85,
    "repo2": 2.15,
    "graph": 2.55,
}


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "profile-cards/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        dest.write_bytes(response.read())
    return dest


def _ensure_fonts() -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, url in FONT_SOURCES.items():
        paths[name] = _download(url, CACHE / name)
    return paths


def _subset_woff(ttf: Path, text: str, weight_hint: str) -> str:
    """Subset a TTF to the glyphs in `text` and return a CSS @font-face src data URI."""
    chars = "".join(sorted(set(text)))
    if not chars:
        chars = "A"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "subset.woff"
        unicodes = ",".join(f"U+{ord(ch):04X}" for ch in chars)
        cmd = [
            os.environ.get("PYTHON", sys.executable),
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
    family = FONT_DISPLAY if "SpaceGrotesk" in ttf.name else FONT_MONO
    weight = "700" if "Bold" in ttf.name else ("500" if "Medium" in ttf.name else "400")
    if weight_hint:
        weight = weight_hint
    return (
        f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;"
        f"src:url('data:font/woff;base64,{b64}') format('woff');}}"
    )


def _font_css(corpus: str) -> str:
    fonts = _ensure_fonts()
    faces = [
        _subset_woff(fonts["SpaceGrotesk-Regular.ttf"], corpus, "400"),
        _subset_woff(fonts["SpaceGrotesk-Medium.ttf"], corpus, "500"),
        _subset_woff(fonts["SpaceGrotesk-Bold.ttf"], corpus, "700"),
        _subset_woff(fonts["JetBrainsMono-Regular.ttf"], corpus, "400"),
        _subset_woff(fonts["JetBrainsMono-Bold.ttf"], corpus, "700"),
    ]
    return "\n".join(faces)


def _motion_css(static: bool) -> str:
    # Final frame is the default so GitHub/img still shows content if CSS
    # animations are skipped. Motion only runs under no-preference.
    base = ".in{opacity:1;transform:none}.bar{transform:none}.cell{opacity:1}"
    if static:
        return base
    return f"""
{base}
.pulse{{opacity:.75}}
@media (prefers-reduced-motion:no-preference){{
  .in{{opacity:0;transform:translateY(14px);animation:rise .7s cubic-bezier(.23,1,.32,1) forwards}}
  .bar{{transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.23,1,.32,1) forwards}}
  .cell{{opacity:0;animation:fade .45s ease forwards}}
  .pulse{{animation:pulse 2.4s ease-in-out infinite}}
}}
@keyframes rise{{to{{opacity:1;transform:translateY(0)}}}}
@keyframes grow{{to{{transform:scaleY(1)}}}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes pulse{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{
  .in,.bar,.cell,.pulse{{animation:none!important;opacity:1!important;transform:none!important}}
}}
""".strip()


def _style(corpus: str, static: bool, extra: str = "") -> str:
    return f"<style>\n{_font_css(corpus)}\n{_motion_css(static)}\n{extra}\n</style>"


def _delay_attr(seconds: float, static: bool) -> str:
    if static:
        return ""
    return f' style="animation-delay:{seconds:.2f}s"'


def _smil_opacity(begin: float, static: bool, dur: float = 0.6) -> str:
    if static:
        return ""
    return (
        f'<animate attributeName="opacity" from="0" to="1" dur="{dur}s" '
        f'begin="{begin:.2f}s" fill="freeze"/>'
    )


def _portrait_data_uri() -> str | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    source = next((p for p in PORTRAIT_CANDIDATES if p.exists()), None)
    if source is None:
        return None
    img = Image.open(source).convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = max(0, (w - side) // 2 - int(w * 0.04))
    top = max(0, (h - side) // 2 - int(h * 0.08))
    crop = img.crop((left, top, left + side, top + side)).resize((240, 240), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    crop.save(buf, format="JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def render_hero(static: bool) -> str:
    portrait = _portrait_data_uri()
    corpus = f"{NAME}{TAGLINE}{LOCATION}AI/ML Engineer"
    delay = DELAY["hero"]
    width, height = 880, 280

    portrait_block = ""
    text_x = 40
    if portrait:
        text_x = 300
        fade = _smil_opacity(delay, static)
        portrait_block = f"""
  <defs>
    <clipPath id="face"><circle cx="150" cy="140" r="96"/></clipPath>
  </defs>
  <circle cx="150" cy="140" r="100" fill="{PANEL}" stroke="{BRAND}" stroke-width="2"/>
  <image href="{portrait}" x="54" y="44" width="192" height="192" clip-path="url(#face)" preserveAspectRatio="xMidYMid slice"/>
  <circle cx="150" cy="140" r="100" fill="none" stroke="{BRAND}" stroke-width="2" opacity="0.9">{fade}</circle>
"""

    d_name = delay + 0.05
    d_line = delay + 0.18
    d_loc = delay + 0.32

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{_esc(NAME)}">
  {_style(corpus, static, f".t{{font-family:'{FONT_DISPLAY}',sans-serif}}.m{{font-family:'{FONT_MONO}',monospace}}")}
  <rect width="{width}" height="{height}" rx="18" fill="{BG}"/>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" fill="none" stroke="{BORDER}" stroke-width="1.5"/>
  <rect x="24" y="22" width="6" height="44" rx="3" fill="{BRAND}" class="pulse"/>
{portrait_block}
  <g class="in"{_delay_attr(d_name, static)}>
    <text x="{text_x}" y="108" fill="{TEXT}" font-size="36" font-weight="700" class="t" letter-spacing="-0.5">{_esc(NAME)}</text>
  </g>
  <g class="in"{_delay_attr(d_line, static)}>
    <text x="{text_x}" y="148" fill="{MUTED}" font-size="15" font-weight="400" class="t">{_esc(TAGLINE)}</text>
  </g>
  <g class="in"{_delay_attr(d_loc, static)}>
    <text x="{text_x}" y="188" fill="{BRAND}" font-size="13" font-weight="500" class="m">{_esc(LOCATION)}</text>
  </g>
</svg>
"""


def render_tile(tile: dict[str, str], index: int, static: bool) -> str:
    corpus = f"{tile['label']}{tile['sub']}{tile['glyph']}open"
    delay = DELAY[f"tile{index}"]
    width, height = 280, 120
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{_esc(tile['label'])}">
  {_style(corpus, static, f".t{{font-family:'{FONT_DISPLAY}',sans-serif}}.m{{font-family:'{FONT_MONO}',monospace}}")}
  <rect width="{width}" height="{height}" rx="16" fill="{CARD}"/>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="15" fill="none" stroke="{BORDER}" stroke-width="1.5"/>
  <g class="in"{_delay_attr(delay, static)}>
    <circle cx="44" cy="60" r="22" fill="{PANEL}" stroke="{BRAND}" stroke-width="1.5"/>
    <text x="44" y="66" text-anchor="middle" fill="{BRAND}" font-size="16" font-weight="700" class="m">{_esc(tile['glyph'])}</text>
    <text x="82" y="54" fill="{TEXT}" font-size="18" font-weight="700" class="t">{_esc(tile['label'])}</text>
    <text x="82" y="78" fill="{MUTED}" font-size="12" font-weight="400" class="m">{_esc(tile['sub'])}</text>
  </g>
</svg>
"""


def _month_totals(days: list[dict]) -> list[tuple[str, int]]:
    totals: Counter[str] = Counter()
    for day in days:
        key = str(day["date"])[:7]
        totals[key] += int(day["count"])
    items = sorted(totals.items())
    return items[-12:]


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
    corpus = (
        f"Contributions per month streak {streak} active days {active} "
        f"busiest {best_label} " + " ".join(m for m, _ in months) + "JanFebMarAprMayJunJulAugSepOctNovDec"
    )
    delay = DELAY["chart"]
    width, height = 880, 320
    chart_x, chart_y = 48, 92
    chart_w, chart_h = 784, 160
    max_count = max((c for _, c in months), default=1) or 1
    bar_gap = 10
    bar_w = (chart_w - bar_gap * (len(months) - 1)) / max(len(months), 1)

    bars = []
    labels = []
    for i, (month, count) in enumerate(months):
        x = chart_x + i * (bar_w + bar_gap)
        h = max(4, (count / max_count) * chart_h)
        y = chart_y + chart_h - h
        short = datetime.strptime(month + "-01", "%Y-%m-%d").strftime("%b")
        bar_delay = delay + 0.15 + i * 0.06
        bars.append(
            f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
            f'rx="6" fill="{BRAND}"{_delay_attr(bar_delay, static)}/>'
        )
        labels.append(
            f'<text x="{x + bar_w/2:.1f}" y="{chart_y + chart_h + 22}" text-anchor="middle" '
            f'fill="{MUTED}" font-size="11" class="m">{short}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Monthly contributions">
  {_style(corpus, static, f".t{{font-family:'{FONT_DISPLAY}',sans-serif}}.m{{font-family:'{FONT_MONO}',monospace}}")}
  <rect width="{width}" height="{height}" rx="18" fill="{BG}"/>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" fill="none" stroke="{BORDER}" stroke-width="1.5"/>
  <g class="in"{_delay_attr(delay, static)}>
    <text x="40" y="42" fill="{TEXT}" font-size="20" font-weight="700" class="t">Contributions / month</text>
    <text x="40" y="68" fill="{MUTED}" font-size="12" class="m">last {len(months)} months · brand cyan</text>
  </g>
  {''.join(bars)}
  {''.join(labels)}
  <g class="in"{_delay_attr(delay + 0.35, static)}>
    <text x="48" y="300" fill="{BRAND}" font-size="13" font-weight="700" class="m">streak {streak}d</text>
    <text x="200" y="300" fill="{TEXT}" font-size="13" class="m">active {active}d</text>
    <text x="380" y="300" fill="{MUTED}" font-size="13" class="m">busiest {_esc(best_label)}</text>
  </g>
</svg>
"""


def render_repo(repo: dict[str, str], index: int, static: bool) -> str:
    corpus = f"{repo['title']}{repo['blurb']}{repo['stack']}{repo['repo']}featured"
    delay = DELAY[f"repo{index}"]
    width, height = 880, 150
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{_esc(repo['title'])}">
  {_style(corpus, static, f".t{{font-family:'{FONT_DISPLAY}',sans-serif}}.m{{font-family:'{FONT_MONO}',monospace}}")}
  <rect width="{width}" height="{height}" rx="18" fill="{CARD}"/>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" fill="none" stroke="{BORDER}" stroke-width="1.5"/>
  <rect x="0" y="24" width="6" height="102" rx="3" fill="{BRAND}"/>
  <g class="in"{_delay_attr(delay, static)}>
    <text x="36" y="48" fill="{BRAND}" font-size="12" font-weight="500" class="m">featured / {_esc(repo['repo'])}</text>
    <text x="36" y="78" fill="{TEXT}" font-size="22" font-weight="700" class="t">{_esc(repo['title'])}</text>
    <text x="36" y="106" fill="{MUTED}" font-size="14" class="t">{_esc(repo['blurb'])}</text>
    <text x="36" y="130" fill="{BRAND_DIM}" font-size="12" class="m">{_esc(repo['stack'])}</text>
  </g>
</svg>
"""


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
        color = HEAT[level]
        cell_delay = delay + (week / max(week_count, 1)) * 1.2 + row * 0.01
        cells.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
            f'fill="{color}"{_delay_attr(cell_delay, static)}/>'
        )
        if date.month != last_month and row <= 1:
            month_labels.append(
                f'<text x="{x}" y="-8" fill="{MUTED}" font-size="10" class="m">{months[date.month - 1]}</text>'
            )
            last_month = date.month

    day_label_svg = "".join(
        f'<text x="-8" y="{row * step + 9}" fill="{MUTED}" font-size="10" text-anchor="end" class="m">{label}</text>'
        for row, label in day_labels.items()
    )

    legend_x = width - right - 18 * len(HEAT) - 72
    legend_y = height - 16
    legend_cells = "".join(
        f'<rect x="{36 + i * 16}" y="-10" width="11" height="11" rx="2" fill="{color}"/>'
        for i, color in enumerate(HEAT)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{stats.get('total', 0)} contributions">
  {_style(corpus, static, f".t{{font-family:'{FONT_DISPLAY}',sans-serif}}.m{{font-family:'{FONT_MONO}',monospace}}")}
  <rect width="{width}" height="{height}" rx="18" fill="{BG}"/>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" fill="none" stroke="{BORDER}" stroke-width="1.5"/>
  <g class="in"{_delay_attr(delay, static)}>
    <text x="{left}" y="28" fill="{TEXT}" font-size="16" font-weight="700" class="t">{stats.get('total', 0)} contributions</text>
    <text x="{left + 180}" y="28" fill="{MUTED}" font-size="12" class="m">streak {stats.get('current_streak', 0)} · longest {stats.get('longest_streak', 0)}</text>
  </g>
  <g transform="translate({left},{top})">
    {day_label_svg}
    {''.join(month_labels)}
    {''.join(cells)}
  </g>
  <g transform="translate({left},{legend_y})" class="in"{_delay_attr(delay + 1.0, static)}>
    <text x="0" y="0" fill="{MUTED}" font-size="11" class="m">brand heatmap</text>
  </g>
  <g transform="translate({legend_x},{legend_y})" class="in"{_delay_attr(delay + 1.05, static)}>
    <text x="0" y="0" fill="{MUTED}" font-size="11" class="m">Less</text>
    {legend_cells}
    <text x="{36 + len(HEAT) * 16 + 4}" y="0" fill="{MUTED}" font-size="11" class="m">More</text>
  </g>
</svg>
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Collapse excess blank lines inside style for smaller files
    cleaned = re.sub(r"\n{3,}", "\n\n", content.strip()) + "\n"
    path.write_text(cleaned, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


def render_all(static: bool, data_path: Path) -> None:
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    CARDS.mkdir(parents=True, exist_ok=True)

    _write(CARDS / "hero.svg", render_hero(static))
    for i, tile in enumerate(TILES):
        _write(CARDS / f"tile-{tile['slug']}.svg", render_tile(tile, i, static))
    _write(CARDS / "chart.svg", render_chart(payload, static))
    for i, repo in enumerate(FEATURED_REPOS):
        _write(CARDS / f"repo-{repo['slug']}.svg", render_repo(repo, i, static))
    _write(CARDS / "graph.svg", render_graph(payload, static))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render animated SVG profile cards.")
    parser.add_argument("--input", type=Path, default=DATA, help="contributions JSON")
    parser.add_argument("--static", action="store_true", help="Freeze final frame (or STATIC=1)")
    args = parser.parse_args()
    static = args.static or os.environ.get("STATIC") == "1"
    if not args.input.exists():
        raise SystemExit(f"Missing {args.input} — run scripts/fetch_contributions.py first")
    render_all(static=static, data_path=args.input)
    print(f"done (static={static})")


if __name__ == "__main__":
    main()
