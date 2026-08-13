from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
CELL_SIZE = 12
CELL_GAP = 3
WEEKS = 53
DAYS = 7
LEFT_PAD = 24
TOP_PAD = 42
RIGHT_PAD = 24
BOTTOM_PAD = 48


def _load_payload(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _palette_for_level(level: int) -> str:
    return PALETTE[max(0, min(level, len(PALETTE) - 1))]


def _week_rows(days: list[dict[str, object]]) -> dict[int, list[dict[str, object]]]:
    weeks: dict[int, list[dict[str, object]]] = {index: [] for index in range(WEEKS)}
    for index, day in enumerate(days[: WEEKS * DAYS]):
        week = index // DAYS
        weeks[week].append(day)
    return weeks


def build_svg(payload: dict[str, object]) -> str:
    days = payload["days"]  # type: ignore[index]
    stats = payload["stats"]  # type: ignore[index]
    width = LEFT_PAD + WEEKS * (CELL_SIZE + CELL_GAP) + RIGHT_PAD
    height = TOP_PAD + DAYS * (CELL_SIZE + CELL_GAP) + BOTTOM_PAD

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )

    ET.SubElement(svg, "rect", {"width": str(width), "height": str(height), "rx": "12", "fill": "#0d1117"})
    ET.SubElement(svg, "text", {"x": str(LEFT_PAD), "y": "24", "fill": "#f0f6fc", "font-family": "monospace", "font-size": "15", "font-weight": "700"}).text = "avi@github ~ $ contributions"
    ET.SubElement(svg, "text", {"x": str(LEFT_PAD), "y": str(height - 18), "fill": "#8b949e", "font-family": "monospace", "font-size": "12"}).text = (
        f"{stats['total']} contributions in the last year | current streak {stats['current_streak']} | longest streak {stats['longest_streak']}"
    )

    grid = ET.SubElement(svg, "g", {"transform": f"translate({LEFT_PAD},{TOP_PAD})"})
    for index, day in enumerate(days[: WEEKS * DAYS]):
        week = index // DAYS
        day_of_week = index % DAYS
        x = week * (CELL_SIZE + CELL_GAP)
        y = day_of_week * (CELL_SIZE + CELL_GAP)
        rect = ET.SubElement(
            grid,
            "rect",
            {
                "x": str(x),
                "y": str(y),
                "width": str(CELL_SIZE),
                "height": str(CELL_SIZE),
                "rx": "3",
                "fill": _palette_for_level(int(day["level"])),
            },
        )
        rect.set("opacity", "0")
        ET.SubElement(rect, "animate", {
            "attributeName": "opacity",
            "values": "0;1;1",
            "keyTimes": f"0;{index / (len(days) + 12):.4f};1",
            "dur": "4.5s",
            "fill": "freeze",
        })

    legend = ET.SubElement(svg, "g", {"transform": f"translate({LEFT_PAD},{height - 36})"})
    ET.SubElement(legend, "text", {"x": "0", "y": "0", "fill": "#8b949e", "font-family": "monospace", "font-size": "12"}).text = "Less"
    for index, color in enumerate(PALETTE):
        ET.SubElement(legend, "rect", {
            "x": str(40 + index * 18),
            "y": "-10",
            "width": "12",
            "height": "12",
            "rx": "2",
            "fill": color,
        })
    ET.SubElement(legend, "text", {"x": str(40 + len(PALETTE) * 18 + 6), "y": "0", "fill": "#8b949e", "font-family": "monospace", "font-size": "12"}).text = "More"

    return ET.tostring(svg, encoding="unicode")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a GitHub-style contribution heatmap SVG.")
    parser.add_argument("--input", type=Path, default=Path("data/contributions.json"), help="Input JSON path")
    parser.add_argument("--output", type=Path, default=Path("contrib-heatmap.svg"), help="Output SVG path")
    args = parser.parse_args()

    payload = _load_payload(args.input)
    args.output.write_text(build_svg(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
