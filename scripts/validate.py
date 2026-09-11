"""Validate collections/ against schemas/.

Usage:
    uv run scripts/validate.py

For every collection, checks that:
    - set.json matches schemas/set.json
    - each card folder in cards/ is named with 3 digits within the set total and
      holds exactly <number>.avif and one <slug>.json, or nothing yet (missing card)
    - <slug>.json matches schemas/card.json and is named after the slug of the card name
    - card slugs are unique across all collections

.DS_Store files are ignored. Exits with code 1 on any error.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas"
COLLECTIONS = ROOT / "collections"
IGNORED_NAMES = {".DS_Store"}


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def load_validator(schema_name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_json(path: Path, validator: Draft202012Validator, schema_name: str) -> tuple[dict | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, [f"invalid JSON: {error}"]

    errors = [
        f"{error.json_path}: {error.message}"
        for error in sorted(validator.iter_errors(data), key=lambda error: error.json_path)
    ]
    if not isinstance(data, dict):
        return None, errors

    ref = data.get("$schema")
    if isinstance(ref, str) and (path.parent / ref).resolve() != SCHEMAS / schema_name:
        errors.append(f"$.$schema: {ref!r} does not point to schemas/{schema_name}")
    return data, errors


def check_card(path: Path, card: dict, slugs: dict[str, Path]) -> list[str]:
    errors = []

    name = card.get("name")
    if isinstance(name, str) and path.stem != slugify(name):
        errors.append(f"file must be named {slugify(name)}.json after the card name {name!r}")

    if path.stem in slugs:
        errors.append(f"slug {path.stem!r} already used by {slugs[path.stem].relative_to(ROOT)}")
    slugs.setdefault(path.stem, path)
    return errors


def check_card_folder(
    folder: Path, total: int | None, validator: Draft202012Validator, slugs: dict[str, Path]
) -> dict[Path, list[str]]:
    files = sorted(p for p in folder.iterdir() if p.name not in IGNORED_NAMES)
    if not files:
        return {}
    if not re.fullmatch(r"\d{3}", folder.name):
        return {folder: ["card folder must be named with 3 digits, e.g. 016"]}

    image = folder / f"{folder.name}.avif"
    cards = [p for p in files if p.suffix == ".json"]
    unexpected = [p.name for p in files if p != image and p not in cards]

    errors = []
    if total is not None and not 1 <= int(folder.name) <= total:
        errors.append(f"card number must be between 001 and {total:03}")
    if image not in files:
        errors.append(f"missing image {image.name}")
    if len(cards) != 1:
        errors.append(f"expected one <slug>.json, found {len(cards)}")
    if unexpected:
        errors.append(f"unexpected files: {', '.join(unexpected)}")

    results = {folder: errors}
    for path in cards:
        card, card_errors = validate_json(path, validator, "card.json")
        if card is not None:
            card_errors += check_card(path, card, slugs)
        results[path] = card_errors
    return results


def main() -> int:
    validators = {}
    for schema_name in ("set.json", "card.json"):
        try:
            validators[schema_name] = load_validator(schema_name)
        except SchemaError as error:
            print(f"error: schemas/{schema_name} is not a valid JSON Schema: {error.message}", file=sys.stderr)
            return 1

    collections = sorted(p for p in COLLECTIONS.iterdir() if p.is_dir())
    if not collections:
        print(f"error: no collection found in {COLLECTIONS}", file=sys.stderr)
        return 1

    results: dict[Path, list[str]] = {}
    slugs: dict[str, Path] = {}
    for collection in collections:
        set_path = collection / "set.json"
        total = None
        if set_path.is_file():
            data, results[set_path] = validate_json(set_path, validators["set.json"], "set.json")
            if data is not None and isinstance(data.get("total"), int):
                total = data["total"]
        else:
            results[set_path] = ["missing set.json"]

        cards_dir = collection / "cards"
        if not cards_dir.is_dir():
            results[cards_dir] = ["missing cards/ folder"]
            continue
        for folder in sorted(p for p in cards_dir.iterdir() if p.is_dir()):
            results.update(check_card_folder(folder, total, validators["card.json"], slugs))

    failed = 0
    for path, errors in results.items():
        if errors:
            failed += 1
            print(f"FAIL {path.relative_to(ROOT)}")
            for error in errors:
                print(f"     {error}")
        elif path.suffix == ".json":
            print(f"ok   {path.relative_to(ROOT)}")

    cards = sum(1 for path in results if path.suffix == ".json" and path.name != "set.json")
    print(f"\n{cards} cards checked, {failed} with errors")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
