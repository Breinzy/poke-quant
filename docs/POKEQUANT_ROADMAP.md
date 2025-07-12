# PokeQuant Tool Roadmap
**Building Quantitative Analysis on Existing eBay + PriceCharting Infrastructure**

---

## 🎯 **Overview**

The PokeQuant tool will provide quantitative analysis for Pokemon cards and sealed products by:
1. **Data Freshness Check**: Verify if we have up-to-date pricing data
2. **Intelligent Data Collection**: Auto-trigger eBay + PriceCharting scrapers when needed
3. **Quantitative Analysis**: Calculate financial metrics (CAGR, volatility, Sharpe ratio, etc.)
4. **Actionable Insights**: Generate buy/hold/sell recommendations

**Input**: Card name or sealed product name  
**Output**: Comprehensive financial analysis with metrics and recommendations

---

## 📊 **Current Infrastructure Assets**

### Database (Supabase)
- ✅ `pokemon_cards` & `pokemon_sets` (metadata)
- ✅ `ebay_sold_listings` & `ebay_sealed_listings` (pricing data)
- ✅ `sealed_products` (product catalog)

### Scrapers  
- ✅ `ebay_search.py` + `ebay_parser.py` + `ebay_to_supabase.py`
- ✅ `pricecharting_scraper.py` (historical data)
- ✅ `data_preparation.py` (basic data joining)

### Infrastructure
- ✅ `supabase_client.py` (authentication & connection)
- ✅ Quality filtering and deduplication

---

## 🛠️ **Phase 1: Data Layer Enhancement** (2-3 days)

### **1.1 Create PokeQuant Database Schema**
**Start Signal**: Current database structure confirmed  
**Done Signal**: New tables created and tested  
**Test Path**: Insert sample data and verify foreign key relationships

```sql
-- New tables for PokeQuant
CREATE TABLE pokequant_products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    product_type VARCHAR NOT NULL, -- 'card' or 'sealed'
    product_id VARCHAR NOT NULL,   -- card_id or sealed_product_id
    product_name VARCHAR NOT NULL,
    set_name VARCHAR,
    last_data_update TIMESTAMP WITH TIME ZONE,
    last_analysis_run TIMESTAMP WITH TIME ZONE,
    data_quality_score DECIMAL(3,2), -- 0.00 to 1.00
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(product_type, product_id)
);

CREATE TABLE pokequant_price_series (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pokequant_product_id UUID REFERENCES pokequant_products(id),
    price_date DATE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    source VARCHAR NOT NULL, -- 'ebay', 'pricecharting'
    condition_category VARCHAR, -- 'raw', 'graded', 'sealed'
    data_confidence DECIMAL(3,2) DEFAULT 1.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(pokequant_product_id, price_date, source, condition_category)
);

CREATE TABLE pokequant_analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pokequant_product_id UUID REFERENCES pokequant_products(id),
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metrics JSONB NOT NULL, -- Store all calculated metrics
    recommendation VARCHAR, -- 'BUY', 'HOLD', 'SELL', 'AVOID'
    confidence_score DECIMAL(3,2),
    analysis_version VARCHAR DEFAULT '1.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### **1.2 Build Data Freshness Service**
**Start Signal**: Database schema ready  
**Done Signal**: `freshness_checker.py` module working  
**Test Path**: `python -m quant.freshness_checker "Charizard V 154/185"` returns freshness status

```python
# quant/freshness_checker.py
class DataFreshnessChecker:
    def __init__(self, max_age_days: int = 7):
        self.max_age_days = max_age_days
    
    def check_product_freshness(self, product_name: str, product_type: str) -> Dict:
        """Check if we have fresh data for a product"""
        return {
            'is_fresh': bool,
            'last_update': datetime,
            'days_old': int,
            'ebay_listing_count': int,
            'pricecharting_available': bool,
            'recommended_action': 'use_cache' | 'scrape_ebay' | 'scrape_both'
        }
