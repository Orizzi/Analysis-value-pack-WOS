# Pack Explorer (frontend)

Static, JS-driven view that reads `site_data/` JSON exports and lets players browse, filter, and rank packs.

## Expected inputs
- `site_data/packs.json` – main pack data (from `wos-pack-value run --with-analysis`).
- `site_data/pack_ranking_overall.json` – overall ranking output.
- `site_data/pack_ranking_by_category.json` – per-category rankings.

## Files
- `pack_explorer/pack_explorer.html` – drop into your static site.
- `pack_explorer/pack_explorer.js` – data loading, filtering, rendering.
- `pack_explorer/pack_explorer.css` – minimal scoped styles.

## Usage
1) Regenerate JSON with analysis:
   ```bash
   wos-pack-value run --raw-dir data_raw --with-analysis
   ```
   or analyze existing exports:
   ```bash
   wos-pack-value analyze --site-dir site_data
   ```
2) Serve `pack_explorer.html` from the repo root (or copy files into your site).
3) If JSON lives elsewhere, set `window.PACK_EXPLORER_BASE` before loading `pack_explorer.js`:
   ```html
   <script>window.PACK_EXPLORER_BASE = "/static/site_data/";</script>
   <script src="/static/pack_explorer.js"></script>
   ```

## Features
- Filters: search, exclude reference, top-N toggle, category focus.
- Sorting: rank overall, value per dollar, price, direction toggle.
- Detail modal: items, values, category scores, reference flag.
- Category dropdown is populated from `pack_ranking_by_category.json`.
- For player-facing tips on using rankings, see `docs/GAMEPLAY_GUIDE.md`.

## Integration notes
- Vanilla JS; no build step required.
- Styles are scoped with `pe-` classes to reduce collisions.
- All rendering mounts inside `#pack-explorer-root`; embed where you need.

## Extending
- Adjust default base path: set `window.PACK_EXPLORER_BASE`.
- Add new sort options by extending the `pe-sort` `<select>` and logic in `applyFiltersAndSort`.
- Hook your own analytics by listening to button clicks or extending `pack_explorer.js`.
