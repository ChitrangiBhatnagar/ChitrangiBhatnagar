from __future__ import annotations

import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]

RAMP = " .:-=+*#%@"
ACCENT = "#E8A33D"
TEXT = "#F5EFE6"
DIM = "#A5927B"
BG = "#0D0A07"
PANEL = "#15110D"


def crop_face(image: Image.Image) -> Image.Image:
    """Tight head crop tuned for me.jpg."""
    w, h = image.size
    return image.crop((int(w * 0.34), int(h * 0.02), int(w * 0.62), int(h * 0.70)))


def prep_gray(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=2)
    gray = ImageEnhance.Contrast(gray).enhance(1.6)
    gray = ImageEnhance.Brightness(gray).enhance(1.05)

    # Soft vignette kills busy background so the face dominates the ASCII.
    arr = np.array(gray).astype(np.float32)
    yy, xx = np.mgrid[0 : arr.shape[0], 0 : arr.shape[1]]
    cy, cx = arr.shape[0] * 0.42, arr.shape[1] * 0.50
    ry, rx = arr.shape[0] * 0.55, arr.shape[1] * 0.55
    dist = ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2
    mask = np.clip(1.15 - dist, 0.0, 1.0)
    arr = arr * mask
    gray = Image.fromarray(arr.astype(np.uint8))
    return gray.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=2))


def to_ascii_grid(image: Image.Image, cols: int, rows: int) -> list[str]:
    resized = image.resize((cols, rows), Image.Resampling.LANCZOS)
    pixels = list(resized.get_flattened_data()) if hasattr(resized, "get_flattened_data") else list(resized.getdata())
    ramp_max = len(RAMP) - 1
    lines: list[str] = []
    for y in range(rows):
        chars = []
        for x in range(cols):
            brightness = pixels[y * cols + x]
            idx = round((brightness / 255) * ramp_max)
            chars.append(RAMP[idx])
        lines.append("".join(chars))
    return lines


