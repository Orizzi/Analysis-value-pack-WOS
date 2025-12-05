# Gameplay Guide – Using Pack Value & Rankings

## Who this is for
Players who want to decide which Whiteout Survival packs are “worth it,” compare pack types fairly, and use the outputs (JSON or Pack Explorer) to plan spending.

## How the model works (no code)
- Each pack is converted into a total “value” based on its items. Every item has a base value (see `config/item_values.yaml`), and pack totals are summed from those values.
- Packs get an inferred price: from the sheet/CSV if present, otherwise inferred using store hints, `gem_value_per_usd`, and snapping to common price tiers (USD/EUR).
- The key metric is **value per dollar** (or euro): `total_value / price`. Higher is better.
- Rankings add simple scores (overall and category-focused) so you can see “best overall” or “best shard/speedup/VIP” packs.
- A budget planner can suggest which packs to buy under a budget: `wos-pack-value plan --site-dir site_data --budget 50 --currency EUR` (after running the pipeline with analysis).

## Reading the exports / Pack Explorer
- Important fields in Pack Explorer:
  - **Price**: inferred or provided store price.
  - **Total value**: summed item value.
  - **Value per dollar**: total_value / price.
  - **Ranks**: overall rank; category ranks (e.g., shards, VIP, crystals) when available.
  - **Category scores**: how strong the pack is for a focus category.
- Overall ranking = sorted by value per dollar (with a score cap). Category rankings = “best for shards/speedups/etc.”
- **is_reference** means the sheet/table was a library/lookup, not a buyable pack; usually hidden by default.

## Practical scenarios
- **I care about shards/heroes:** choose the shard-focused ranking or filter by shard category and pick top ranks.
- **I have a monthly budget:** sort by value per dollar, enable “top N,” and pick from the top list.
- **I only buy small packs (e.g., 5.99€):** filter by price range (via Pack Explorer search/filters) and then sort by value per dollar.
- **I care about VIP/long-term strength:** look at VIP-focused ranks/scores; check overall rank as a secondary metric.
- **I have a fixed budget:** run the budget planner to get a shortlist (it picks top value-per-dollar packs greedily within your budget).
- **Use player profiles:** try `wos-pack-value analyze --profile f2p` for profile-focused ranks or `wos-pack-value plan --profile f2p --budget ...` to bias recommendations toward your priorities (profiles live in `config/player_profiles.yaml`).

## Limitations & caveats
- Values depend on assumptions in `config/item_values.yaml`, tier hints, and `gem_value_per_usd`.
- Time-gated effects, event synergies, opportunity costs, and subjective preferences aren’t fully captured.
- Rankings are a guide, not absolute truth—tweak configs if your priorities differ.
- Validation runs after the pipeline; if something looks off, check `site_data/validation_report.json` and the logs for anomalies.

## Keeping it up to date
- When the game changes (new packs/items/balance), refresh data and configs:
  - Update raw sheets/screenshots in `data_raw/` (or screenshots for OCR) and rerun the pipeline.
  - Adjust item values/tiers in `config/item_values.yaml` (and `config/analysis.yaml` for weighting) and rerun analysis.
- Regenerate exports with `wos-pack-value run --with-analysis ...`; Pack Explorer will read the new JSON automatically.
