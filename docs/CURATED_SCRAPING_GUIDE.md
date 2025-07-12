# 🎯 Curated Investment Scraping Guide

This guide shows you how to use the new focused approach to scrape data for specific high-value cards and sealed products, then prepare the data for quantitative analysis.

## 🎯 What's Different

**Before**: The scraper was too broad, grabbing thousands of "premium" cards based on general criteria.

**Now**: We target exactly 15 specific high-value cards + 5 sealed products for comprehensive data collection.

## 📊 Curated Investment Targets

### 🎴 Cards (15 total)
- **Charizard Cards**: Base Set Charizard, Brilliant Stars Charizard V/VSTAR
- **Pikachu Cards**: Base Set Pikachu, Scarlet & Violet Pikachu V, Vivid Voltage Pikachu VMAX
- **Modern High-Value**: Lugia V/VSTAR, Rayquaza V/VMAX from popular sets
- **Alt Art Cards**: Umbreon V, Espeon V from Evolving Skies
- **Promo Cards**: Special promotional Pikachu and Charizard cards

### 📦 Sealed Products (5 total)
- Brilliant Stars Booster Box
- Evolving Skies Booster Box  
- Silver Tempest Booster Box
- Base Set Booster Box (vintage)
- Charizard Ultra Premium Collection

## 🚀 Quick Start

### Option 1: Full Comprehensive Analysis (Recommended)

```bash
cd ebay-scraper
python comprehensive_curated_scraper.py
```

This runs both eBay scraping AND PriceCharting historical data collection in one go.

**Options:**
```bash
# Light mode (faster but less data)
python comprehensive_curated_scraper.py --light-mode

# Skip PriceCharting (eBay only)
python comprehensive_curated_scraper.py --skip-pricecharting

# Limit to first 10 items
python comprehensive_curated_scraper.py --max-items 10
```

### Option 2: eBay Scraping Only

```bash
cd ebay-scraper
python targeted_scraper.py --strategy curated --comprehensive
```

### Option 3: PriceCharting Historical Data Only

```bash
cd ebay-scraper
python pricecharting_scraper.py
```

## 📊 Data Flow

```
1. Card Selection → 15 specific cards + 5 sealed products
2. eBay Scraping → Multiple search terms per item → High-quality listings
3. PriceCharting → Historical pricing data for same items
4. Data Prep → Join and prepare for quant analysis
5. Quant Analysis → Build models and generate insights
```

## 📈 Expected Results

After running the comprehensive scraper, you should have:

- **eBay Data**: 500-2000 high-quality sold listings for your curated items
- **Historical Data**: PriceCharting price history for comparison
- **Comprehensive Dataset**: Ready for quantitative modeling

## 🧮 Next Steps: Quant Analysis

Once you have the data, start building quant models:

```bash
cd quant
python data_preparation.py
```

This will:
1. Load eBay data from Supabase
2. Load PriceCharting data from files
3. Join the datasets
4. Calculate basic features
5. Generate card-level statistics
6. Save prepared datasets for modeling

## 📁 Output Files

The scraping process creates several files:

```
ebay-scraper/data/
├── comprehensive_analysis_YYYYMMDD_HHMMSS.json    # Full results
├── pricecharting_historical_YYYYMMDD_HHMMSS.json  # Historical data
└── logs/
    └── targeted_scraping_YYYYMMDD_HHMMSS.json     # eBay scraping logs

quant/data/
├── unified_dataset_YYYYMMDD_HHMMSS.csv            # Combined dataset
└── card_stats_YYYYMMDD_HHMMSS.csv                 # Card aggregates
```

## 🎯 Key Benefits

1. **Focused**: Only 20 items instead of thousands
2. **Comprehensive**: Deep data collection for each item
3. **Quality**: Better search terms and filtering
4. **Actionable**: Perfect size for detailed analysis
5. **Scalable**: Easy to add more items to the curated list

## 🔧 Customizing the Curated List

To modify which cards/products are tracked, edit:

```python
# ebay-scraper/card_selector.py
def get_curated_investment_targets(self):
    target_cards = [
        # Add your own cards here
        {"card_name": "Your Card", "set_name": "Set Name", "card_number": "123"},
    ]
```

## 🚨 Important Notes

- **Rate Limiting**: Built-in delays to respect eBay and PriceCharting
- **Data Quality**: Extensive filtering to ensure clean listings
- **Error Handling**: Continues processing even if some items fail
- **Comprehensive Mode**: Increases limits and delays for maximum data collection

## 📞 Troubleshooting

**No cards found**: Check that your `pokemon_cards` table has the target cards
**eBay scraping fails**: Verify your proxy settings and rate limits
**PriceCharting fails**: Check your internet connection and consider using a VPN
**Missing data**: Run with `--light-mode` first to test connectivity

Now you're ready to collect focused, high-quality data for your quant analysis! 🎉 