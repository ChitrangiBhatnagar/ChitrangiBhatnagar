from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "me.jpg"
OUT_SVG = ROOT / "assets" / "persona-card.svg"
OUT_PHOTO = ROOT / "assets" / "persona-photo.jpg"


def crop_portrait(src: Image.Image, size: int = 280) -> Image.Image:
    w, h = src.size
    # Prefer a tall portrait crop around the subject (center-left bias for this photo).
    target_w = int(min(w, h) * 0.72)
    target_h = int(target_w * 1.2)
    target_w = min(target_w, w)
    target_h = min(target_h, h)

    left = max(0, (w - target_w) // 2 - int(w * 0.04))
    top = max(0, (h - target_h) // 2 - int(h * 0.08))
    right = min(w, left + target_w)
    bottom = min(h, top + target_h)
    crop = src.crop((left, top, right, bottom))
    return crop.resize((size, int(size * 1.2)), Image.Resampling.LANCZOS)


def main() -> None:
    src = Image.open(SOURCE).convert("RGB")
    photo = crop_portrait(src, size=250)

    OUT_PHOTO.parent.mkdir(parents=True, exist_ok=True)
    photo.save(OUT_PHOTO, format="JPEG", quality=82, optimize=True)

    buf = io.BytesIO()
    photo.save(buf, format="JPEG", quality=82, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    href = f"data:image/jpeg;base64,{b64}"

    svg = f"""<svg width="980" height="460" viewBox="0 0 980 460" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <defs>
    <style>
      .bg {{ fill: #0D0A07; }}
      .border {{ stroke: #E8A33D; stroke-width: 2; fill: none; }}
      .terminal-header {{ fill: #15110D; }}
      .text-amber {{ fill: #E8A33D; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
      .text-light {{ fill: #F5EFE6; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
      .text-dim {{ fill: #A5927B; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
      .title {{ font-size: 24px; font-weight: 700; }}
      .subtitle {{ font-size: 14px; font-weight: 500; }}
      .body {{ font-size: 13px; font-weight: 400; }}
      .small {{ font-size: 11px; font-weight: 400; }}
      .bar-bg {{ fill: #0D0A07; }}
      .bar-fill {{ fill: #E8A33D; }}
    </style>
    <clipPath id="photoClip">
      <rect x="30" y="58" width="250" height="300" rx="12" />
    </clipPath>
  </defs>

  <rect class="bg" x="1" y="1" width="978" height="458" rx="8" />
  <rect class="border" x="1" y="1" width="978" height="458" rx="8" />

  <path class="terminal-header" d="M 1 9 Q 1 1 9 1 L 971 1 Q 979 1 979 9 L 979 35 L 1 35 Z" />
  <line x1="1" y1="35" x2="979" y2="35" stroke="#E8A33D" stroke-width="1" />
  <circle cx="20" cy="18" r="6" fill="#FF5F56" />
  <circle cx="40" cy="18" r="6" fill="#FFBD2E" />
  <circle cx="60" cy="18" r="6" fill="#27C93F" />
  <text x="490" y="23" class="text-amber body" text-anchor="middle">chitrangi@nexus: ~</text>

  <rect x="30" y="58" width="250" height="300" rx="12" fill="#15110D" />
  <image href="{href}" xlink:href="{href}" x="30" y="58" width="250" height="300" preserveAspectRatio="xMidYMid slice" clip-path="url(#photoClip)" />
  <rect x="30" y="58" width="250" height="300" rx="12" fill="none" stroke="#E8A33D" stroke-width="1.5" />
  <text x="155" y="380" class="text-dim small" text-anchor="middle">[AVATAR]</text>

  <g transform="translate(310, 78)">
    <text x="0" y="0" class="text-amber title">Chitrangi Bhatnagar</text>
    <text x="0" y="24" class="text-light subtitle">&gt; AI Engineer &amp; ML Practitioner</text>
    <text x="0" y="60" class="text-dim body">[LOC]</text>
    <text x="50" y="60" class="text-light body">Bengaluru, India</text>
    <text x="0" y="84" class="text-dim body">[EDU]</text>
    <text x="50" y="84" class="text-light body">B.Tech CS (AI &amp; ML) · Presidency University</text>
    <text x="0" y="108" class="text-dim body">[GPA]</text>
    <text x="50" y="108" class="text-amber" font-weight="700">8.54</text>
  </g>

  <g transform="translate(310, 210)">
    <text x="0" y="0" class="text-amber subtitle">[ System Stats ]</text>
    <text x="0" y="28" class="text-dim body">Experience:</text>
    <text x="95" y="28" class="text-light body">3 internships, 5+ AI systems</text>
    <text x="0" y="52" class="text-dim body">Domains:</text>
    <text x="95" y="52" class="text-light body">RAG · LLM orchestration · Full-Stack</text>
    <text x="0" y="76" class="text-dim body">Status:</text>
    <text x="95" y="76" class="text-light body">Open to Opportunities</text>
  </g>

  <g transform="translate(640, 78)">
    <text x="0" y="0" class="text-amber subtitle">[ Competencies ]</text>
    <g transform="translate(0, 24)">
      <text x="0" y="12" class="text-light body">Python / AI / ML</text>
      <rect x="150" y="3" width="160" height="10" rx="4" class="bar-bg" />
      <rect x="150" y="3" width="142" height="10" rx="4" class="bar-fill" />
    </g>
    <g transform="translate(0, 48)">
      <text x="0" y="12" class="text-light body">LangChain / RAG</text>
      <rect x="150" y="3" width="160" height="10" rx="4" class="bar-bg" />
      <rect x="150" y="3" width="124" height="10" rx="4" class="bar-fill" />
    </g>
    <g transform="translate(0, 72)">
      <text x="0" y="12" class="text-light body">React / Next.js</text>
      <rect x="150" y="3" width="160" height="10" rx="4" class="bar-bg" />
      <rect x="150" y="3" width="116" height="10" rx="4" class="bar-fill" />
    </g>
    <g transform="translate(0, 96)">
      <text x="0" y="12" class="text-light body">Backend (FastAPI)</text>
      <rect x="150" y="3" width="160" height="10" rx="4" class="bar-bg" />
      <rect x="150" y="3" width="134" height="10" rx="4" class="bar-fill" />
    </g>
    <g transform="translate(0, 120)">
      <text x="0" y="12" class="text-light body">Cloud / DevOps</text>
      <rect x="150" y="3" width="160" height="10" rx="4" class="bar-bg" />
      <rect x="150" y="3" width="108" height="10" rx="4" class="bar-fill" />
    </g>
  </g>

  <g transform="translate(640, 240)">
    <text x="0" y="0" class="text-amber subtitle">[ Achievements ]</text>
    <text x="0" y="28" class="text-dim body">[AWARD]</text>
    <text x="60" y="28" class="text-light body">Best Societal Project</text>
    <text x="0" y="52" class="text-dim body">[AWARD]</text>
    <text x="60" y="52" class="text-light body">Hackathon Finalist · Genesys 2025</text>
    <text x="0" y="76" class="text-dim body">[AWARD]</text>
    <text x="60" y="76" class="text-light body">1st Prize · Bengaluru Eco Summit</text>
  </g>

  <g transform="translate(30, 420)">
    <text x="0" y="0" class="text-amber body">&gt; executing current_focus.sh:</text>
    <text x="240" y="0" class="text-light body">model evaluation · feature engineering · deployment patterns</text>
  </g>
</svg>
"""
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT_PHOTO} ({OUT_PHOTO.stat().st_size} bytes)")
    print(f"wrote {OUT_SVG} ({OUT_SVG.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
