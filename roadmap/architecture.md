# 🧱 eBay Scraper Architecture for Cardfolio

A scalable, standalone service for scraping eBay listings (sold + active), storing results, and serving market data to the Cardfolio app.

---

## 📁 File & Folder Structure

```
ebay-scraper/
│
├── src/
│   ├── config/
│   │   └── index.ts              # Global configs (API keys, constants)
│   │
│   ├── utils/
│   │   └── logger.ts             # Logging helper (Winston or console)
│   │   └── rateLimiter.ts        # Request throttling control
│   │
│   ├── services/
│   │   └── ebayFetcher.ts        # Core fetch logic for sold/active listings
│   │   └── parser.ts             # Extracts relevant fields from HTML or API response
│   │   └── database.ts           # Supabase/DB write helpers
│   │   └── alertService.ts       # Checks pricing triggers, sends webhook/email
│   │
│   ├── schedulers/
│   │   └── index.ts              # Cron or node-cron entrypoint
│   │   └── productSync.ts        # Periodic task to sync product prices
│   │   └── alertCheck.ts         # Periodic task to evaluate alert triggers
│   │
│   ├── api/
│   │   └── index.ts              # REST/GraphQL API entrypoint (if needed)
│   │   └── getLatest.ts          # GET endpoint: latest market price for card
│   │   └── getHistory.ts         # GET endpoint: price history
│   │
│   ├── types/
│   │   └── ebay.types.ts         # Types for listing data, prices, alerts
│   │   └── db.types.ts           # Types for DB interactions
│   │
│   └── index.ts                  # Entrypoint for manual runs
│
├── scripts/
│   └── testRun.ts                # Manual test for one-off fetch
│
├── .env                          # Environment variables (API keys, Supabase URL)
├── package.json
└── tsconfig.json
```

---

## 🔧 What Each Part Does

### `config/`

* Centralized configs (e.g., request intervals, retry logic, scraper options, Supabase keys).

### `utils/`

* Shared helpers:

  * `logger.ts`: Standard logging for all services.
  * `rateLimiter.ts`: Ensures scraping doesn’t exceed eBay or proxy limits.

### `services/`

* **ebayFetcher.ts**
  Fetches sold and active listings from eBay using:

  * Public search + filters (`site.ebay.com/sch/…`)
  * (Optional) eBay Partner Network API

* **parser.ts**
  Parses response:

  * Title, condition, price, shipping, date sold
  * Normalizes card names + trims variants

* **database.ts**

  * Inserts new listings into a `scraped_listings` table
  * Updates `products` with average/lowest prices
  * Sends updates to Cardfolio if data is stale

* **alertService.ts**

  * Matches watchlist entries against new scraped prices
  * Sends webhook/email notifications

### `schedulers/`

* Uses `node-cron` or deployed Cloud Functions/VPS scheduler.

  * `productSync.ts`: Runs every 6–12 hours, updates product market values.
  * `alertCheck.ts`: Evaluates if any alerts are triggered.

### `api/`

* Optional internal API if you want Cardfolio to fetch directly from here.

  * `/getLatest?cardId=xyz`
  * `/getHistory?productId=abc`

### `types/`

* TypeScript types for scraper models and DB rows.

### `scripts/`

* `testRun.ts`: Script to run the scraper on a sample product or keyword.

---

## 🌐 Where State Lives

### 🔄 Transient State (in-memory)

* Each fetch cycle maintains:

  * Raw HTML/text
  * Parsed listings array
  * Temporary pricing aggregates

### 🧹 Persistent State (Supabase or DB)

* `scraped_listings` table:

  * `id`, `title`, `price`, `condition`, `sold_at`, `url`, `is_active`
* `product_prices` table:

  * `product_id`, `avg_price`, `lowest_price`, `last_updated`
* `watchlist_alerts` table:

  * `user_id`, `product_id`, `trigger_type`, `target_price`, `last_notified`

---

## 🔗 How Services Connect

```
[SCHEDULER] --> [ebayFetcher] --> [parser] --> [database]
                                          ↳ [alertService] --> [notifications]
                                          ↳ [API layer] (optional)
```

* Scheduler initiates scrapes.
* `ebayFetcher` grabs raw data.
* `parser` cleans and structures listings.
* `database` inserts listings and updates product pricing.
* `alertService` evaluates and fires alerts.
* API endpoints can optionally serve this to Cardfolio in real-time.

---

## 🧱 Deployment Recommendations

* Use a **separate VPS** (like Hetzner or Fly.io) for continuous scraping.
* Avoid Vercel for long-running cron jobs or Puppeteer.
* Deploy a Node server or Docker container.

---

## 🧠 Optional Features for Later

* 🔍 **Image-based product matching**
  Match scraped listings to a known card by analyzing image (not just text).

* 📈 **Price history dashboard**
  Store daily price snapshots per card for long-term analysis.

* 🧼 **Listing deduplication**
  Auto-remove reposted or duplicate listings using image hashes or title similarity.

* 📊 **Market snapshot exports**
  Allow premium users to download current pricing or trend data.
