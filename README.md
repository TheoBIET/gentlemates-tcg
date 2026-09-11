# Gentle Mates TCG

[![Latest release](https://img.shields.io/github/v/release/TheoBIET/gentlemates-tcg?sort=date&display_name=tag&label=release)](https://github.com/TheoBIET/gentlemates-tcg/releases/latest)
[![CI](https://github.com/TheoBIET/gentlemates-tcg/actions/workflows/ci.yml/badge.svg)](https://github.com/TheoBIET/gentlemates-tcg/actions/workflows/ci.yml)

An unofficial, open source database of every card in the Gentle Mates Trading Card Game, and the data source behind the TCG features of [matepedia.com](https://matepedia.com).

> Not affiliated with, endorsed by, or sponsored by [Gentle Mates](https://gentlemates.com).

## Use the data

| | |
| --- | --- |
| Browse the cards | [theobiet.github.io/gentlemates-tcg](https://theobiet.github.io/gentlemates-tcg/) |
| Every collection | [`all-collections.json`](https://theobiet.github.io/gentlemates-tcg/all-collections.json) |
| One collection | [`tout-commence-ici.json`](https://theobiet.github.io/gentlemates-tcg/tout-commence-ici.json) |
| One card | [`collections/tout-commence-ici/cards/016/mur-salvateur.json`](https://theobiet.github.io/gentlemates-tcg/collections/tout-commence-ici/cards/016/mur-salvateur.json) |
| Download everything | [`data.zip`](https://github.com/TheoBIET/gentlemates-tcg/releases/latest/download/data.zip) from the latest release: JSON, card images, set logos |

The site follows `main`. Releases are dated snapshots: to pin one, download `https://github.com/TheoBIET/gentlemates-tcg/releases/download/<version>/data.zip`.

Card files, images, and logos keep their repository paths under `collections/`. Each card has an `id` (the slug of its name), a `number`, and an `image` path, each collection a `logo` path, both relative to the site root or the zip. Card text is in French, as printed. See [`schemas/`](schemas/) for every field.

## Layout

```
collections/<set>/
  set.json              # name and total number of cards
  logo.svg
  cards/<number>/       # e.g. cards/016/
    <slug>.json         # card data, e.g. mur-salvateur.json
    <number>.avif       # card image, e.g. 016.avif
schemas/                # JSON Schemas for set.json and card files
scripts/
```

## Contributing

Pull requests are welcome, to add a card or fix a mistake. A photo of the card helps review.

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv run scripts/rename.py     # rename new card images to <number>.avif
uv run scripts/validate.py   # check sets and cards against the schemas
uv run scripts/generate.py   # build data/: JSON files, card images, set logos
uv run scripts/preview.py    # build data/index.html from data/
```

CI validates every pull request and deploys the site on every push to `main`.

## Releases

Releases are tagged `vYYYY.MM.DD`, e.g. `v2026.09.10`. A fix to a release keeps its date and adds a number: a typo found in `v2026.09.10` ships as `v2026.09.10.1`, then `v2026.09.10.2`. Publishing a release attaches `data.zip` to it.

## License

Scripts, schemas, and data structure: [MIT](LICENSE). Card content (names, text, artwork, images) and the Gentle Mates brand belong to [Gentle Mates](https://gentlemates.com).
