"""Build data/ from collections/.

Usage:
    uv run scripts/generate.py

Writes:
    data/all-collections.json   every collection, keyed by collection id
    data/<collection>.json      one collection with its cards
    data/collections/...        card files, card images, and set logos, at their repository paths

Each card gets an "id" (its file name), a "number" (its folder), and an "image"
path, each collection a "logo" path, both relative to data/. The "$schema" keys
are dropped.
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLLECTIONS = ROOT / "collections"
OUTPUT = ROOT / "data"
ALL_COLLECTIONS = "all-collections"


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path.relative_to(ROOT)}: {error}") from error
    data.pop("$schema", None)
    return data


def copy_asset(path: Path) -> str:
    relative = path.relative_to(ROOT)
    (OUTPUT / relative).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, OUTPUT / relative)
    return relative.as_posix()


def load_collection(folder: Path) -> dict:
    cards = []
    for path in sorted(folder.glob("cards/[0-9][0-9][0-9]/*.json")):
        number, image = int(path.parent.name), copy_asset(path.parent / f"{path.parent.name}.avif")
        card = {"id": path.stem, "number": number, **load_json(path), "image": image}
        write_json(OUTPUT / path.relative_to(ROOT), card)
        cards.append(card)
    logo = folder / "logo.svg"
    return {
        "id": folder.name,
        **load_json(folder / "set.json"),
        "logo": copy_asset(logo) if logo.is_file() else None,
        "cards": cards,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")


def main() -> int:
    shutil.rmtree(OUTPUT, ignore_errors=True)
    collections = {}
    try:
        for folder in sorted(p for p in COLLECTIONS.iterdir() if p.is_dir()):
            if folder.name == ALL_COLLECTIONS:
                raise ValueError(f"a collection can't be named {ALL_COLLECTIONS!r}")
            collections[folder.name] = load_collection(folder)
            print(f"{folder.name}: {len(collections[folder.name]['cards'])} cards")
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    write_json(OUTPUT / f"{ALL_COLLECTIONS}.json", collections)
    for name, collection in collections.items():
        write_json(OUTPUT / f"{name}.json", collection)
    print(f"wrote {OUTPUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
