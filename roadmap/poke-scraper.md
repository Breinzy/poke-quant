# 🧠 Pokémon TCG Scraper → Supabase Integration Roadmap

This roadmap outlines the steps to build a scraper that collects Pokémon TCG set and card data from the official site and inserts it into your Supabase database. It matches the schema provided in your eBay scraper database migration.

---

## 🧱 PHASE 1: Project Setup

### 🔹 1.1. Create Project Folder

```bash
mkdir poke-scraper && cd poke-scraper

🔹 1.2. Install Dependencies

pip install requests beautifulsoup4 supabase

🔹 1.3. Initialize Supabase Client

Create a file supabase_client.py:

from supabase import create_client

SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-or-service-key"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

🧩 PHASE 2: Scrape Pokémon Set Metadata
🔹 2.1. Target Set URLs

Each set has a pattern:

https://www.pokemon.com/us/pokemon-tcg/{series}-{set-name}

Start with:

https://www.pokemon.com/us/pokemon-tcg/sword-shield-evolving-skies

🔹 2.2. Extract Set Fields

For each set, extract and format the following fields:
Field	Type	Example
set_name	string	"Sword & Shield – Evolving Skies"
release_date	date	"2021-08-27"
series	string	"Sword & Shield"
total_cards	integer	237
base_cards	integer	203
secret_rare_count	integer	34
structure	JSON	{ "V": 18, "VMAX": 15, ... }
products	JSON	[{"name": "Booster Box", "msrp_usd": 144}]
known_pull_rates	JSON	{ "VMAX": "1 per 12 packs" }
rarity_breakdown	JSON	{ "Common": 70, "Rare": 45, ... }
🃏 PHASE 3: Scrape Cards in Set

Each card should extract:
Field	Type	Example
card_name	string	"Rayquaza VMAX"
card_number	string	"195/203"
set_name	string	"Evolving Skies"
rarity	string	"Ultra Rare"

Store this as a list of dictionaries to prepare for batch insert.
🔁 PHASE 4: Insert into Supabase
🔹 4.1. Insert Set Data

supabase.table("pokemon_sets").insert([set_dict]).execute()

🔹 4.2. Insert Card Data

supabase.table("pokemon_cards").insert(cards_list).execute()

    ⚠️ Use batching (e.g., 25–50 records at a time) to avoid hitting Supabase rate limits.

📦 PHASE 5: Multi-Set Support

Create a file sets.json with known metadata for each modern set:

[
  {
    "url": "https://www.pokemon.com/us/pokemon-tcg/sword-shield-evolving-skies",
    "release_date": "2021-08-27",
    "series": "Sword & Shield"
  },
  {
    "url": "https://www.pokemon.com/us/pokemon-tcg/sword-shield-fusion-strike",
    "release_date": "2021-11-12",
    "series": "Sword & Shield"
  }
]

Iterate over each entry to populate your full catalog.

Suggested sets to support:

🗡️ Sword & Shield Era (Eighth Generation)

    Sword & Shield (Base)

    Rebel Clash

    Darkness Ablaze

    Champion’s Path (extra set)

    Vivid Voltage

    Shining Fates (extra set)

    Battle Styles

    Chilling Reign

    Evolving Skies

    Celebrations (extra set)

    Fusion Strike

    Brilliant Stars

    Astral Radiance

    Pokémon GO (extra set)

    Lost Origin

    Silver Tempest

    Crown Zenith (extra set)

🌸 Scarlet & Violet Era (Ninth Generation)

    Scarlet & Violet (Base)

    Paldea Evolved

    Obsidian Flames

    Scarlet & Violet 151 (extra set)

    Paradox Rift

    Paldean Fates (extra set)

    Temporal Forces

    Twilight Masquerade

    Shrouded Fable (extra set)

    Stellar Crown

    Surging Sparks

    Prismatic Evolutions (extra set)

    Journey Together

    Destined Rivals

    Black Bolt & White Flare (extra set)

✅ Final Project Structure

poke-scraper/
├── supabase_client.py
├── scrape_sets.py
├── utils/
│   ├── parse_cards.py
│   └── rarity_counter.py
├── data/
│   ├── evolving_skies.json
│   └── all_cards.csv
└── sets.json

🔜 BONUS PHASE (Optional Improvements)

    ✅ Add CLI tool to scrape a single set or all

    ✅ Add logging and error handling for failed inserts

    ✅ Use CRON jobs or GitHub Actions to auto-update

    ✅ Include card images and external links (TCGPlayer, eBay)

    ✅ Cross-link eBay pricing data using card_number + set_name