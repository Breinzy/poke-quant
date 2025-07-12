#!/usr/bin/env python3
"""
Debug eBay HTML Structure
Captures fresh eBay HTML and analyzes the structure to fix parsing
"""

import sys
import os
from bs4 import BeautifulSoup
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ebay_search import eBaySearcher

def analyze_ebay_html_structure():
    """Analyze current eBay HTML structure to fix parsing"""
    
    print("🔍 ANALYZING EBAY HTML STRUCTURE")
    print("="*50)
    
    # Get fresh eBay HTML
    searcher = eBaySearcher()
    
    # Use one of our new specific search terms
    search_term = "Charizard V 154 Brilliant Stars near mint"
    print(f"🔎 Testing search: '{search_term}'")
    
    try:
        # Get HTML
        search_results = searcher.search_sold_listings(search_term, max_pages=1, max_results=10)
        
        if not search_results:
            print("❌ No search results returned")
            return
        
        html = search_results[0]  # First page
        print(f"✅ Got {len(html)} characters of HTML")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Save HTML for manual inspection
        with open('debug_fresh_ebay_html.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"💾 Saved HTML to: debug_fresh_ebay_html.html")
        
        # Analyze structure
        print(f"\n🔍 ANALYZING HTML STRUCTURE:")
        
        # Check different potential listing containers
        container_patterns = [
            ('li with s-item', 'li', {'class': re.compile(r's-item')}),
            ('div with srp-results', 'div', {'class': re.compile(r'srp-results')}),
            ('div with s-item', 'div', {'class': re.compile(r's-item')}),
            ('li with srp-results', 'li', {'class': re.compile(r'srp-results')}),
            ('div with item', 'div', {'class': re.compile(r'item')}),
            ('li with result', 'li', {'class': re.compile(r'result')}),
            ('article tags', 'article', {}),
            ('div with listing', 'div', {'class': re.compile(r'listing')}),
        ]
        
        for description, tag, attrs in container_patterns:
            elements = soup.find_all(tag, attrs)
            print(f"  📊 {description}: {len(elements)} found")
            
            if elements and len(elements) > 5:  # Promising pattern
                print(f"    ✅ GOOD CANDIDATE: {description}")
                
                # Analyze first few elements
                for i, elem in enumerate(elements[:3]):
                    print(f"    🔍 Element {i+1}:")
                    
                    # Look for title
                    title_selectors = [
                        'div.s-item__title span',
                        'h3 span',
                        '.s-item__title',
                        'h3',
                        '.title',
                        'a[href*="itm"]'
                    ]
                    
                    title_found = False
                    for selector in title_selectors:
                        title_elem = elem.select_one(selector)
                        if title_elem and title_elem.get_text(strip=True):
                            title = title_elem.get_text(strip=True)
                            if len(title) > 10:  # Valid title
                                print(f"      🎯 Title (via {selector}): {title[:60]}...")
                                title_found = True
                                break
                    
                    if not title_found:
                        print(f"      ❌ No title found")
                    
                    # Look for price
                    price_selectors = [
                        '.s-item__price',
                        'span.notranslate',
                        '.price',
                        '[class*="price"]'
                    ]
                    
                    price_found = False
                    for selector in price_selectors:
                        price_elem = elem.select_one(selector)
                        if price_elem and price_elem.get_text(strip=True):
                            price = price_elem.get_text(strip=True)
                            if '$' in price:  # Valid price
                                print(f"      💰 Price (via {selector}): {price}")
                                price_found = True
                                break
                    
                    if not price_found:
                        print(f"      ❌ No price found")
                    
                    print()
        
        # Look for the main results container
        print(f"\n🔍 LOOKING FOR MAIN RESULTS CONTAINER:")
        
        main_containers = [
            soup.find('div', {'id': 'srp-river-results'}),
            soup.find('div', {'class': re.compile(r'srp-results')}),
            soup.find('ul', {'class': re.compile(r'srp-results')}),
            soup.find('div', {'id': 'ListViewInner'}),
        ]
        
        for i, container in enumerate(main_containers):
            if container:
                print(f"  ✅ Container {i+1} found: {container.name} with {len(container.find_all('li'))} <li> children")
                
                # Check class names
                if container.get('class'):
                    print(f"    Classes: {container.get('class')}")
                if container.get('id'):
                    print(f"    ID: {container.get('id')}")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        print(f"1. Try different listing container selectors")
        print(f"2. Update title and price extraction selectors") 
        print(f"3. Look for the main results container first")
        print(f"4. Check debug_fresh_ebay_html.html for manual inspection")
        
    except Exception as e:
        print(f"❌ Error analyzing HTML: {e}")

if __name__ == "__main__":
    analyze_ebay_html_structure() 