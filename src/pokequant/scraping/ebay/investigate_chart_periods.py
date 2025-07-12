#!/usr/bin/env python3
"""
Investigate Chart Period Settings
Find how to get full historical data from PriceCharting
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

def investigate_chart_periods():
    """Investigate how to get full historical chart data"""
    
    print("🔍 INVESTIGATING CHART PERIOD SETTINGS")
    print("="*60)
    
    # Initialize components
    card_selector = CardSelector()
    pricecharting_scraper = PriceChartingScraper()
    
    # Get test card
    curated_cards = card_selector.get_curated_investment_targets()
    test_card = curated_cards[0]  # Charizard V
    
    print(f"🎯 Testing with: {test_card.get('card_name', 'Unknown')}")
    
    # Get the base URL
    base_url = pricecharting_scraper.search_card_on_pricecharting(
        test_card.get('card_name', ''),
        test_card.get('set_name', ''),
        test_card
    )
    
    print(f"🔗 Base URL: {base_url}")
    print()
    
    # Test different URL variations to get full historical data
    url_variations = [
        base_url,  # Original
        f"{base_url}?period=all",
        f"{base_url}?timeframe=all",
        f"{base_url}?range=all",
        f"{base_url}?view=all",
        f"{base_url}?chart=all",
        f"{base_url}?time=all",
        f"{base_url}?span=max",
        f"{base_url}?period=max",
        f"{base_url}?all=true",
    ]
    
    results = {}
    
    for i, url in enumerate(url_variations):
        print(f"🧪 Testing URL {i+1}: {url}")
        
        try:
            pricecharting_scraper._rate_limit()
            response = pricecharting_scraper.session.get(url)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Extract timestamp-price pairs
                timestamp_pattern = r'\[(\d{13}),(\d+)\]'
                matches = re.findall(timestamp_pattern, html_content)
                
                print(f"  ✅ Status: {response.status_code}")
                print(f"  📊 Chart data points: {len(matches)}")
                
                if matches:
                    # Analyze date range
                    timestamps = [int(match[0]) for match in matches]
                    earliest = datetime.fromtimestamp(min(timestamps) / 1000)
                    latest = datetime.fromtimestamp(max(timestamps) / 1000)
                    
                    print(f"  📅 Date range: {earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}")
                    print(f"  ⏱️ Time span: {(latest - earliest).days} days")
                    
                    # Sample prices
                    prices = [int(match[1]) / 100.0 for match in matches if int(match[1]) > 0]
                    if prices:
                        print(f"  💰 Price range: ${min(prices):.2f} - ${max(prices):.2f}")
                
                results[url] = {
                    'status': response.status_code,
                    'data_points': len(matches),
                    'url_length': len(url),
                    'response_length': len(html_content)
                }
                
            else:
                print(f"  ❌ Status: {response.status_code}")
                results[url] = {
                    'status': response.status_code,
                    'data_points': 0,
                    'url_length': len(url),
                    'response_length': 0
                }
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[url] = {
                'status': 'error',
                'data_points': 0,
                'error': str(e)
            }
        
        print()
    
    # Summary
    print("📊 SUMMARY:")
    print("-" * 40)
    
    best_url = None
    max_data_points = 0
    
    for url, result in results.items():
        data_points = result.get('data_points', 0)
        status = result.get('status', 'unknown')
        
        url_desc = url.replace(base_url, '').replace('?', 'with ?') or 'original'
        print(f"  {url_desc}: {data_points} points (status: {status})")
        
        if data_points > max_data_points:
            max_data_points = data_points
            best_url = url
    
    print()
    if best_url:
        print(f"🏆 BEST URL: {best_url}")
        print(f"📊 Max data points: {max_data_points}")
        
        # Save the best URL format for use in scraper
        with open('best_chart_url.txt', 'w') as f:
            f.write(best_url)
        print(f"💾 Saved best URL to: best_chart_url.txt")
    
    return results

if __name__ == "__main__":
    investigate_chart_periods() 