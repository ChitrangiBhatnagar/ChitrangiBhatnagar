from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

# Amber-on-dark to match the profile README
PALETTE = ["#241B10", "#4A3418", "#7A5220", "#C08A2E", "#E8A33D"]
BG = "#0D0A07"
TEXT = "#F5EFE6"
DIM = "#A5927B"
ACCENT = "#E8A33D"

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT = 36
TOP = 52
RIGHT = 18
BOTTOM = 44
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def _load_payload(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _palette_for_level(level: int) -> str:
    return PALETTE[max(0, min(level, len(PALETTE) - 1))]


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def build_svg(payload: dict[str, object]) -> str:
    raw_days = payload["days"]  # type: ignore[index]
    stats = payload["stats"]  # type: ignore[index]
    days = sorted(raw_days, key=lambda item: str(item["date"]))
    if not days:
        raise RuntimeError("No contribution days to render")

    first = _parse_date(str(days[0]["date"]))
    # GitHub columns start on Sunday.
    sunday_offset = (first.weekday() + 1) % 7
    week_count = ((sunday_offset + len(days) - 1) // 7) + 1

    width = LEFT + week_count * STEP + RIGHT
    height = TOP + 7 * STEP + BOTTOM

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
            "role": "img",
            "aria-label": f"{stats['total']} contributions in the last year",
        },
    )

    ET.SubElement(svg, "rect", {"width": str(width), "height": str(height), "rx": "12", "fill": BG})
    ET.SubElement(
        svg,
        "text",
        {
            "x": str(LEFT),
            "y": "22",
            "fill": ACCENT,
            "font-family": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "font-size": "13",
            "font-weight": "700",
        },
    ).text = "$ contributions --year"

    grid = ET.SubElement(svg, "g", {"transform": f"translate({LEFT},{TOP})"})

    for row, label in DAY_LABELS.items():
        ET.SubElement(
            grid,
            "text",
            {
                "x": "-8",
                "y": str(row * STEP + 9),
                "fill": DIM,
                "font-family": "ui-monospace, Menlo, Consolas, monospace",
                "font-size": "10",
                "text-anchor": "end",
            },
        ).text = label

    last_month = None
    for index, day in enumerate(days):
        date = _parse_date(str(day["date"]))
        week = (sunday_offset + index) // 7
        row = (sunday_offset + index) % 7
        x = week * STEP
        y = row * STEP

        month = date.month
        if month != last_month and row <= 1:
            ET.SubElement(
                grid,
                "text",
                {
                    "x": str(x),
                    "y": "-8",
                    "fill": DIM,
                    "font-family": "ui-monospace, Menlo, Consolas, monospace",
                    "font-size": "10",
                },
            ).text = MONTHS[month - 1]
            last_month = month

        ET.SubElement(
            grid,
            "rect",
            {
                "x": str(x),
                "y": str(y),
                "width": str(CELL),
                "height": str(CELL),
                "rx": "2",
                "fill": _palette_for_level(int(day["level"])),
            },
        )

    legend_y = height - 16
    legend = ET.SubElement(svg, "g", {"transform": f"translate({LEFT},{legend_y})"})
    ET.SubElement(
        legend,
        "text",
        {
            "x": "0",
            "y": "0",
            "fill": DIM,
            "font-family": "ui-monospace, Menlo, Consolas, monospace",
            "font-size": "11",
        },
    ).text = f"{stats['total']} contributions  ·  streak {stats['current_streak']}  ·  longest {stats['longest_streak']}"

    legend_x = width - RIGHT - 18 * len(PALETTE) - 72
    scale = ET.SubElement(svg, "g", {"transform": f"translate({legend_x},{legend_y})"})
    ET.SubElement(
        scale,
        "text",
        {"x": "0", "y": "0", "fill": DIM, "font-family": "ui-monospace, Menlo, Consolas, monospace", "font-size": "11"},
    ).text = "Less"
    for index, color in enumerate(PALETTE):
        ET.SubElement(
            scale,
            "rect",
            {
                "x": str(36 + index * 16),
                "y": "-10",
                "width": "11",
                "height": "11",
                "rx": "2",
                "fill": color,
            },
        )
    ET.SubElement(
        scale,
        "text",
        {
            "x": str(36 + len(PALETTE) * 16 + 4),
            "y": "0",
            "fill": DIM,
            "font-family": "ui-monospace, Menlo, Consolas, monospace",
            "font-size": "11",
        },
    ).text = "More"

    return ET.tostring(svg, encoding="unicode")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a GitHub-style contribution heatmap SVG.")
    parser.add_argument("--input", type=Path, default=Path("data/contributions.json"), help="Input JSON path")
    parser.add_argument("--output", type=Path, default=Path("contrib-heatmap.svg"), help="Output SVG path")
    args = parser.parse_args()

    payload = _load_payload(args.input)
    args.output.write_text(build_svg(payload), encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
