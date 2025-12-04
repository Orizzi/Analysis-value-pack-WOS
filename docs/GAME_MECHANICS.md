# Game Mechanics & Pack Context

Sources consulted: in-game export sheets in `data_raw/` plus high-level reference from wosnerds.com (general item lists and event tokens). Use these notes to keep valuations grounded and to update configs.

## Core currencies and items
- **Fire Crystals**: premium currency; anchors many pack valuations.
- **Gems**: secondary premium currency (often used as value proxy in spreadsheets).
- **VIP Points**: progress toward VIP perks; common filler in packs.
- **Speedups**: time reductions (5m, 1h, 3h); valued by duration.
- **Hero shards / manuals**: rarity-based (Rare/Epic/Mythic/Legendary) and event-specific shards.
- **Resources**: Food/Wood/Coal/Iron; low marginal value.
- **Event tokens**: shop currency (Arena, Alliance Championship, State of Power, etc.), priced via “Gems per token”.

## Pack roles and tiers (assumed, adjustable)
- Typical price tiers observed in Whiteout Survival and similar games: **$0.99 / $4.99 / $9.99 / $19.99 / $49.99 / $99.99**.
- “Blessing” / “Design/Charm” packs: mid-tier ($4.99–$9.99) with shards, gear materials, VIP.
- “Fire Crystal” packs: lower tiers with gems, fire crystals, speedups, and resources.
- Event shop “packs”: token-based; value expressed in gem-equivalent costs rather than USD.

## Event shop behavior
- Shops provide **Gems per token** and **Equivalent Gem Cost** in `Event Shop Item Evaluator.xlsx`.
- Tokens are limited; prioritization should focus on low gem-per-token ratios (higher value density).
- Event labels seen: Arena, Alliance Championship, Foundry, State of Power, Canyon Shop, Tundra Trading Station, Emporium of Enigma, Honor Festival.

## Item categories (for config tuning)
- `premium_currency`: Fire Crystals, Gems.
- `speedup`: duration-based.
- `vip`: VIP points.
- `shard`: hero shards/manuals (rarity multipliers can be added).
- `resource`: food/wood/coal/iron.
- `gear/charm materials`: design plans, polishing solution, hardened alloy, etc.
- `event_token_goods`: items purchasable with tokens; priced via gem-per-token.

## How to extend
- When new event shops appear, log their token rate (gems per token) into `config/item_values.yaml` or per-item overrides.
- If a pack has a novel price tier, add a `pack_price_hints` entry or update the inference section to avoid 0-price valuations.
- For skins/cosmetics, add a category with a multiplier (often high subjective value).
