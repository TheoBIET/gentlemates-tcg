"""Build data/index.html, a page showing every card image next to its JSON.

Usage:
    uv run scripts/generate.py && uv run scripts/preview.py && open data/index.html

Reads data/all-collections.json. The page markup, styles, and script live in
scripts/preview.html.
"""

import html
import json
import re
import sys
import unicodedata
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
TEMPLATE = Path(__file__).with_name("preview.html")
JSON_TOKEN = re.compile(r'("(?:\\.|[^"\\])*")(\s*:)?|\b(true|false|null)\b|(-?\d+)')

RARITIES = {
    "common": "#88888c",
    "uncommon": "#c4a674",
    "rare": "#8daeeb",
    "epic": "#8a6bf1",
    "legendary": "#f0d567",
    "promo": "#cc664a",
}
ESSENCES = {
    "pink": "#ea528f",
    "orange": "#ef7f29",
    "jade": "#3fb68f",
    "violet": "#9f8ac0",
    "yellow": "#f2c230",
    "mauve": "#b185ba",
    "green": "#5cb85c",
    "blue": "#4a78e0",
    "azure": "#3fb8e8",
    "neutral": "#a1a1a8",
}


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()


def highlight(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=4)
    parts, end = [], 0
    for match in JSON_TOKEN.finditer(text):
        string, colon, literal, number = match.groups()
        parts.append(html.escape(text[end : match.start()]))
        if string:
            parts.append(f'<span class="{"k" if colon else "s"}">{html.escape(string)}</span>{colon or ""}')
        else:
            parts.append(f'<span class="{"l" if literal else "n"}">{literal or number}</span>')
        end = match.end()
    return "".join(parts) + html.escape(text[end:])


def badge(text: str, css: str = "", color: str = "") -> str:
    style = f' style="--c: {color}"' if color else ""
    dot = "<i></i>" if css == "essence" else ""
    return f'<span class="badge {css}"{style}>{dot}{html.escape(text)}</span>'


def render_card(card: dict, collection: dict) -> tuple[str, str]:
    """Return the card section and its search result."""
    rarity, color = card["rarity"].capitalize(), RARITIES.get(card["rarity"], "#88888c")
    types = [card["type"], card["subtype"]] if "subtype" in card else [card["type"]]
    badges = [
        badge(rarity, "tinted", color),
        *(badge(value.capitalize()) for value in types),
        badge(f"{card['essence'].capitalize()} essence", "essence", ESSENCES.get(card["essence"], "#a1a1a8")),
    ]
    number = f"{card['number']:03}"
    source = f"collections/{collection['id']}/cards/{number}/{card['id']}.json"
    name = html.escape(card["name"])

    section = f"""
<section class="card" id="{card['id']}">
  <img class="art" src="{html.escape(card['image'])}" alt="{name}" loading="lazy">
  <div class="side">
    <div class="panel">
      <div class="badges">{"".join(badges)}</div>
      <div>
        <div class="name">{name}</div>
        <div class="sub">{html.escape(collection['name'])} · <span class="chip">{number}/{collection['total']}</span></div>
      </div>
      <div class="flavor"><em>“{html.escape(card['quote'])}”</em><small>Illus. {html.escape(card['illustrator'])}</small></div>
      <div class="label">
        <code><a href="{source}">{source}</a></code>
        <span class="actions">
          <button type="button" data-action="copy">Copy</button>
          <button type="button" data-action="expand">Expand</button>
        </span>
      </div>
      <div class="code"><pre>{highlight(card)}</pre></div>
    </div>
  </div>
</section>"""

    search = normalize(" ".join([number, card["id"], card["name"], card["illustrator"], rarity, *types, card["essence"]]))
    result = (
        f'<li data-search="{html.escape(search)}"><a href="#{card["id"]}">'
        f'<span class="chip">{number}</span><span class="result-name">{name}</span>{badges[0]}</a></li>'
    )
    return section, result


def main() -> int:
    try:
        collections = json.loads((DATA / "all-collections.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("error: data/all-collections.json not found, run scripts/generate.py first", file=sys.stderr)
        return 1

    sections, results = [], []
    for collection in collections.values():
        name = html.escape(collection["name"])
        title = f'<img src="{html.escape(collection["logo"])}" alt="{name}">' if collection["logo"] else name
        count = f'{len(collection["cards"])} / {collection["total"]}'
        sections.append(f'<h2 class="collection">{title}<span class="count">{count}</span></h2>')
        for card in collection["cards"]:
            section, result = render_card(card, collection)
            sections.append(section)
            results.append(result)

    page = TEMPLATE.read_text(encoding="utf-8")
    page = page.replace("<!-- results -->", "".join(results)).replace("<!-- cards -->", "".join(sections))
    (DATA / "index.html").write_text(page, encoding="utf-8")
    print(f"wrote data/index.html ({len(results)} cards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