```

### **1.3 Create Product Search & Identification Service**
**Start Signal**: Freshness service working  
**Done Signal**: `product_finder.py` can find cards and sealed products  
**Test Path**: Search for "Charizard V" returns multiple card options with set info

```python
# quant/product_finder.py  
class ProductFinder:
    def search_products(self, query: str) -> List[Dict]:
        """Search across cards and sealed products"""
        # Search pokemon_cards table
        # Search sealed_products table
        # Return unified results with type indicators
        
    def get_product_by_id(self, product_type: str, product_id: str) -> Dict:
        """Get specific product details"""
```

---

## 🔄 **Phase 2: Smart Data Collection** (3-4 days)

### **2.1 Refactor Existing Scrapers into Services**
**Start Signal**: Data layer ready  
**Done Signal**: Unified scraper services with consistent APIs  
**Test Path**: `scraper_service.collect_ebay_data(card_id=123)` returns standardized data

```python
# quant/scraper_service.py
class ScraperService:
    def collect_ebay_data(self, product_type: str, product_id: str) -> Dict:
        """Collect eBay data for any product type"""
        
    def collect_pricecharting_data(self, product_type: str, product_id: str) -> Dict:
        """Collect PriceCharting data for any product type"""
        
    def collect_all_data(self, product_type: str, product_id: str) -> Dict:
        """Orchestrate collection from all sources"""
```

### **2.2 Build Price Series Aggregator**
**Start Signal**: Scraper services ready  
**Done Signal**: `price_aggregator.py` creates clean time series  
**Test Path**: Aggregator produces daily price series with gap filling and outlier detection

```python
# quant/price_aggregator.py
class PriceSeriesAggregator:
    def aggregate_ebay_prices(self, listings: List[Dict]) -> pd.DataFrame:
        """Convert eBay listings to daily price series"""
        
    def merge_pricecharting_data(self, ebay_series: pd.DataFrame, 
                                pc_data: Dict) -> pd.DataFrame:
        """Merge eBay and PriceCharting into unified series"""
        
    def clean_and_validate(self, price_series: pd.DataFrame) -> pd.DataFrame:
        """Remove outliers, fill gaps, validate data quality"""
```

### **2.3 Create Data Collection Orchestrator**
**Start Signal**: Price aggregator working  
**Done Signal**: `data_collector.py` coordinates all data collection  
**Test Path**: `python -m quant.data_collector "Evolving Skies Booster Box"` collects fresh data

```python
# quant/data_collector.py
class DataCollector:
    def collect_product_data(self, product_name: str, force_refresh: bool = False) -> Dict:
        """Main entry point for data collection"""
        # 1. Find/identify product
        # 2. Check data freshness  
        # 3. Collect missing data
        # 4. Aggregate into price series
        # 5. Store in pokequant_price_series
        # 6. Return analysis-ready data
```

---

## 📈 **Phase 3: Quantitative Analysis Engine** (3-4 days)

### **3.1 Build Core Metrics Calculator**
**Start Signal**: Clean price series available  
**Done Signal**: `metrics_calculator.py` produces standard financial metrics  
**Test Path**: Metrics match hand-calculated values for test data

```python
# quant/metrics_calculator.py
class MetricsCalculator:
    def calculate_returns_metrics(self, price_series: pd.DataFrame) -> Dict:
        """Calculate return-based metrics"""
        return {
            'cagr': float,              # Compound Annual Growth Rate
            'total_return': float,       # Total return %
            'volatility': float,         # Annualized volatility
            'sharpe_ratio': float,       # Risk-adjusted return
            'max_drawdown': float,       # Maximum peak-to-trough loss
            'recovery_time_days': int,   # Days to recover from max drawdown
        }
    
    def calculate_market_metrics(self, price_series: pd.DataFrame) -> Dict:
        """Calculate market structure metrics"""
        return {
            'trend_strength': float,     # Price trend momentum
            'price_stability': float,    # Consistency of pricing
            'liquidity_score': float,    # Based on listing frequency
            'current_vs_peak': float,    # Current price vs all-time high
            'support_level': float,      # Estimated price floor
            'resistance_level': float,   # Estimated price ceiling
        }
