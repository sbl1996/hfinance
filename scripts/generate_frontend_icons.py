#!/usr/bin/env python3
"""Generate frontend PWA icon files from an RGBA source image."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "frontend" / "public"

TARGETS = {
    "favicon-32x32.png": 32,
    "icons/apple-touch-icon.png": 180,
    "icons/icon-192x192.png": 192,
    "icons/icon-512x512.png": 512,
}


def fit_on_transparent_canvas(source: Image.Image, size: int) -> Image.Image:
    """Resize source into a square transparent canvas without losing alpha."""
    image = source.convert("RGBA")
    scale = min(size / image.width, size / image.height)
    resized_dimensions = (
        max(1, round(image.width * scale)),
        max(1, round(image.height * scale)),
    )
    image = image.resize(resized_dimensions, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - image.width) // 2, (size - image.height) // 2)
    canvas.alpha_composite(image, offset)
    return canvas


def generate_icons(source_path: Path, output_dir: Path) -> None:
    if not source_path.is_file():
        raise FileNotFoundError(f"source image not found: {source_path}")

    with Image.open(source_path) as source:
        for relative_path, size in TARGETS.items():
            output_path = output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            icon = fit_on_transparent_canvas(source, size)
            icon.save(output_path, "PNG", optimize=True)
            print(f"wrote {output_path.relative_to(ROOT)} ({size}x{size}, {icon.mode})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate frontend/public icon PNGs from a source image."
    )
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        help=f"source PNG path",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"frontend public directory, defaults to {DEFAULT_OUTPUT_DIR}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_icons(args.source.expanduser(), args.output_dir.expanduser())


if __name__ == "__main__":
    main()
