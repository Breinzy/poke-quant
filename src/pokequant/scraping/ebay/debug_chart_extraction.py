#!/usr/bin/env python3
"""
Debug Chart Data Extraction
Investigate how PriceCharting stores chart data in JavaScript
"""

import sys
import os
import re
import json
from bs4 import BeautifulSoup

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_selector import CardSelector
from pricecharting_scraper import PriceChartingScraper

def debug_chart_extraction():
    """Debug chart data extraction from PriceCharting"""
    
    print("🔍 DEBUGGING CHART DATA EXTRACTION")
    print("="*60)
    
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
    
    if not pricecharting_url:
        print("❌ No URL found")
        return
    
    print(f"🔗 URL: {pricecharting_url}")
    print()
    
    # Get the raw HTML
    print("📄 Fetching raw HTML...")
    try:
        pricecharting_scraper._rate_limit()
        response = pricecharting_scraper.session.get(pricecharting_url)
        
        if response.status_code != 200:
            print(f"❌ Failed to load page: {response.status_code}")
            return
        
        html_content = response.text
        print(f"✅ HTML loaded: {len(html_content)} characters")
        print()
        
        # Look for JavaScript patterns
        print("🔍 SEARCHING FOR JAVASCRIPT CHART DATA:")
        print("-" * 40)
        
        # Search patterns
        patterns_to_check = [
            (r'chartData\s*[=:]\s*(\[.*?\]);?', 'chartData variable'),
            (r'priceData\s*[=:]\s*(\[.*?\]);?', 'priceData variable'),
            (r'historyData\s*[=:]\s*(\[.*?\]);?', 'historyData variable'),
            (r'price_history\s*[=:]\s*(\[.*?\]);?', 'price_history variable'),
            (r'data\s*:\s*(\[.*?\])', 'data property'),
            (r'series\s*:\s*\[\s*\{\s*data\s*:\s*(\[.*?\])', 'series data'),
            (r'"data"\s*:\s*(\[.*?\])', 'JSON data property'),
            (r'new\s+Highcharts\.Chart\s*\(\s*\{.*?data\s*:\s*(\[.*?\])', 'Highcharts data'),
            (r'Chart\s*\(\s*.*?data\s*:\s*(\[.*?\])', 'Chart constructor data'),
            (r'\[[\d\s,.\-"\']+\]', 'Any array with numbers'),
        ]
        
        for pattern, description in patterns_to_check:
            print(f"\n🔎 Checking: {description}")
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            if matches:
                print(f"  ✅ Found {len(matches)} matches")
                
                for i, match in enumerate(matches[:3]):  # Show first 3
                    print(f"    Match {i+1}: {match[:200]}{'...' if len(match) > 200 else ''}")
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(match)
                        if isinstance(data, list) and len(data) > 0:
                            print(f"      ✅ Valid JSON array with {len(data)} items")
                            
                            # Show sample
                            first_item = data[0]
                            print(f"      Sample item: {first_item}")
                            
                            # Check if it looks like date-price data
                            if isinstance(first_item, list) and len(first_item) >= 2:
                                print(f"      📊 Looks like chart data: {len(first_item)} fields per item")
                        else:
                            print(f"      ⚠️ JSON but not array: {type(data)}")
                    except json.JSONDecodeError:
                        print(f"      ❌ Not valid JSON")
            else:
                print(f"  ❌ No matches found")
        
        # Look specifically in script tags
        print(f"\n📜 ANALYZING SCRIPT TAGS:")
        print("-" * 40)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        scripts = soup.find_all('script')
        
        print(f"Found {len(scripts)} script tags")
        
        chart_scripts = []
        for i, script in enumerate(scripts):
            script_content = script.get_text()
            
            # Look for chart-related keywords
            chart_keywords = ['chart', 'price', 'data', 'series', 'highcharts', 'graph']
            keyword_count = sum(1 for keyword in chart_keywords if keyword.lower() in script_content.lower())
            
            if keyword_count >= 2:  # At least 2 chart-related keywords
                chart_scripts.append((i, script_content, keyword_count))
        
        print(f"Found {len(chart_scripts)} scripts with chart-related content")
        
        for i, (script_idx, script_content, keyword_count) in enumerate(chart_scripts[:3]):  # Show first 3
            print(f"\n  📜 Chart Script {i+1} (index {script_idx}, {keyword_count} keywords):")
            print(f"    Length: {len(script_content)} characters")
            
            # Look for arrays in this script
            array_pattern = r'\[[\d\s,.\-"\']+\]'
            arrays = re.findall(array_pattern, script_content)
            
            print(f"    Arrays found: {len(arrays)}")
            
            for j, array in enumerate(arrays[:2]):  # Show first 2
                print(f"      Array {j+1}: {array[:100]}{'...' if len(array) > 100 else ''}")
                
                try:
                    data = json.loads(array)
                    if isinstance(data, list) and len(data) > 0:
                        print(f"        ✅ Valid array with {len(data)} items")
                        print(f"        Sample: {data[0] if data else 'empty'}")
                except:
                    print(f"        ❌ Invalid JSON")
        
        # Save sample script for manual inspection
        if chart_scripts:
            sample_script = chart_scripts[0][1]
            with open('debug_sample_script.js', 'w', encoding='utf-8') as f:
                f.write(sample_script)
            print(f"\n💾 Saved sample script to: debug_sample_script.js")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")

if __name__ == "__main__":
    debug_chart_extraction() 