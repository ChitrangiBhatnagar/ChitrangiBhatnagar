from __future__ import annotations

import argparse
import base64
import io
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def prep_bw_portrait(source: Path, size: tuple[int, int] = (320, 400)) -> Image.Image:
    image = Image.open(source).convert("RGB")
    w, h = image.size

    crop_w = int(w * 0.34)
    crop_h = int(crop_w * 1.25)
    left = int(w * 0.30)
    top = int(h * 0.00)
    portrait = image.crop((left, top, left + crop_w, top + crop_h))

    gray = ImageOps.grayscale(portrait)
    gray = ImageOps.autocontrast(gray, cutoff=2)
    gray = ImageEnhance.Contrast(gray).enhance(1.25)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1.2, percent=110, threshold=2))
    return gray.resize(size, Image.Resampling.LANCZOS)


def to_data_uri(image: Image.Image, quality: int = 85) -> str:
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def build_persona_svg(photo_uri: str) -> str:
    width, height = 360, 460
    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "xmlns:xlink": "http://www.w3.org/1999/xlink",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )

    ET.SubElement(svg, "rect", {"width": str(width), "height": str(height), "rx": "12", "fill": "#0D0A07"})
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
            "stroke": "#E8A33D",
            "stroke-width": "2",
        },
    )
    ET.SubElement(svg, "rect", {"x": "1", "y": "1", "width": str(width - 2), "height": "34", "rx": "11", "fill": "#15110D"})
    ET.SubElement(
        svg,
        "text",
        {
            "x": "18",
            "y": "23",
            "fill": "#E8A33D",
            "font-family": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            "font-size": "13",
            "font-weight": "700",
        },
    ).text = "avi@github ~ $ ./render_persona.sh"

    defs = ET.SubElement(svg, "defs")
    clip_path = ET.SubElement(defs, "clipPath", {"id": "photo"})
    ET.SubElement(clip_path, "rect", {"x": "20", "y": "48", "width": "320", "height": "360", "rx": "8"})

    photo_group = ET.SubElement(svg, "g", {"clip-path": "url(#photo)"})
    image = ET.SubElement(
        photo_group,
        "image",
        {
            "x": "20",
            "y": "48",
            "width": "320",
            "height": "360",
            "href": photo_uri,
            "preserveAspectRatio": "xMidYMid slice",
        },
    )
    image.set("{http://www.w3.org/1999/xlink}href", photo_uri)

    # Animated scan line (decorative — photo stays fully visible on GitHub)
    scan = ET.SubElement(
        photo_group,
        "rect",
        {"x": "20", "y": "48", "width": "320", "height": "3", "fill": "#E8A33D", "opacity": "0.55"},
    )
    ET.SubElement(
        scan,
        "animate",
        {
            "attributeName": "y",
            "values": "48;405;48",
            "dur": "3.5s",
            "repeatCount": "indefinite",
        },
    )
    ET.SubElement(
        scan,
        "animate",
        {
            "attributeName": "opacity",
            "values": "0;0.65;0.65;0",
            "keyTimes": "0;0.08;0.92;1",
            "dur": "3.5s",
            "repeatCount": "indefinite",
        },
    )

    ET.SubElement(
        svg,
        "rect",
        {
            "x": "20",
            "y": "48",
            "width": "320",
            "height": "360",
            "rx": "8",
            "fill": "none",
            "stroke": "#E8A33D",
            "stroke-width": "1.5",
        },
    )

    footer = ET.SubElement(
        svg,
        "text",
        {
            "x": "18",
            "y": "430",
            "fill": "#E8A33D",
            "font-family": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            "font-size": "12",
        },
    )
    footer.text = "avi@github ~ $ whoami"
    cursor = ET.SubElement(
        svg,
        "rect",
        {"x": "188", "y": "418", "width": "8", "height": "14", "fill": "#E8A33D"},
    )
    ET.SubElement(
        cursor,
        "animate",
        {
            "attributeName": "opacity",
            "values": "1;0;1",
            "dur": "1.1s",
            "repeatCount": "indefinite",
        },
    )

    return ET.tostring(svg, encoding="unicode")


