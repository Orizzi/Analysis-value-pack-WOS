# Valuation Strategy

## Overview
- Packs are valued in a unified “value” unit driven by per-item/base-category rates from `config/item_values.yaml`.
- Scores are derived from value/price ratios, scaled to 0–100, and bucketed into qualitative labels (Trash → Excellent).
- Prices are pulled from pack data when available, otherwise inferred.

## Price inference
- `pack_price_hints`: fuzzy (substring) matching from config to set a default tier when price is missing.
- `price_inference.gem_value_per_usd`: when `gem_total` is present in `pack.meta` (e.g., from spreadsheets with “Gem Total”), price is inferred as `gem_total / gem_value_per_usd`.
- `price_defaults.fallback_price`: used only if no hints or gem totals exist.
- Price source is recorded in `pack.meta["price_source"]`.

## Item value resolution
1. **Per-item override** (`items` in config) – includes optional category override.
2. **Ingested base_value** – e.g., `Gem per unit` from spreadsheets or `equivalent_gem_cost / quantity` for event-shop items.
3. **Category default** (`categories` in config) – base value × quantity × optional multiplier.

## Scoring
- Ratio → score: bounded by `valuation.ratio_scale.max_ratio`, then linearly scaled to 0–100.
- Bands (`valuation.score_bands`) map scores to labels/colors for the static site.

## Practical knobs to tune
- Adjust `items` or `categories` when community consensus shifts (e.g., shard valuation, speedups).
- Update `pack_price_hints` when a new pack’s tier is known; otherwise increase `gem_value_per_usd` to make gem-based inference more conservative.
- Add event-specific multipliers (e.g., holiday shops) by extending `categories` with contextual multipliers and tagging items accordingly.

## Data captured from current raw files
- Event shop sheets provide `Gems per token` and `Equivalent Gem Cost`; ingestion uses per-item gem-equivalent divided by quantity as `base_value`.
- Regular pack summaries provide `Gem Total`, enabling price inference when explicit USD amounts are absent.
