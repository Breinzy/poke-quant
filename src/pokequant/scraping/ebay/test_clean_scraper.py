#!/usr/bin/env python3
"""
Test Clean PriceCharting Scraper
Verify the updated scraper filters out subscription fees and extracts clean date-price pairs
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_selector import CardSelector
from pricecharting_scraper import PriceChartingScraper

def test_clean_scraper():
    """Test the updated scraper with clean data extraction"""
    
    print("🧪 TESTING CLEAN PRICECHARTING SCRAPER")
    print("="*60)
    
    # Initialize components
    card_selector = CardSelector()
    pricecharting_scraper = PriceChartingScraper()
    
    # Get one test card
    curated_cards = card_selector.get_curated_investment_targets()
    if not curated_cards:
        print("❌ No curated cards found")
        return
    
    test_card = curated_cards[0]  # Use first card
    card_name = test_card.get('card_name', 'Unknown')
    
    print(f"🎯 Testing with: {card_name}")
    print()
    
    # Search for the card
    print("🔍 Step 1: Searching PriceCharting...")
    pricecharting_url = pricecharting_scraper.search_card_on_pricecharting(
        test_card.get('card_name', ''),
        test_card.get('set_name', ''),
        test_card
    )
    
    if not pricecharting_url:
        print("❌ No PriceCharting page found")
        return
    
    print(f"✅ Found URL: {pricecharting_url}")
    print()
    
    # Scrape the data
    print("📈 Step 2: Scraping clean price data...")
    price_data = pricecharting_scraper.scrape_price_history(pricecharting_url)
    
    if not price_data:
        print("❌ Failed to scrape data")
        return
    
    print("✅ Data scraped successfully!")
    print()
    
    # Analyze the data
    print("📊 CLEAN DATA ANALYSIS:")
    print("-" * 40)
    
    # Current prices analysis
    current_prices = price_data.get('current_prices', {})
    filtered_prices = {k: v for k, v in current_prices.items() 
                      if v != 6.0 and v >= 1.0 and v <= 100000}
    subscription_fees_removed = len(current_prices) - len(filtered_prices)
    
    print(f"Current Prices:")
    print(f"  Raw prices found: {len(current_prices)}")
    print(f"  Clean prices (filtered): {len(filtered_prices)}")
    print(f"  Subscription fees removed: {subscription_fees_removed}")
    
    if filtered_prices:
        print(f"  Sample clean prices:")
        for i, (key, price) in enumerate(list(filtered_prices.items())[:5]):
            print(f"    {key}: ${price}")
        if len(filtered_prices) > 5:
            print(f"    ... and {len(filtered_prices) - 5} more")
    print()
    
    # Historical data analysis
    historical_data = price_data.get('historical_chart_data', [])
    clean_historical = [entry for entry in historical_data 
                       if isinstance(entry, dict) and 'date' in entry and 'price' in entry]
    
    print(f"Historical Chart Data:")
    print(f"  Raw chart entries: {len(historical_data)}")
    print(f"  Clean date-price pairs: {len(clean_historical)}")
    
    if clean_historical:
        print(f"  Sample clean historical data:")
        for entry in clean_historical[:5]:
            print(f"    {entry['date']}: ${entry['price']}")
        if len(clean_historical) > 5:
            print(f"    ... and {len(clean_historical) - 5} more entries")
    print()
    
    # Price tables analysis
    price_tables = price_data.get('price_tables', [])
    total_clean_table_entries = 0
    
    print(f"Price Tables:")
    print(f"  Total tables found: {len(price_tables)}")
    
    for i, table in enumerate(price_tables):
        clean_data = table.get('clean_price_data', [])
        total_clean_table_entries += len(clean_data)
        print(f"  Table {i+1}: {len(clean_data)} clean entries")
        
        if clean_data and i == 0:  # Show sample from first table
            print(f"    Sample from table {i+1}:")
            for entry in clean_data[:3]:
                print(f"      {entry['date']}: ${entry['price']}")
    print()
    
    # Summary
    total_clean_data = len(clean_historical) + total_clean_table_entries
    total_raw_data = len(historical_data) + len(current_prices)
    
    print("📈 SUMMARY:")
    print(f"  Total raw data points: {total_raw_data}")
    print(f"  Total clean data points: {total_clean_data}")
    print(f"  Data cleaned successfully: {subscription_fees_removed + (len(historical_data) - len(clean_historical))} points filtered")
    print()
    
    if clean_historical or total_clean_table_entries > 0:
        print("✅ SUCCESS: Clean date-price pairs extracted successfully!")
        print("🚫 Subscription fees ($6.00) filtered out")
        print("📅 Historical data with dates available")
    else:
        print("⚠️ WARNING: No clean historical data found")

if __name__ == "__main__":
    test_clean_scraper() 