```

### **3.2 Create Analysis Engine**
**Start Signal**: Metrics calculator ready  
**Done Signal**: `analysis_engine.py` produces comprehensive analysis  
**Test Path**: Analysis includes all metrics + data quality assessment + confidence scores

```python
# quant/analysis_engine.py
class AnalysisEngine:
    def run_full_analysis(self, product_name: str) -> Dict:
        """Run complete quantitative analysis"""
        return {
            'product_info': Dict,
            'data_summary': Dict,        # Data quality, date range, source breakdown
            'returns_metrics': Dict,     # From MetricsCalculator
            'market_metrics': Dict,      # From MetricsCalculator  
            'risk_assessment': Dict,     # Custom risk metrics
            'comparison_metrics': Dict,  # vs similar products, market
            'confidence_score': float,  # Overall analysis confidence
            'analysis_timestamp': datetime
        }
```

### **3.3 Add Comparative Analysis**
**Start Signal**: Basic analysis working  
**Done Signal**: Products compared against similar items and market  
**Test Path**: Charizard V cards compared against other VMAXs, Evolving Skies set average

```python
# quant/comparative_analyzer.py
class ComparativeAnalyzer:
    def compare_to_set_average(self, product_analysis: Dict) -> Dict:
        """Compare product performance to its set average"""
        
    def compare_to_similar_products(self, product_analysis: Dict) -> Dict:
        """Compare to similar rarity/type products"""
        
    def calculate_market_position(self, product_analysis: Dict) -> Dict:
        """Determine relative market position (top/middle/bottom performers)"""
```

---

## 🤖 **Phase 4: Intelligence Layer** (2-3 days)

### **4.1 Create Recommendation Engine**
**Start Signal**: Analysis engine producing results  
**Done Signal**: `recommendation_engine.py` generates actionable recommendations  
**Test Path**: Engine produces BUY/HOLD/SELL with reasoning for different scenarios

```python
# quant/recommendation_engine.py
class RecommendationEngine:
    def generate_recommendation(self, analysis: Dict) -> Dict:
        """Generate buy/hold/sell recommendation"""
        return {
            'recommendation': str,       # 'BUY', 'HOLD', 'SELL', 'AVOID'
            'confidence': float,         # 0.0 to 1.0
            'reasoning': List[str],      # Bullet points explaining decision
            'target_buy_price': float,   # Suggested buy-in price
            'target_sell_price': float,  # Suggested exit price
            'risk_level': str,          # 'LOW', 'MEDIUM', 'HIGH'
            'time_horizon': str,        # 'SHORT', 'MEDIUM', 'LONG'
        }
    
    def create_investment_thesis(self, analysis: Dict, recommendation: Dict) -> str:
        """Generate human-readable investment thesis"""
```

### **4.2 Add LLM Insight Generation (Optional)**
**Start Signal**: Recommendation engine working  
**Done Signal**: GPT integration provides natural language insights  
**Test Path**: LLM generates coherent 2-3 sentence investment summary

```python
# quant/llm_insights.py  
class LLMInsightGenerator:
    def generate_insights(self, analysis: Dict, recommendation: Dict) -> str:
        """Use GPT to generate natural language insights"""
        # Build prompt with analysis data
        # Call OpenAI API
        # Return formatted insights
```

### **4.3 Create Analysis Caching System**
**Start Signal**: Recommendation engine ready  
**Done Signal**: Results cached in `pokequant_analyses` table  
**Test Path**: Subsequent requests return cached results if data is fresh

```python
# quant/analysis_cache.py
class AnalysisCache:
    def get_cached_analysis(self, product_id: str, max_age_hours: int = 1) -> Optional[Dict]:
        """Retrieve recent analysis from cache"""
        
    def store_analysis(self, product_id: str, analysis: Dict) -> bool:
        """Store analysis results in database"""
        
    def invalidate_cache(self, product_id: str) -> bool:
        """Force cache refresh for product"""
```

---

## 🚀 **Phase 5: User Interface** (2-3 days)

### **5.1 Build CLI Interface**
**Start Signal**: Analysis engine complete  
**Done Signal**: Command-line tool working  
**Test Path**: `python -m pokequant "Charizard V 154/185"` returns formatted analysis

```bash
# Example CLI usage
python -m pokequant "Charizard V 154/185"
python -m pokequant "Evolving Skies Booster Box" --force-refresh
python -m pokequant "Charizard" --search  # Show search results
```

### **5.2 Create FastAPI Web Service**
**Start Signal**: CLI working  
**Done Signal**: REST API with OpenAPI docs  
**Test Path**: `GET /api/v1/analysis/charizard-v-154-185` returns JSON analysis

```python
# api/main.py
from fastapi import FastAPI

