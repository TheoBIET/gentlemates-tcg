"""Rename each card image to <number>.avif.

Usage:
    uv run scripts/rename.py

E.g. cards/023/023_E_Joueur_Rose_Marteen-Supreme.avif -> cards/023/023.avif.
A card folder with more than one .avif is reported and left untouched.
"""

import sys
from pathlib import Path

COLLECTIONS = Path(__file__).resolve().parent.parent / "collections"


def main() -> int:
    renamed = failed = 0
    for folder in sorted(COLLECTIONS.glob("*/cards/[0-9][0-9][0-9]")):
        images = list(folder.glob("*.avif"))
        if len(images) > 1:
            print(f"error: {folder}: {len(images)} .avif files, expected one", file=sys.stderr)
            failed += 1
        elif images and images[0].stem != folder.name:
            images[0].rename(folder / f"{folder.name}.avif")
            print(f"{images[0]} -> {folder.name}.avif")
            renamed += 1

    print(f"\n{renamed} renamed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
