"""Validate the complete shipping content registry as a standalone CI gate."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.content import ContentRegistry, ContentValidationError


def main() -> int:
    try:
        registry = ContentRegistry.load(ROOT_DIR / "backend" / "data")
        registry.validate()
    except ContentValidationError as exc:
        print(f"Content validation failed [{exc.code}]: {exc.message}", file=sys.stderr)
        if exc.details:
            print(exc.details, file=sys.stderr)
        return 1

    print(
        "Content valid: "
        f"{len(registry.scenes)} scenes, "
        f"{len(registry.npcs)} NPCs, "
        f"{len(registry.fragments)} fragments, "
        f"{len(registry.hotspots)} hotspots, "
        f"{len(registry.choices)} choices, "
        f"{len(registry.endings)} endings."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
