# 📚 poke_scraper — Pokémon TCG API Integration

This module loads Pokémon TCG metadata (sets and cards) into Supabase using the [Pokémon TCG API](https://pokemontcg.io). It replaces fragile HTML scraping with a more robust, scalable, and cleanly structured approach.

---

## 🎯 Goals

- Pull all modern Pokémon TCG sets (Sword & Shield, Scarlet & Violet, etc.)
- Insert or upsert each set into the `pokemon_sets` table
- Pull every card from each set and insert into the `pokemon_cards` table
- Normalize and enforce integrity (`card_number + set_name` uniqueness)
- Cache the API responses to avoid redundant downloads

---

## 📁 Folder Structure

```
poke_scraper/
├── api_sets.py               # Main API client + fetch logic
├── sync_to_supabase.py       # Pushes parsed sets/cards into Supabase
├── constants.py              # Maps series names, aliases, and metadata
├── utils.py                  # Shared formatting or ID logic
├── data/
│   ├── sets_cache.json       # Cached API response for sets
│   ├── cards_{set_id}.json   # Cached cards per set
```

---

## 🔌 Supabase Targets

### Table: `pokemon_sets`

| Field             | Type     |
|------------------|----------|
| set_name          | string   |
| release_date      | date     |
| series            | string   |
| total_cards       | int      |
| base_cards        | int      |
| secret_rare_count | int      |
| structure         | JSONB    |
| products          | JSONB    |
| known_pull_rates  | JSONB    |
| rarity_breakdown  | JSONB    |

---

### Table: `pokemon_cards`

| Field         | Type   |
|---------------|--------|
| card_name     | string |
| card_number   | string |
| set_name      | string |
| rarity        | string |

---

## 🧠 Roadmap to Set It Up

### 🔹 1. Setup environment

```bash
pip install requests python-dotenv supabase
```

Add your `.env`:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

---

### 🔹 2. Fetch and cache sets

In `api_sets.py`:

```python
GET https://api.pokemontcg.io/v2/sets
```

- Save to `data/sets_cache.json`
- Extract:
  - `id`, `name`, `releaseDate`, `total`, `printedTotal`, `series`

---

### 🔹 3. Fetch and cache cards per set

For each set:

```python
GET https://api.pokemontcg.io/v2/cards?set.id={set_id}
```

- Save to `data/cards_{set_id}.json`
- Extract card fields:
  - `name`, `number`, `rarity`, `set.name`, `set.series`

---

### 🔹 4. Normalize and insert into Supabase

In `sync_to_supabase.py`:
- Parse cached files
- Build rarity breakdown and card structure
- Insert into `pokemon_sets` (upsert by `set_name`)
- Insert into `pokemon_cards` (upsert by `card_number + set_name`)

Use batching to avoid hitting rate limits.

---

## 🛡️ Data Quality

- Rarities are standardized via `constants.py` mapping
- Use `utils.py` to slugify `set_name`, deduplicate cards, and map types
- Respect Supabase constraints (e.g., foreign key from `pokemon_cards` to `pokemon_sets`)

---

## 🧪 Optional CLI

Add a script:

```bash
python api_sets.py --sync
```

Flags:
- `--skip-cache`
- `--only-set sv6`
- `--dry-run`

---

## ✅ Final Outcome

- All Pokémon TCG metadata is loaded and normalized
- Fully linked to your eBay price data
- Ready for use in `quant/` feature generation and modeling

