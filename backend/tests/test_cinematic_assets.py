from pathlib import Path

from PIL import Image

from scripts.validate_cinematic_assets import validate_fragment, validate_portrait

ROOT = Path(__file__).parents[2]


def save_rgba(path: Path, size: tuple[int, int], alpha: int) -> None:
    Image.new("RGBA", size, (120, 90, 60, alpha)).save(path, "WEBP", lossless=True)


def test_transparent_portrait_passes(tmp_path: Path) -> None:
    path = tmp_path / "portrait.webp"
    image = Image.new("RGBA", (600, 1000), (0, 0, 0, 0))
    image.paste((120, 90, 60, 255), (180, 100, 500, 950))
    image.save(path, "WEBP", lossless=True)
    assert validate_portrait(path) == []


def test_opaque_portrait_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "portrait.webp"
    save_rgba(path, (600, 1000), 255)
    assert "portrait must contain transparent pixels" in validate_portrait(path)


def test_fragment_requires_four_by_three_and_budget(tmp_path: Path) -> None:
    path = tmp_path / "fragment.webp"
    Image.new("RGB", (1200, 900), (40, 30, 20)).save(path, "WEBP", quality=80)
    assert validate_fragment(path) == []


def test_fragment_rejects_wrong_aspect_ratio(tmp_path: Path) -> None:
    path = tmp_path / "fragment.webp"
    Image.new("RGB", (1600, 900), (40, 30, 20)).save(path, "WEBP", quality=80)
    assert "fragment aspect ratio must be 4:3 ± 0.03" in validate_fragment(path)


def test_xiaoyu_2089_aged_portrait_is_deployable_and_distinct() -> None:
    aged = ROOT / "frontend/src/assets/cinematic/xiaoyu-2089-aged-solid.webp"
    xiaoyu_2050 = ROOT / "frontend/src/assets/cinematic/xiaoyu-2050-solid.webp"

    assert aged.is_file(), f"missing aged Xiaoyu portrait: {aged}"
    assert aged.suffix.lower() == ".webp"
    with Image.open(aged) as image:
        assert image.format == "WEBP"
        assert image.width >= 600
        assert image.height >= 1000
    assert aged.read_bytes() != xiaoyu_2050.read_bytes()
