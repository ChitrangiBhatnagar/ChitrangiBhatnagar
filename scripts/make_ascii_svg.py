from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

RAMP = " .`:-=+*cs#%@"
OUTPUT_WIDTH = 64
OUTPUT_HEIGHT = 78
TEXT_COLOR = "#D9D9D9"
ACCENT = "#E8A33D"
BACKGROUND = "#0D0A07"
LINE_HEIGHT = 12
FONT_SIZE = 12


def image_to_grid(image: Image.Image, width: int, height: int) -> list[str]:
    resized = image.convert("L").resize((width, height), Image.Resampling.LANCZOS)
    pixels = list(resized.get_flattened_data()) if hasattr(resized, "get_flattened_data") else list(resized.getdata())
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


def build_svg(grid: list[str], animate: bool) -> str:
    width = OUTPUT_WIDTH * 8 + 48
    height = OUTPUT_HEIGHT * LINE_HEIGHT + 96
    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )

    ET.SubElement(svg, "rect", {"width": str(width), "height": str(height), "rx": "12", "fill": BACKGROUND})
    ET.SubElement(
        svg,
        "rect",
        {
            "x": "1",
            "y": "1",
            "width": str(width - 2),
            "height": str(height - 2),
            "rx": "11",
            "fill": "none",
            "stroke": ACCENT,
            "stroke-width": "2",
        },
    )

    text_group = ET.SubElement(
        svg,
        "g",
        {"font-family": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace", "font-size": str(FONT_SIZE), "fill": TEXT_COLOR},
    )
    header = ET.SubElement(text_group, "text", {"x": "24", "y": "28", "fill": ACCENT, "font-size": "14", "font-weight": "700"})
    header.text = "avi@github ~ $ ./render_persona.sh"

    start_y = 52
    total = max(len(grid), 1)
    for row_index, row in enumerate(grid):
        y = start_y + row_index * LINE_HEIGHT
        node = ET.SubElement(text_group, "text", {"x": "24", "y": str(y)})
        node.text = row
        if animate:
            node.set("opacity", "0")
            begin = f"{(row_index / total) * 4.5:.3f}s"
            ET.SubElement(
                node,
                "animate",
                {
                    "attributeName": "opacity",
                    "values": "0;0;1;1",
                    "keyTimes": "0;0.02;0.12;1",
                    "dur": "5s",
                    "begin": begin,
                    "repeatCount": "indefinite",
                    "fill": "freeze",
                },
            )

    footer = ET.SubElement(text_group, "text", {"x": "24", "y": str(height - 24), "fill": ACCENT, "font-size": "13"})
    footer.text = "avi@github ~ $ whoami"
    if animate:
        footer.set("opacity", "0")
        ET.SubElement(
            footer,
            "animate",
            {
                "attributeName": "opacity",
                "values": "0;0;1;1",
                "keyTimes": "0;0.85;0.92;1",
                "dur": "5s",
                "repeatCount": "indefinite",
                "fill": "freeze",
            },
        )

    return ET.tostring(svg, encoding="unicode")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a prepped portrait into an animated B&W ASCII SVG.")
    parser.add_argument("image", nargs="?", default=Path("source-prepped.png"), type=Path)
    parser.add_argument("--output", type=Path, default=Path("avi-ascii.svg"))
    parser.add_argument("--no-animate", action="store_true")
    args = parser.parse_args()

    image = Image.open(args.image)
    grid = image_to_grid(image, OUTPUT_WIDTH, OUTPUT_HEIGHT)
    args.output.write_text(build_svg(grid, animate=not args.no_animate), encoding="utf-8")
    print(f"wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
