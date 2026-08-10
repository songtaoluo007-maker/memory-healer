from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

PORTRAIT_BUDGET = 800_000
FRAGMENT_BUDGET = 600_000


def _common_errors(path: Path, budget: int) -> tuple[list[str], Image.Image | None]:
    errors: list[str] = []
    if not path.is_file():
        return [f"asset does not exist: {path}"], None
    if path.stat().st_size > budget:
        errors.append(f"asset exceeds {budget} bytes")
    try:
        image = Image.open(path)
        image.load()
    except Exception as exc:
        return [f"asset cannot be decoded: {exc}"], None
    if image.format != "WEBP":
        errors.append("asset must be WebP")
    return errors, image


def validate_portrait(path: Path) -> list[str]:
    errors, image = _common_errors(path, PORTRAIT_BUDGET)
    if image is None:
        return errors
    if image.height <= image.width:
        errors.append("portrait must be vertical")
    if "A" not in image.getbands():
        errors.append("portrait must contain an alpha channel")
        errors.append("portrait must contain transparent pixels")
        return errors
    alpha = image.getchannel("A")
    minimum, maximum = alpha.getextrema()
    if minimum > 16:
        errors.append("portrait must contain transparent pixels")
    if maximum < 240:
        errors.append("portrait subject must contain opaque pixels")
    transparent = sum(value <= 16 for value in alpha.resize((64, 64)).getdata())
    if transparent / (64 * 64) < 0.18:
        errors.append("portrait transparent area must be at least 18%")
    return errors


def validate_fragment(path: Path) -> list[str]:
    errors, image = _common_errors(path, FRAGMENT_BUDGET)
    if image is None:
        return errors
    ratio = image.width / image.height
    if abs(ratio - 4 / 3) > 0.03:
        errors.append("fragment aspect ratio must be 4:3 ± 0.03")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portrait", action="append", default=[])
    parser.add_argument("--fragment", action="append", default=[])
    args = parser.parse_args()
    failures: list[str] = []
    for raw in args.portrait:
        path = Path(raw)
        failures.extend(f"{path}: {error}" for error in validate_portrait(path))
    for raw in args.fragment:
        path = Path(raw)
        failures.extend(f"{path}: {error}" for error in validate_fragment(path))
    if failures:
        print("\n".join(failures))
        return 1
    print(f"Validated {len(args.portrait)} portraits and {len(args.fragment)} fragments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
