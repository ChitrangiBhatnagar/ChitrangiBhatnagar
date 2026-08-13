from __future__ import annotations

import argparse
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep_photo(source_path: Path, output_path: Path) -> None:
    source_image = Image.open(source_path).convert("RGBA")
    foreground = remove(source_image)

    if isinstance(foreground, Image.Image):
        foreground_image = foreground.convert("RGBA")
    elif isinstance(foreground, np.ndarray):
        foreground_image = Image.fromarray(foreground).convert("RGBA")
    else:
        foreground_image = Image.open(io.BytesIO(foreground)).convert("RGBA")

    rgba = np.array(foreground_image)
    alpha = rgba[:, :, 3:4].astype(np.float32) / 255.0
    rgb = rgba[:, :, :3].astype(np.float32)

    white_background = np.full_like(rgb, 255.0)
    composited = rgb * alpha + white_background * (1.0 - alpha)
    bgr = cv2.cvtColor(composited.astype(np.uint8), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    normalized = cv2.normalize(enhanced, None, 0, 255, cv2.NORM_MINMAX)

    cv2.imwrite(str(output_path), normalized)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a portrait for ASCII conversion.")
    parser.add_argument("source", type=Path, help="Source photo path")
    parser.add_argument("--output", type=Path, default=Path("source-prepped.png"), help="Output image path")
    args = parser.parse_args()
    prep_photo(args.source, args.output)


if __name__ == "__main__":
    main()
