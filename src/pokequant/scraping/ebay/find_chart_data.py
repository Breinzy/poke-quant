#!/usr/bin/env python3
"""
Find Chart Data in PriceCharting HTML
Extract the timestamp-price pairs we discovered
"""

import sys
import os
import re
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_selector import CardSelector
from pricecharting_scraper import PriceChartingScraper

def find_chart_data():
    """Find and extract chart data from PriceCharting"""
    
    print("📊 FINDING CHART DATA")
    print("="*50)
    
    # Initialize components
    card_selector = CardSelector()
    pricecharting_scraper = PriceChartingScraper()
    
    # Get test card
    curated_cards = card_selector.get_curated_investment_targets()
    test_card = curated_cards[0]  # Charizard V
    
    print(f"🎯 Testing with: {test_card.get('card_name', 'Unknown')}")
    
    # Get the URL
    pricecharting_url = pricecharting_scraper.search_card_on_pricecharting(
        test_card.get('card_name', ''),
        test_card.get('set_name', ''),
        test_card
    )
    
    print(f"🔗 URL: {pricecharting_url}")
    
    # Get the HTML
    pricecharting_scraper._rate_limit()
    response = pricecharting_scraper.session.get(pricecharting_url)
    html_content = response.text
    
    print(f"📄 HTML: {len(html_content)} characters")
    print()
    
    # Look for timestamp-price pairs
    print("🔍 EXTRACTING TIMESTAMP-PRICE PAIRS:")
    print("-" * 40)
    
    # Pattern for [timestamp, price] pairs
    timestamp_pattern = r'\[(\d{13}),(\d+)\]'
    matches = re.findall(timestamp_pattern, html_content)
    
    print(f"✅ Found {len(matches)} timestamp-price pairs")
    
    if matches:
        print("\n📊 Sample data:")
        chart_data = []
        
        for i, (timestamp_str, price_str) in enumerate(matches[:10]):  # Show first 10
            timestamp = int(timestamp_str)
            price = int(price_str)
            
            # Convert timestamp to date
            date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
            
            # Convert price (seems to be in cents)
            price_dollars = price / 100.0
            
            chart_entry = {
                'timestamp': timestamp,
                'date': date,
                'price': price_dollars,
                'raw_price': price
            }
            chart_data.append(chart_entry)
            
            print(f"  {i+1}. {date}: ${price_dollars:.2f} (raw: {price})")
        
        if len(matches) > 10:
            print(f"  ... and {len(matches) - 10} more entries")
        
        print(f"\n📈 CHART DATA ANALYSIS:")
        print(f"  Total entries: {len(matches)}")
        
        if chart_data:
            prices = [entry['price'] for entry in chart_data]
            print(f"  Price range: ${min(prices):.2f} - ${max(prices):.2f}")
            
            dates = [entry['date'] for entry in chart_data]
            print(f"  Date range: {min(dates)} to {max(dates)}")
        
        # Save sample to file
        sample_data = []
        for timestamp_str, price_str in matches:
            timestamp = int(timestamp_str)
            price = int(price_str)
            date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
            price_dollars = price / 100.0
            
            sample_data.append({
                'date': date,
                'price': price_dollars,
                'timestamp': timestamp,
                'raw_price': price
            })
        
        with open('sample_chart_data.json', 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        print(f"\n💾 Saved chart data to: sample_chart_data.json")
        
        return sample_data
    else:
        print("❌ No timestamp-price pairs found")
        return []

if __name__ == "__main__":
    find_chart_data() 