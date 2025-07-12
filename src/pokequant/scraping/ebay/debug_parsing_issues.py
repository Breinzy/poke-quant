#!/usr/bin/env python3
"""
Debug Parsing Issues
Investigate the root cause of $1.00 prices and wrong product data
"""

import sys
import os
import re
from bs4 import BeautifulSoup

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_selector import CardSelector
from pricecharting_scraper import PriceChartingScraper

def debug_specific_product(product_name, expected_price_range, is_sealed=False):
    """Debug a specific product to understand parsing issues"""
    
    print(f"\n🔍 DEBUGGING: {product_name}")
    print("="*60)
    
    # Initialize scraper
    pricecharting_scraper = PriceChartingScraper()
    
    # Get the URL
    if is_sealed:
        url = pricecharting_scraper.search_sealed_product_on_pricecharting(product_name)
    else:
        card_selector = CardSelector()
        cards = card_selector.get_curated_investment_targets()
        test_card = next((c for c in cards if product_name.lower() in c.get('card_name', '').lower()), None)
        if test_card:
            url = pricecharting_scraper.search_card_on_pricecharting(
                test_card.get('card_name', ''),
                test_card.get('set_name', ''),
                test_card
            )
        else:
            print(f"❌ Could not find card: {product_name}")
            return
    
    if not url:
        print(f"❌ Could not find URL for: {product_name}")
        return
    
    print(f"🔗 URL: {url}")
    print(f"💰 Expected price range: {expected_price_range}")
    print()
    
    # Get the HTML
    try:
        pricecharting_scraper._rate_limit()
        response = pricecharting_scraper.session.get(url)
        
        if response.status_code != 200:
            print(f"❌ Failed to load page: {response.status_code}")
            return
        
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print(f"📄 HTML loaded: {len(html_content)} characters")
        print()
        
        # 1. Check page title and product info
        print("📋 PAGE INFORMATION:")
        print("-" * 30)
        
        title = soup.find('title')
        if title:
            print(f"  Page title: {title.get_text()}")
        
        # Look for product name/description
        product_selectors = ['h1', '.product-title', '.game-title', '.title']
        for selector in product_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) < 200:
                    print(f"  Product info ({selector}): {text}")
        
        print()
        
        # 2. Analyze where $1.00 prices are coming from
        print("🔍 ANALYZING $1.00 PRICE SOURCES:")
        print("-" * 40)
        
        # Find all elements containing $1.00 or 1.0
        dollar_one_pattern = r'\$1\.0{1,2}(?!\d)'
        one_dollar_elements = []
        
        for element in soup.find_all(text=re.compile(dollar_one_pattern)):
            parent = element.parent
            if parent:
                one_dollar_elements.append({
                    'text': element.strip(),
                    'parent_tag': parent.name,
                    'parent_class': parent.get('class', []),
                    'parent_id': parent.get('id', ''),
                    'context': parent.get_text().strip()[:100]
                })
        
        print(f"  Found {len(one_dollar_elements)} $1.00 references:")
        for i, elem in enumerate(one_dollar_elements[:10]):  # Show first 10
            print(f"    {i+1}. Tag: <{elem['parent_tag']}> Class: {elem['parent_class']}")
            print(f"       Context: {elem['context']}")
            print()
        
        # 3. Examine our current price extraction logic
        print("🎯 TESTING CURRENT PRICE EXTRACTION:")
        print("-" * 40)
        
        # Test our current selectors
        price_selectors = [
            '.price-display',
            '.current-price', 
            '.price-value',
            'span[class*="price"]',
            'div[class*="price"]',
            '.loose-price',
            '.cib-price',
            '.new-price'
        ]
        
        found_prices = []
        
        for selector in price_selectors:
            elements = soup.select(selector)
            print(f"  Selector '{selector}': {len(elements)} elements")
            
            for i, element in enumerate(elements[:3]):  # Show first 3
                text = element.get_text().strip()
                price_match = re.search(r'\$(\d+\.?\d*)', text)
                
                if price_match:
                    price = float(price_match.group(1))
                    found_prices.append({
                        'selector': selector,
                        'price': price,
                        'text': text,
                        'element_html': str(element)[:200]
                    })
                    print(f"    Element {i+1}: ${price} from '{text}'")
                    print(f"      HTML: {str(element)[:100]}...")
        
        print()
        
        # 4. Examine table data extraction
        print("📊 ANALYZING TABLE DATA:")
        print("-" * 30)
        
        tables = soup.find_all('table')
        print(f"  Found {len(tables)} tables")
        
        for i, table in enumerate(tables[:3]):  # Examine first 3 tables
            print(f"\n  Table {i+1}:")
            
            # Look for table headers
            headers = table.find_all(['th', 'thead'])
            if headers:
                header_texts = [h.get_text().strip() for h in headers]
                print(f"    Headers: {header_texts}")
            
            # Look for prices in this table
            cells = table.find_all(['td', 'th'])
            table_prices = []
            
            for cell in cells:
                text = cell.get_text().strip()
                price_match = re.search(r'\$(\d+\.?\d*)', text)
                if price_match:
                    price = float(price_match.group(1))
                    table_prices.append({
                        'price': price,
                        'text': text,
                        'cell_html': str(cell)[:100]
                    })
            
            print(f"    Prices found: {len(table_prices)}")
            
            # Show sample prices
            for j, price_info in enumerate(table_prices[:5]):
                print(f"      Price {j+1}: ${price_info['price']} from '{price_info['text']}'")
                if price_info['price'] <= 2.0:  # Focus on suspicious low prices
                    print(f"        ⚠️ LOW PRICE HTML: {price_info['cell_html']}")
        
        print()
        
        # 5. Check chart data
        print("📈 CHART DATA ANALYSIS:")
        print("-" * 25)
        
        timestamp_pattern = r'\[(\d{13}),(\d+)\]'
        chart_matches = re.findall(timestamp_pattern, html_content)
        
        print(f"  Chart data points: {len(chart_matches)}")
        
        if chart_matches:
            prices = [int(match[1]) / 100.0 for match in chart_matches]
            print(f"  Chart price range: ${min(prices):.2f} - ${max(prices):.2f}")
            
            # Show some sample points
            print("  Sample chart prices:")
            for i, (timestamp, price_cents) in enumerate(chart_matches[:5]):
                from datetime import datetime
                date = datetime.fromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d')
                price = int(price_cents) / 100.0
                print(f"    {date}: ${price:.2f}")
        
        # 6. Save sample HTML for manual inspection
        sample_filename = f"debug_html_{product_name.replace(' ', '_').lower()}.html"
        with open(sample_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n💾 Saved HTML to: {sample_filename}")
        
        return {
            'url': url,
            'title': title.get_text() if title else '',
            'found_prices': found_prices,
            'chart_data_points': len(chart_matches),
            'suspicious_low_prices': [p for p in found_prices if p['price'] <= 2.0]
        }
        
    except Exception as e:
        print(f"❌ Error debugging {product_name}: {e}")
        return None

def main():
    """Debug multiple problematic products"""
    
    print("🚨 DEBUGGING PARSING ISSUES")
    print("="*60)
    
    # Products with known issues
    problematic_products = [
        ("Evolving Skies Booster Box", "$400-600", True),
        ("Base Set Booster Box", "$15,000-30,000", True), 
        ("Charizard V", "$300-500", False),
    ]
    
    results = {}
    
    for product_name, expected_price, is_sealed in problematic_products:
        result = debug_specific_product(product_name, expected_price, is_sealed)
        if result:
            results[product_name] = result
    
    # Summary
    print(f"\n📋 DEBUGGING SUMMARY:")
    print("="*40)
    
    for product_name, result in results.items():
        print(f"\n{product_name}:")
        print(f"  URL: {result['url']}")
        print(f"  Title: {result['title']}")
        print(f"  Prices found: {len(result['found_prices'])}")
        print(f"  Chart data: {result['chart_data_points']} points")
        print(f"  Suspicious low prices: {len(result['suspicious_low_prices'])}")
        
        if result['suspicious_low_prices']:
            print(f"  Low price details:")
            for price_info in result['suspicious_low_prices'][:3]:
                print(f"    ${price_info['price']} from '{price_info['text']}'")

if __name__ == "__main__":
    main() 