from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

RAMP = " .`:-=+*cs#%@"
OUTPUT_WIDTH = 100
OUTPUT_HEIGHT = 53
BLOCK_SIZE = 8
TEXT_COLOR = "#D9D9D9"
BACKGROUND = "#000000"


def image_to_grid(image: Image.Image, width: int, height: int) -> list[str]:
    resized = image.convert("L").resize((width, height), Image.Resampling.LANCZOS)
    flattened = getattr(resized, "get_flattened_data", None)
    pixels = list(flattened()) if callable(flattened) else list(resized.getdata())
    ramp_max = len(RAMP) - 1
    rows: list[str] = []
    for y in range(height):
        row = []
        for x in range(width):
            brightness = pixels[y * width + x]
            ramp_index = round((brightness / 255) * ramp_max)
            row.append(RAMP[ramp_index])
        rows.append("".join(row))
    return rows


def build_svg(grid: list[str]) -> str:
    width = OUTPUT_WIDTH * BLOCK_SIZE + 60
    height = OUTPUT_HEIGHT * 14 + 80
    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )

    ET.SubElement(svg, "rect", {"width": str(width), "height": str(height), "fill": BACKGROUND})
    ET.SubElement(svg, "defs")

    text_group = ET.SubElement(svg, "g", {"font-family": "monospace", "font-size": "12", "fill": TEXT_COLOR})
    ET.SubElement(text_group, "text", {"x": "30", "y": "28", "fill": TEXT_COLOR, "font-size": "16"}).text = "avi@github ~ $ ./contributions.sh"

    start_y = 54
    for row_index, row in enumerate(grid):
        y = start_y + row_index * 12
        row_group = ET.SubElement(text_group, "text", {"x": "30", "y": str(y)})
        row_group.text = row
        animate = ET.SubElement(row_group, "animate", {
            "attributeName": "opacity",
            "values": "0;0;1;1",
            "keyTimes": f"0;{row_index / (len(grid) + 8):.4f};{(row_index + 2) / (len(grid) + 8):.4f};1",
            "dur": "5s",
            "repeatCount": "1",
            "fill": "freeze",
        })
        animate.tail = None

    footer = ET.SubElement(text_group, "text", {"x": "30", "y": str(height - 24), "font-size": "13"})
    footer.text = "avi@github ~ $ whoami"

    return ET.tostring(svg, encoding="unicode")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a prepped portrait into an SVG ASCII animation.")
    parser.add_argument("image", nargs="?", default=Path("source-prepped.png"), type=Path, help="Prepped image path")
    parser.add_argument("--output", type=Path, default=Path("avi-ascii.svg"), help="Output SVG path")
    args = parser.parse_args()

    image = Image.open(args.image)
    grid = image_to_grid(image, OUTPUT_WIDTH, OUTPUT_HEIGHT)
    args.output.write_text(build_svg(grid), encoding="utf-8")


if __name__ == "__main__":
    main()
