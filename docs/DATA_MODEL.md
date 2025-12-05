# Data Model

## Pack
- `pack_id` (str) – slugified identifier (pack name + price + source).
- `name` (str)
- `price` (float)
- `currency` (str, default USD)
- `source_file` (str), `source_sheet` (str|None)
- `is_reference` (bool) - reference/library blocks rather than purchasable packs.
- `tags` (list[str])
- `items` (list[`PackItem`])
- `notes` (str|None)
- `meta` (dict) - free-form, e.g., event name.

## PackItem
- `item_id` (str) – slugified from name.
- `name` (str)
- `quantity` (float)
- `category` (str) - e.g., premium_currency, speedup, shard, resource.
- `icon` (str|None) - path in `images_raw/` when extracted.
- `base_value` (float|None)
- `source_row` (int|None) - Excel row used during ingestion.
- `meta` (dict) - may include `token_cost`, `equivalent_gem_cost`, `row_total`, `valuation_category`.

## ItemDefinition
- `item_id` (str)
- `name` (str)
- `category` (str)
- `icon` (str|None)
- `base_value` (float|None)
- `description` (str|None)
- `meta` (dict)

## PackValuation
- `pack_id` (str)
- `total_value` (float) - summed item values after multipliers.
- `price` (float)
- `ratio` (float) - `total_value / price` (0 if price is 0).
- `score` (float) - 0-100, bounded by `valuation.ratio_scale.max_ratio`.
- `label` (str) - qualitative bucket from `valuation.score_bands`.
- `color` (str) - hex string aligned to label.
- `breakdown` (dict[str, float]) - item_id → item value.
- `meta` on Pack captures optional derived fields:
  - `gem_total` (float) - pulled from spreadsheets’ “Gem Total” rows.
  - `pack_pct` / `true_pack_value_pct` - optional summary percentages.
  - `price_source` - `pack`, `hint:*`, `gem_total`, or `fallback`.

## JSON export shapes

### `data_processed/packs.json`
```json
{
  "generated_at": "ISO timestamp",
  "packs": [Pack...]
}
```

### `data_processed/items.json`
```json
{
  "generated_at": "ISO timestamp",
  "items": [ItemDefinition...]
}
```

### `data_processed/valuations.json`
```json
{
  "generated_at": "ISO timestamp",
  "config": { ... },
  "packs": [Pack...],
  "valuations": [PackValuation...]
}
```

### `site_data/packs.json`
```json
{
  "generated_at": "ISO timestamp",
  "packs": [
    {
      "id": "starter-pack-4-99-sample",
      "name": "Starter Pack",
      "price": {"amount": 4.99, "currency": "USD"},
      "source": {"file": "data_raw/sample.csv", "sheet": null},
      "tags": [],
      "items": [{"id": "fire-crystal", "name": "Fire Crystal", "quantity": 300, "category": "premium_currency", "icon": null, "value": 300.0}],
      "value": 320.0,
      "price_to_value": 64.1,
      "score": 100.0,
      "label": "Excellent",
      "color": "#00a388"
    }
  ]
}
```

### `site_data/items.json`
```json
{
  "generated_at": "ISO timestamp",
  "items": [ItemDefinition...]
}
```