def build_info_card() -> str:
    width, height = 520, 460
    rows = [
        ("Now", "Shipping AI systems & polishing profile craft"),
        ("Prev", "AI/ML internships · backend · production APIs"),
        ("Stack", "Python · FastAPI · LangChain · React"),
        ("Focus", "RAG · eval · deployment patterns"),
        ("Wins", "2K+ users · 10K jobs/day · 25% latency cut"),
    ]

    svg = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )
    ET.SubElement(svg, "rect", {"width": str(width), "height": str(height), "rx": "12", "fill": "#0D0A07"})
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
            "stroke": "#E8A33D",
            "stroke-width": "2",
        },
    )
    ET.SubElement(svg, "rect", {"x": "1", "y": "1", "width": str(width - 2), "height": "34", "rx": "11", "fill": "#15110D"})
    ET.SubElement(
        svg,
        "text",
        {
            "x": "24",
            "y": "23",
            "fill": "#E8A33D",
            "font-family": "ui-monospace, Menlo, Monaco, Consolas, monospace",
            "font-size": "14",
            "font-weight": "700",
        },
    ).text = "avi@nexus: ~"

    y = 90
    for index, (label, value) in enumerate(rows):
        label_node = ET.SubElement(
            svg,
            "text",
            {
                "x": "28",
                "y": str(y),
                "fill": "#E8A33D",
                "font-family": "ui-monospace, Menlo, Monaco, Consolas, monospace",
                "font-size": "15",
                "font-weight": "700",
            },
        )
        label_node.text = f"[{label}]"
        value_node = ET.SubElement(
            svg,
            "text",
            {
                "x": "110",
                "y": str(y),
                "fill": "#F5EFE6",
                "font-family": "ui-monospace, Menlo, Monaco, Consolas, monospace",
                "font-size": "14",
            },
        )
        value_node.text = value

        # Fade-in that ends visible; if GitHub skips SMIL, keep opacity=1 fallback via final freeze
        # Start visible so README never blanks out.
        ET.SubElement(
            label_node,
            "animate",
            {
                "attributeName": "opacity",
                "values": "0.15;1",
                "begin": f"{index * 0.18}s",
                "dur": "0.5s",
                "fill": "freeze",
            },
        )
        ET.SubElement(
            value_node,
            "animate",
            {
                "attributeName": "opacity",
                "values": "0.15;1",
                "begin": f"{0.08 + index * 0.18}s",
                "dur": "0.5s",
                "fill": "freeze",
            },
        )
        y += 58

    return ET.tostring(svg, encoding="unicode")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build clean B&W animated persona + info card SVGs.")
    parser.add_argument("--source", type=Path, default=ROOT / "me.jpg")
    parser.add_argument("--persona-out", type=Path, default=ROOT / "avi-ascii.svg")
    parser.add_argument("--info-out", type=Path, default=ROOT / "info-card.svg")
    parser.add_argument("--photo-out", type=Path, default=ROOT / "assets" / "persona-photo.jpg")
    args = parser.parse_args()

    portrait = prep_bw_portrait(args.source)
    args.photo_out.parent.mkdir(parents=True, exist_ok=True)
    portrait.save(args.photo_out, format="JPEG", quality=88, optimize=True)

    uri = to_data_uri(portrait)
    args.persona_out.write_text(build_persona_svg(uri), encoding="utf-8")
    args.info_out.write_text(build_info_card(), encoding="utf-8")
    (ROOT / "assets" / "persona-card.svg").write_text(args.persona_out.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"wrote {args.photo_out}")
    print(f"wrote {args.persona_out} ({args.persona_out.stat().st_size} bytes)")
    print(f"wrote {args.info_out} ({args.info_out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
