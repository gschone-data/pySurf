# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

pySurf is a static surf-forecast dashboard generator. It scrapes surf-forecast.com for multiple
French Atlantic-coast regions, picks the best-rated spot per time slot, and renders one static HTML
page per region into `_site/`. A GitHub Actions workflow runs it every 3 hours and on each push to
`main`, deploying `_site/` to GitHub Pages.

There is no server and no runtime backend — the deployed product is the generated static HTML/CSS.

## Commands

```bash
pip install -r requirements.txt   # deps: requests, bs4, jinja2, pandas
python main.py                    # scrape all regions and regenerate _site/*.html + styles.css
```

`python main.py` performs live HTTP requests to surf-forecast.com for every spot in every region
(~38 spots), so a full run is slow and network-dependent. There is no test runner configured;
`test/res_fin.csv` is sample scraped output, not a test suite.

## Pipeline (data flow)

The render is a three-stage pipeline, one module per stage:

1. `webscrapping/load_data_f.py` — `load_data(spot)` scrapes a single spot's six-day forecast page
   and returns a per-slot DataFrame. It parses the surf-forecast HTML table by `data-row-name`
   attributes (`days`, `time`, `wave-height`, `periods`, `wind`, `wind-state`) plus `star-rating`
   divs. Row lengths are reconciled with `pad_or_truncate`/truncation because the source columns are
   not always equal length. Network/parse failures return an empty DataFrame (logged, not raised).

2. `webscrapping/load_data_all.py` — `load_data_all(spots)` concatenates all spots, normalizes
   `rating` (`'!'` → -1 meaning saturated/unavailable, non-numeric → 0), reconstructs absolute
   calendar dates from bare day numbers via `build_date_sequence` (handles month rollover), maps the
   French time-of-day label to an hour via `TIME_MAPPING`, builds a sortable `key`, then keeps only
   the **max-rated spot(s) per time slot**.

3. `main.py` — `prepare_display_dataframe` aggregates surviving rows per `(key, date, time, rating)`
   slot (joining tied spot names with `<br>`, max wave height/period, mean wind), converts ratings to
   star glyphs, and builds the HTML table. `generate_html` renders `templates/index.html` (Jinja2).
   `main()` loops `REGION_ORDER`, writes one file per region, and copies `styles.css` into `_site/`.

## Conventions that matter

- **`config.py` is the single source of truth.** Regions, their spots, region ordering, the default
  region, `TIME_MAPPING`, the scrape URL template, timeout, and `OUTPUT_DIR` all live there. To add a
  region or spot, edit `REGIONS` and `REGION_ORDER` only — nothing else hardcodes them. Spot names are
  the exact surf-forecast URL slugs (e.g. `Pointdela-Torche`, `La-Cotiniere_Ile-D-Oleron`).

- **`DEFAULT_REGION` is special**: it is written as `index.html`; every other region is written as
  `<slug>.html`. The region selector links and the output filename both branch on this.

- **Rating semantics**: `-1` = saturated/unavailable (source `'!'`), `0` = no/invalid rating. Both are
  treated as "no surf" — their spot names are blanked in the display table.

- **Scraping is structure-sensitive**: parsing depends on surf-forecast's `data-row-name` table
  markup. If the site changes its HTML, the row-finders in `load_data_f.py` are where it breaks
  (they log "Structure HTML inattendue" and return empty rather than crashing).

- Code and comments are written in French (no accents in identifiers/strings).