app = FastAPI(title="PokeQuant API")

@app.get("/api/v1/analysis/{product_slug}")
async def get_analysis(product_slug: str, force_refresh: bool = False):
    """Get quantitative analysis for a product"""
    
@app.get("/api/v1/search/{query}")  
async def search_products(query: str):
    """Search for products"""
```

### **5.3 Add Monitoring & Health Checks**
**Start Signal**: API working  
**Done Signal**: Health endpoints and basic monitoring  
**Test Path**: `GET /health` returns system status and data freshness

```python
@app.get("/health")
async def health_check():
    """System health and data freshness check"""
    return {
        'status': 'healthy',
        'database_connection': bool,
        'scraper_status': dict,
        'cache_status': dict,
        'data_freshness': dict
    }
```

---

## 📦 **Phase 6: Integration & Testing** (2-3 days)

### **6.1 End-to-End Integration Tests**
**Start Signal**: All components built  
**Done Signal**: Full workflow tests passing  
**Test Path**: Integration test runs complete analysis pipeline from search to recommendation

```python
# tests/test_integration.py
def test_full_analysis_pipeline():
    """Test complete pipeline: search -> collect -> analyze -> recommend"""
    
def test_cache_behavior():
    """Test caching works correctly"""
    
def test_data_freshness_logic():
    """Test freshness checking and auto-refresh"""
```

### **6.2 Performance Optimization**
**Start Signal**: Integration tests passing  
**Done Signal**: Response times under target thresholds  
**Test Path**: Analysis completes in <30s for cached data, <2min for fresh scraping

### **6.3 Documentation & Examples**
**Start Signal**: Performance optimized  
**Done Signal**: Complete documentation with examples  
**Test Path**: New user can follow quick-start guide successfully

---

## ✅ **Completion Criteria**

```python
# Example final output
GET /api/v1/analysis/charizard-v-154-185
{
    "product": {
        "name": "Charizard V",
        "set": "Evolving Skies", 
        "number": "154/185",
        "type": "card"
    },
    "data_summary": {
        "ebay_listings": 1247,
        "date_range": "2021-08-01 to 2024-12-28",
        "data_quality": 0.94,
        "last_updated": "2024-12-28T10:30:00Z"
    },
    "metrics": {
        "cagr": 0.23,
        "volatility": 0.18,
        "sharpe_ratio": 1.28,
        "max_drawdown": -0.15,
        "current_vs_peak": 0.85
    },
    "recommendation": {
        "action": "BUY",
        "confidence": 0.87,
        "reasoning": [
            "Strong 23% CAGR with manageable volatility",
            "Currently 15% below peak - good entry point", 
            "High Sharpe ratio indicates good risk-adjusted returns"
        ],
        "target_buy_price": 45.00,
        "target_sell_price": 65.00
    }
}
```

**Success Metrics:**
- ✅ Handles both cards and sealed products
- ✅ Auto-refreshes stale data  
- ✅ Produces analysis in <2 minutes
- ✅ 95%+ uptime for API
- ✅ Clear, actionable recommendations
- ✅ Proper error handling and fallbacks

---

## 🔧 **Technical Stack**

- **Database**: Existing Supabase PostgreSQL
- **Data Processing**: pandas, numpy
- **Web Framework**: FastAPI
- **Task Queue**: (Optional) Celery for async scraping
- **Caching**: Database-based with timestamp logic
- **Testing**: pytest with integration test suite
- **Documentation**: FastAPI automatic OpenAPI docs

---

## 📋 **Dependencies**

- All existing scraper dependencies
- `pandas>=1.5.0` (financial calculations)
- `numpy>=1.21.0` (mathematical operations)  
- `fastapi>=0.68.0` (API framework)
- `pytest>=6.0.0` (testing framework)

**Total Estimated Time: 14-20 days** 