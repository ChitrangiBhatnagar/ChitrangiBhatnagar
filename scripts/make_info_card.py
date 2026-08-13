from __future__ import annotations

import argparse
import os
from pathlib import Path
from xml.etree import ElementTree as ET

WIDTH = 490
HEIGHT = 370
BG = "#0D0A07"
PANEL = "#15110D"
ACCENT = "#E8A33D"
TEXT = "#F5EFE6"
DIM = "#C9A876"

ROWS = [
    ("Now", "Building profile art and tightening the README flow"),
    ("Prev", "AI/ML engineering intern work, backend systems, shipping"),
    ("Stack", "Python, FastAPI, LangChain, React, Airflow, Redis"),
    ("Highlights", "2K+ users, 10K daily jobs, 100+ endpoints, 25% latency cut"),
]


def build_svg(static: bool) -> str:
    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "width": str(WIDTH),
        "height": str(HEIGHT),
        "viewBox": f"0 0 {WIDTH} {HEIGHT}",
    })

    ET.SubElement(svg, "rect", {"width": str(WIDTH), "height": str(HEIGHT), "rx": "12", "fill": BG})
    ET.SubElement(svg, "rect", {"x": "1", "y": "1", "width": str(WIDTH - 2), "height": str(HEIGHT - 2), "rx": "11", "fill": "none", "stroke": ACCENT, "stroke-width": "2"})
    ET.SubElement(svg, "rect", {"x": "1", "y": "1", "width": str(WIDTH - 2), "height": "34", "rx": "11", "fill": PANEL})
    ET.SubElement(svg, "text", {"x": "24", "y": "23", "fill": ACCENT, "font-family": "monospace", "font-size": "15", "font-weight": "700"}).text = "avi@nexus: ~"

    y = 72
    for index, (label, value) in enumerate(ROWS):
        label_node = ET.SubElement(svg, "text", {"x": "24", "y": str(y), "fill": ACCENT, "font-family": "monospace", "font-size": "15", "font-weight": "700"})
        label_node.text = f"[{label}]"
        value_node = ET.SubElement(svg, "text", {"x": "110", "y": str(y), "fill": TEXT, "font-family": "monospace", "font-size": "15"})
        value_node.text = value
        if not static:
            label_node.set("opacity", "0")
            value_node.set("opacity", "0")
            ET.SubElement(label_node, "animate", {
                "attributeName": "opacity",
                "values": "0;1;1",
                "keyTimes": "0;0.15;1",
                "dur": f"3.2s",
                "begin": f"{index * 0.25}s",
                "fill": "freeze",
            })
            ET.SubElement(value_node, "animate", {
                "attributeName": "opacity",
                "values": "0;1;1",
                "keyTimes": "0;0.15;1",
                "dur": f"3.2s",
                "begin": f"{index * 0.25 + 0.08}s",
                "fill": "freeze",
            })
        y += 64

    # GitHub README often skips SMIL animation — keep cards fully visible by default.
    if not static:
        footer = ET.SubElement(svg, "text", {"x": "24", "y": str(HEIGHT - 28), "fill": DIM, "font-family": "monospace", "font-size": "12"})
        footer.text = "animated preview"
    return ET.tostring(svg, encoding="unicode")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the profile info card SVG.")
    parser.add_argument("--output", type=Path, default=Path("info-card.svg"), help="Output SVG path")
    parser.add_argument("--animate", action="store_true", help="Enable fade-in animation (not reliable on GitHub README)")
    args = parser.parse_args()
    static = not args.animate and os.environ.get("STATIC", "1") != "0"
    args.output.write_text(build_svg(static=static), encoding="utf-8")


if __name__ == "__main__":
    main()
