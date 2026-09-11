"""List the cards revealed on gentlemates.com/tcg-cards.

Usage:
    uv run scripts/scrape.py            # print every card, + marks cards missing from collections/
    uv run scripts/scrape.py --images   # also download the images of the missing cards

The card list comes from the list_tcg_cards Supabase function called by the page.
The Supabase URL and public anon key are read from the page's JavaScript bundles.

Images are saved as cards/<number>/<site file name>.avif, e.g.
cards/023/023_E_Joueur_Rose_Marteen-Supreme.avif, ready for rename.py.
Cards without a set number (e.g. 124_level-2.avif) are listed apart and never downloaded.
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLLECTION = ROOT / "collections" / "tout-commence-ici"
SITE = "https://www.gentlemates.com"
CARDLIST_PAGE = f"{SITE}/tcg-cards"
USER_AGENT = "gentlemates-tcg (+https://github.com/TheoBIET/gentlemates-tcg)"
CARD_FILE = re.compile(r"(\d{3})_([A-Z]{1,2})_.+\.avif")


def fetch(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def find_supabase() -> tuple[str, str]:
    html = fetch(CARDLIST_PAGE).decode("utf-8")
    for script in dict.fromkeys(re.findall(r"/_next/static/chunks/[^\"'?\\]+\.js", html)):
        code = fetch(SITE + script).decode("utf-8", "replace")
        url = re.search(r"https://[a-z0-9]+\.supabase\.co", code)
        key = re.search(r"eyJ[\w-]+\.[\w-]+\.[\w-]+", code)
        if url and key:
            return url.group(), key.group()
    raise ValueError(f"no Supabase URL and key found in the scripts of {CARDLIST_PAGE}")


def list_cards(url: str, key: str) -> list[dict]:
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    return json.loads(fetch(f"{url}/rest/v1/rpc/list_tcg_cards", b"{}", headers))


def file_name(card: dict) -> str:
    return urllib.parse.unquote(urllib.parse.urlsplit(card["image_url"]).path.rsplit("/", 1)[1])


def main() -> int:
    download = "--images" in sys.argv[1:]
    try:
        cards = list_cards(*find_supabase())
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    known = {path.parent.name for path in COLLECTION.glob("cards/[0-9][0-9][0-9]/*.json")}
    missing = downloaded = 0
    extras = []
    for card in cards:
        name = file_name(card) if card.get("image_url") else ""
        match = CARD_FILE.fullmatch(name)
        if not card.get("found") or not match:
            extras.append(card)
            continue

        number, rarity = match.groups()
        new = number not in known
        missing += new
        print(f"{'+' if new else ' '} {number}  {rarity:<2}  {card['name']}")

        folder = COLLECTION / "cards" / number
        if download and new and not any(folder.glob("*.avif")):
            folder.mkdir(parents=True, exist_ok=True)
            (folder / name).write_bytes(fetch(card["image_url"]))
            downloaded += 1

    if extras:
        print("\nwithout a set number:")
        for card in extras:
            print(f"  {card['name'] if card.get('found') else '(not revealed)'}  [{file_name(card) if card.get('image_url') else '-'}]")

    print(f"\n{len(cards)} cards on the site, {missing} missing from collections/, {len(extras)} without a set number")
    if download:
        print(f"{downloaded} images downloaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
