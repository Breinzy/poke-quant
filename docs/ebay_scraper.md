# 🕵️‍♂️ ebay_scraper Architecture (v3) - Targeted Approach

This module scrapes sold listings from eBay for specific cards by querying your database first, then generating targeted searches. This ensures clean data linkage and precise tracking.

---

## 📁 Folder Structure

```
ebay_scraper/
├── scrape_ebay.py            # Main entry point – runs the scraper loop
├── ebay_search.py            # Handles eBay search URLs + pagination ✅
├── ebay_parser.py            # Parses raw titles into structured card data ✅
├── card_selector.py          # Selects cards to track from database
├── search_generator.py       # Generates targeted search terms for specific cards
├── ebay_to_supabase.py       # Upload logic + deduplication
├── filters.json              # Search presets (keywords, grading, sets) ✅
├── utils.py                  # Date handling, batching, retries ✅
├── data/
│   └── raw_html/             # (Optional) Saved HTMLs for debugging ✅
│   └── logs/                 # JSON or CSV logs of scraped items ✅
```

---

## 🧠 Data Flow (Corrected)

```
pokemon_cards DB → card_selector.py → search_generator.py
                                    ↓
                  eBay Targeted Search → ebay_search.py ✅
                                    ↓
                  Parse Listings → ebay_parser.py ✅
                                    ↓
                  Store with card_id → ebay_to_supabase.py
                                    ↓
                  Supabase: ebay_sold_listings (with FK)
```

---

## 🧾 Output Table: `ebay_sold_listings` (Updated)

| Column          | Type        | Description                                  |
|-----------------|-------------|----------------------------------------------|
| `card_id`       | INTEGER     | **FK to pokemon_cards.id** (Direct link!)   |
| `title`         | TEXT        | Raw eBay title                               |
| `price`         | DECIMAL     | Final sale price                             |
| `sold_date`     | TIMESTAMP   | Sold date/time                               |
| `condition`     | VARCHAR     | "Raw", "PSA 10", "NM", etc.                  |
| `is_graded`     | BOOLEAN     | True if explicitly graded                    |
| `grading_company` | VARCHAR  | PSA / BGS / CGC                              |
| `grade`         | VARCHAR     | "10", "9", etc.                              |
| `image_url`     | TEXT        | eBay image URL (optional)                    |
| `search_terms`  | TEXT        | Original query terms used                    |
| `listing_url`   | TEXT        | Direct link to sold listing                  |
| `is_auction`    | BOOLEAN     | True if it was an auction                    |
| `bids`          | INTEGER     | Auction bid count (if available)             |
| `created_at`    | TIMESTAMP   | When we scraped this listing                 |

---

## 🎯 Targeted Tracking Benefits

### ✅ **Direct Database Linkage**
- No fuzzy matching needed
- Clean foreign key relationships
- 100% accurate card identification

### ✅ **Precise Data Collection**
- Search for specific cards you care about
- Track high-value cards in your collection
- Monitor cards for investment opportunities

### ✅ **Quality Control**
- Know exactly what card each listing represents
- Avoid mismatched/garbage data
- Better price accuracy and reliability

---

## 🧩 eBay Scraper Roadmap (Updated)

Step-by-step breakdown for building the targeted `ebay_scraper` pipeline:

---

### 🔹 Phase 1: Setup & Boilerplate ✅

1. `mkdir ebay_scraper && cd ebay_scraper` ✅
2. Create core files ✅
3. Install dependencies ✅

---

### 🔹 Phase 2: Search & Fetch ✅

#### 🔁 ebay_search.py ✅

- Build eBay URLs with sold listings filter ✅
- Support pagination and price filters ✅ 
- Rate limiting and error handling ✅
- Return raw HTML content ✅

---

### 🔹 Phase 3: Parse Listings ✅

#### 🔍 ebay_parser.py ✅

- Extract titles, prices, URLs, conditions ✅
- Parse grading information (PSA/BGS/CGC + grades) ✅
- Extract card numbers and detect sets ✅
- Clean price data and handle various formats ✅

---

### 🔹 Phase 4: Targeted Card Selection (NEW)

#### 🎯 card_selector.py

- Query `pokemon_cards` table for cards to track
- Support different selection strategies:
  - High-value cards (>$X price threshold)
  - Specific sets or rarities
  - User watchlist/collection
  - Recently released cards
- Return list of cards with metadata

#### 🔍 search_generator.py

- Generate precise search terms for each card:
  ```python
  f"{card.name} {card.set_name} {card.number} pokemon card"
  ```
- Handle special cases (promos, variants)
- Support grading filters (PSA 10 only, etc.)

---

### 🔹 Phase 5: Focused Scraping & Direct Storage ✅

#### 📤 ebay_to_supabase.py (Updated) ✅

- Store listings with direct `card_id` foreign key ✅
- Batch upload with deduplication by `listing_url` ✅
- Link sales data directly to card metadata ✅
- No fuzzy matching required ✅

---

### 🔹 Phase 6: Market Summary & Analytics ✅

#### 📊 market_analyzer.py ✅

- Enhanced market summary calculations with:
  - Separate statistics for raw, PSA 9, PSA 10 conditions ✅
  - Grading premium calculations (percentage over raw) ✅
  - Market liquidity assessment (high/medium/low) ✅
  - Comprehensive price statistics per condition ✅

#### 🎯 Advanced Features ✅

- Bulk market summary updates for all cards ✅
- Market insights generation (top opportunities) ✅
- Investment scoring with multiple factors ✅
- Automated summary updates after scraping ✅

#### 🗄️ Enhanced Database Schema ✅

- Direct `card_id` foreign keys (UUID support) ✅
- Search strategy tracking (`raw_nm`, `psa_9`, `psa_10`) ✅
- Condition categorization (`raw` vs `graded`) ✅
- Numeric grade storage for sorting ✅
- Performance indexes for fast queries ✅

---

### 🔹 Phase 7: Automation & Scheduling

- CLI interface for different tracking modes
- Automated runs for portfolio monitoring
- Alerts for price movements

---

## ✅ Final Result

A precise, reliable pricing database where every eBay sale is directly linked to a specific card in your metadata, enabling:

- **Accurate price tracking** for your collection
- **Investment analysis** with clean historical data  
- **Portfolio monitoring** with real-time alerts
- **Market insights** for specific cards/sets
