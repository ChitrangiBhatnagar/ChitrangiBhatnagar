from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def prep_for_ascii(source: Path, output: Path) -> None:
    image = Image.open(source).convert("RGB")
    w, h = image.size

    # Tight face / upper-body crop tuned for me.jpg composition.
    crop_w = int(w * 0.38)
    crop_h = int(h * 0.72)
    left = int(w * 0.28)
    top = int(h * 0.02)
    portrait = image.crop((left, top, left + crop_w, top + crop_h))

    gray = ImageOps.grayscale(portrait)
    gray = ImageOps.autocontrast(gray, cutoff=3)
    gray = ImageEnhance.Contrast(gray).enhance(1.55)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1.5, percent=140, threshold=2))
    gray = gray.resize((640, 900), Image.Resampling.LANCZOS)

    output.parent.mkdir(parents=True, exist_ok=True)
    gray.save(output, format="PNG")
    print(f"wrote {output} ({output.stat().st_size} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prep a photo for B&W ASCII SVG conversion.")
    parser.add_argument("source", nargs="?", type=Path, default=Path("me.jpg"))
    parser.add_argument("--output", type=Path, default=Path("source-prepped.png"))
    args = parser.parse_args()
    prep_for_ascii(args.source, args.output)


if __name__ == "__main__":
    main()
