# PokeQuant v1.0 Roadmap – **Supabase Edition**  
_Complete, copy-paste-ready plan for Cursor_

This is the **same deliverable-oriented roadmap** you approved earlier, but updated to match the stack you already use for the eBay scraper:

| Layer               | Original Plan | **Updated Plan** |
|---------------------|---------------|------------------|
| Database            | Local/Postgres| **Supabase Postgres (same cluster as `ebay_sold_listings`)** |
| ORM / Client        | SQLAlchemy    | **`supabase-py` (async)** or Supabase REST/RPC |
| Auth / Security     | n/a           | Supabase service key + RLS (optional) |
| Hosting             | Docker        | Docker **or** Supabase Edge Functions (future) |

> **Conceptual change:** Wherever the old roadmap said “PostgreSQL + SQLAlchemy,” substitute **Supabase + `supabase-py`**.  
> Everything else—ETL flow, metrics, FastAPI—remains identical.

---

## Phase 0 — Project Scaffolding (½ day)

| Step | Description | Start Signal | Done Signal | Test Path |
|------|-------------|--------------|-------------|-----------|
|0.1|Create repo (`pokequant/`) with Poetry or PDM|none|`pyproject.toml`, CI job|`poetry run pytest -q` → 0 failures|
|0.2|Add `.env.example` (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `OPENAI_API_KEY`)|repo ready|Committed file + README setup|`cp .env.example .env && pytest` still green|

---

## Phase 1 — **Supabase Data Layer** (1 day)

| Step | Description | Start Signal | Done Signal | Test Path |
|------|-------------|--------------|-------------|-----------|
|1.1|Define schema in Supabase SQL editor:<br>• `products` (uuid PK, …)<br>• `prices` (uuid PK, product_id FK, date, price, source)<br>• `analyses` (uuid PK, product_id FK, metrics JSONB, created_at)|scaffold complete|Tables visible in Supabase|Insert row via SQL console succeeds|
|1.2|Generate typed client:<br>`supabase-py` helpers + Pydantic models (`get_product`, `upsert_prices`)|schema done|`supabase_client.py`|`pytest tests/supa_dal_test.py` writes/reads|
|1.3|Add **freshness checker** (`needs_refresh(product_id, max_age_days)`) using Supabase SELECT MAX(date)|client ready|`utils/freshness.py`|Unit test: 1-day data → `False`; 8-day → `True`|

---

## Phase 2 — Scraper Adapters (3-4 days)

| Step | Description | Start Signal | Done Signal | Test Path |
|------|-------------|--------------|-------------|-----------|
|2.1|Refactor **eBay scraper** into `scrapers/ebay.py` (`EbayScraper.fetch`) returning `[{date, price}]`|legacy script|file exists|Run on “Charizard 151” → ≥ 1 record|
|2.2|Refactor **PriceCharting scraper** (`scrapers/pricecharting.py`)|legacy script|file exists|Unit test length > 0|
|2.3|**Price Ingest Service**: `ingest_prices(product_id)` → freshness check → scrape (if stale) → `upsert_prices()` to Supabase|adapters ready|`services/ingest.py`|`python -m services.ingest Charizard_151` → rows ↑ in Supabase|

---

## Phase 3 — Quant Engine (2-3 days)

| Step | Description | Start Signal | Done Signal | Test Path |
|------|-------------|--------------|-------------|-----------|
|3.1|Implement metrics (`cagr`, `volatility`, `max_drawdown`, Sharpe-lite) in `metrics.py` (pure pandas)|prices in DB|file exists|Synthetic tests match hand-calc|
|3.2|**Analysis Runner** `analyze(product_id)` → returns dict; store in `analyses` table|metrics done|`services/quant.py`|Run on “Charizard 151” → JSON with keys|
|3.3|Cache logic: re-run within 1 h hits cache (no extra scrape)|runner done|cache works|Log “cached” message|

---

## Phase 4 — LLM Insight Generator (1-2 days)

| Step | Description | Start Signal | Done Signal | Test Path |
|------|-------------|--------------|-------------|-----------|
|4.1|Write prompt (`prompts/insight.md`) that consumes metrics + returns Buy/Hold/Avoid + 2-sentence rationale|analysis dict|file exists|Manual review|
|4.2|Implement `generate_insight(analysis_dict)` with OpenAI SDK|prompt ready|`services/insight.py`|Mock metrics → non-empty string|
|4.3|Guard flag `LLM_ENABLED` for cost control|function done|env-switch works|Flag off → “LLM disabled”|

---

## Phase 5 — Public Interface (2-3 days)

| Step | Description | Start Signal | Done Signal | Test Path |
|------|-------------|--------------|-------------|-----------|
|5.1|FastAPI app `main.py` with route `GET /pokequant/{product_slug}` (ingest → analyze → insight)|services ready|endpoint live|`curl localhost:8000/...` → JSON|
|5.2|CLI wrapper `cli.py` (`python -m cli Charizard_151 --no-llm`)|endpoint live|file exists|Metrics table prints in terminal|
|5.3|Integration tests via `pytest-asyncio` hitting FastAPI|endpoint stable|`tests/integration_test.py`|`pytest -m integration` passes|

---

## Phase 6 — Packaging & Docs (1 day)

| Step | Description | Start Signal | Done Signal | Test Path |
|------|-------------|--------------|-------------|-----------|
|6.1|**Dockerfile** + `docker-compose.yml` with app only (Supabase is SaaS)|code stable|images build|`docker compose up --build` → health OK|
|6.2|README quick-start:<br>```bash<br>SUPABASE_URL=https://xyz.supabase.co<br>SUPABASE_ANON_KEY=pk_…<br>SUPABASE_SERVICE_KEY=sk_… # CI/prod only<br>OPENAI_API_KEY=…<br>```|docker builds|README renders badges|Fresh clone + quick-start works|
|6.3|Tag **v1.0.0** release; GitHub Actions green|README done|tag exists|CI passes on tag|

---

## ✅ Completion Criteria

```json
GET /pokequant/charizard_151
→
{
  "product": "Charizard 151 ETB",
  "metrics": { "cagr": 0.19, "volatility": 0.08, ... },
  "insight": "BUY — Momentum is strong…"
}
