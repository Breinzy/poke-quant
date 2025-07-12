# 🧠 poke-quant Architecture Overview

This project is designed to analyze, predict, and monitor the trading performance of Pokémon TCG cards and sealed products using scraped sales data, structured metadata, and quantitative models. It is composed of three main components:

---

## 📁 Project Structure

```
poke-quant/
├── README.md
├── .env
├── supabase_client.py
│
├── ebay_scraper/
├── poke_scraper/
├── quant/
```

---

## 🔗 Shared Components

### `.env`

Holds shared environment variables such as:

```
SUPABASE_URL=
SUPABASE_KEY=
PROXY_URL=
```

### `supabase_client.py`

Provides a centralized Supabase client instance for all modules. This ensures consistent DB access patterns and credentials.

```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
```

---

## 📦 ebay_scraper/

### Purpose

Scrapes eBay sold listings, parses listing data (e.g. title, price, condition), and stores the output in Supabase tables (`ebay_sold_listings` and `ebay_market_summary`).

### Key Scripts

- `scrape_ebay.py`: Pulls recent sold listings using eBay search or third-party endpoints.
- `parse_title.py`: Extracts card metadata (name, number, grading, etc.) from messy eBay titles.
- `ebay_to_supabase.py`: Uploads parsed records to Supabase with duplicate protection and integrity enforcement.

### Output Tables

- `ebay_sold_listings`
- `ebay_market_summary`

---

## 📚 poke_scraper/

### Purpose

Pulls official Pokémon Trading Card Game metadata using the [Pokémon TCG API](https://pokemontcg.io), rather than scraping HTML. This module provides the foundational dataset for all card and set-level relationships used in pricing analysis and modeling.

---

### Key Scripts

- `api_sets.py`: Fetches set list and individual card data via the TCG API and caches locally
- `sync_to_supabase.py`: Parses cached data and inserts/upserts into Supabase
- `constants.py`: Contains standardized rarity mappings and known metadata enrichments
- `utils.py`: Handles common helpers (slugifying, rarity normalization, batching)
- `data/`: Stores local JSON files from API responses to avoid duplicate downloads

---

### Output Tables

- `pokemon_sets`: Contains metadata for each TCG expansion set
- `pokemon_cards`: Contains card-level data including name, number, rarity, and set reference

---

### Data Relationships

- Each `pokemon_card.set_name` maps to `pokemon_sets.set_name` via a foreign key
- Set names and card numbers are aligned with those used in `ebay_sold_listings`
- These relations allow the `ebay_scraper` and `quant` modules to join pricing data with clean metadata for modeling

---


---

## 📊 quant/

### Purpose

Processes structured data from both `poke_scraper` and `ebay_scraper` to generate actionable insights and predictive models.

### Key Scripts

- `build_features.py`: Joins card metadata + historical price data to generate model-ready features.
- `model.py`: Runs regression, classification, or ranking models to score card investment potential.
- `backtest.py`: Simulates buy/sell strategies using historical eBay data.
- `signal_generator.py`: Produces real-time buy/sell/hold alerts, optionally stores to a future `signals` table.

---

## 🔁 Data Flow Diagram

```
poke_scraper/      ---> pokemon_sets
                   ---> pokemon_cards
                            ↑
ebay_scraper/      ---> ebay_sold_listings
                   ---> ebay_market_summary

quant/             ---> joins all tables to create:
                            - feature sets
                            - price predictions
                            - investment signals
```

---

## 🧠 Future Expansion Ideas

- Add Discord/Telegram webhook alerts for price movements or buy signals
- Integrate sealed product tracking and restock alerting
- Create admin panel or dashboard to monitor trends
- Feed data into a public-facing app for collectors/investors

---

## ✅ Summary

Each module operates independently, but shares:

- The same Supabase backend
- The same metadata source of truth (`set_name` + `card_number`)
- A unified goal: to empower smarter decisions in the Pokémon trading card market

This modular architecture keeps scraping, storage, and modeling decoupled — allowing easy debugging, swapping of services, and clean scaling.