def build_hero_svg(grid: list[str]) -> str:
    cols = len(grid[0])
    rows = len(grid)
    cell_w, cell_h = 7, 11
    ascii_pad_x, ascii_pad_y = 26, 58
    left_panel_w = ascii_pad_x * 2 + cols * cell_w
    right_panel_w = 400
    width = left_panel_w + right_panel_w
    height = max(ascii_pad_y + rows * cell_h + 44, 540)

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
            "role": "img",
            "aria-label": "Chitrangi Bhatnagar ASCII persona card",
        },
    )

    ET.SubElement(svg, "rect", {"width": str(width), "height": str(height), "rx": "14", "fill": BG})
    ET.SubElement(
        svg,
        "rect",
        {
            "x": "1",
            "y": "1",
            "width": str(width - 2),
            "height": str(height - 2),
            "rx": "13",
            "fill": "none",
            "stroke": ACCENT,
            "stroke-width": "1.5",
        },
    )
    ET.SubElement(svg, "rect", {"x": "1", "y": "1", "width": str(width - 2), "height": "36", "rx": "13", "fill": PANEL})
    ET.SubElement(svg, "rect", {"x": "1", "y": "20", "width": str(width - 2), "height": "17", "fill": PANEL})
    ET.SubElement(svg, "line", {"x1": "1", "y1": "37", "x2": str(width - 1), "y2": "37", "stroke": ACCENT, "stroke-width": "1"})
    for i, color in enumerate(("#FF5F56", "#FFBD2E", "#27C93F")):
        ET.SubElement(svg, "circle", {"cx": str(22 + i * 18), "cy": "19", "r": "5", "fill": color})
    ET.SubElement(
        svg,
        "text",
        {
            "x": str(width // 2),
            "y": "23",
            "fill": ACCENT,
            "font-family": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "font-size": "13",
            "font-weight": "700",
            "text-anchor": "middle",
        },
    ).text = "chitrangi@nexus — persona.card"

    ET.SubElement(
        svg,
        "line",
        {
            "x1": str(left_panel_w),
            "y1": "37",
            "x2": str(left_panel_w),
            "y2": str(height - 1),
            "stroke": "#3A2A18",
            "stroke-width": "1",
        },
    )

    ascii_group = ET.SubElement(
        svg,
        "g",
        {
            "font-family": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
            "font-size": "11",
            "fill": ACCENT,
        },
    )
    ET.SubElement(ascii_group, "text", {"x": str(ascii_pad_x), "y": "52", "fill": DIM, "font-size": "11"}).text = "$ cat portrait.ascii"

    for i, line in enumerate(grid):
        y = ascii_pad_y + 6 + i * cell_h
        node = ET.SubElement(ascii_group, "text", {"x": str(ascii_pad_x), "y": str(y)})
        node.text = line
        ET.SubElement(
            node,
            "animate",
            {
                "attributeName": "opacity",
                "values": "0.3;1",
                "dur": "0.75s",
                "begin": f"{i * 0.014:.3f}s",
                "fill": "freeze",
            },
        )

    rx = left_panel_w + 26
    font = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    ET.SubElement(svg, "text", {"x": str(rx), "y": "68", "fill": ACCENT, "font-family": font, "font-size": "20", "font-weight": "700"}).text = "Chitrangi Bhatnagar"
    ET.SubElement(svg, "text", {"x": str(rx), "y": "92", "fill": TEXT, "font-family": font, "font-size": "13"}).text = "> AI Engineer  ·  ML Practitioner"

    y = 130
    for label, value in (
        ("LOC", "Bengaluru, India"),
        ("EDU", "B.Tech CS · AI & ML"),
        ("UNI", "Presidency University"),
        ("GPA", "8.54"),
        ("NOW", "Open to opportunities"),
    ):
        ET.SubElement(svg, "text", {"x": str(rx), "y": str(y), "fill": DIM, "font-family": font, "font-size": "12"}).text = f"[{label}]"
        ET.SubElement(svg, "text", {"x": str(rx + 70), "y": str(y), "fill": TEXT, "font-family": font, "font-size": "12"}).text = value
        y += 28

    ET.SubElement(svg, "text", {"x": str(rx), "y": str(y + 16), "fill": ACCENT, "font-family": font, "font-size": "13", "font-weight": "700"}).text = "[ stack ]"
    y += 44
    for skill, bar in (
        ("Python / AI / ML", 158),
        ("LangChain / RAG", 138),
        ("FastAPI / Backend", 146),
        ("React / TypeScript", 126),
    ):
        ET.SubElement(svg, "text", {"x": str(rx), "y": str(y), "fill": TEXT, "font-family": font, "font-size": "12"}).text = skill
        ET.SubElement(svg, "rect", {"x": str(rx + 168), "y": str(y - 9), "width": "168", "height": "8", "rx": "4", "fill": "#241B10"})
        ET.SubElement(svg, "rect", {"x": str(rx + 168), "y": str(y - 9), "width": str(bar), "height": "8", "rx": "4", "fill": ACCENT})
        y += 30

    ET.SubElement(svg, "text", {"x": str(rx), "y": str(y + 12), "fill": ACCENT, "font-family": font, "font-size": "13", "font-weight": "700"}).text = "[ focus ]"
    ET.SubElement(svg, "text", {"x": str(rx), "y": str(y + 36), "fill": TEXT, "font-family": font, "font-size": "12"}).text = "eval · features · deployment"

    ET.SubElement(svg, "text", {"x": "26", "y": str(height - 16), "fill": DIM, "font-family": font, "font-size": "11"}).text = "ready."
    cursor = ET.SubElement(svg, "rect", {"x": "70", "y": str(height - 28), "width": "7", "height": "12", "fill": ACCENT})
    ET.SubElement(cursor, "animate", {"attributeName": "opacity", "values": "1;0;1", "dur": "1.05s", "repeatCount": "indefinite"})

    return ET.tostring(svg, encoding="unicode")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ASCII persona hero SVG from me.jpg")
    parser.add_argument("--source", type=Path, default=ROOT / "me.jpg")
    parser.add_argument("--out", type=Path, default=ROOT / "assets" / "persona-card.svg")
    parser.add_argument("--cols", type=int, default=54)
    parser.add_argument("--rows", type=int, default=66)
    args = parser.parse_args()

    face = prep_gray(crop_face(Image.open(args.source).convert("RGB")))
    face.save(ROOT / "source-prepped.png")
    face.resize((320, 400), Image.Resampling.LANCZOS).save(ROOT / "assets" / "persona-photo.jpg", quality=90)

    grid = to_ascii_grid(face, args.cols, args.rows)
    print("ASCII preview (eyes/mid):")
    for line in grid[18:36]:
        print(line)

    svg = build_hero_svg(grid)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg, encoding="utf-8")
    (ROOT / "avi-ascii.svg").write_text(svg, encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
