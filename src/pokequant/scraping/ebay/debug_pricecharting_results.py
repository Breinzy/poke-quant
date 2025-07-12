#!/usr/bin/env python3
"""
Debug what PriceCharting actually returns for our search terms
"""

import requests
from bs4 import BeautifulSoup
import time

def debug_search_results(search_term: str):
    """Debug what PriceCharting returns for a specific search term"""
    
    print(f"\n🔍 DEBUGGING SEARCH: '{search_term}'")
    print("=" * 50)
    
    try:
        search_url = f"https://www.pricecharting.com/search-products?q={search_term}&console=&genre=TCG+Card"
        print(f"URL: {search_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check page title
            title = soup.find('title')
            if title:
                print(f"Page title: {title.get_text()}")
            
            # Look for ALL links and print them
            all_links = soup.find_all('a')
            game_links = []
            other_links = []
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text().strip()
                
                if href and ('/game/' in href or '/games/' in href):
                    game_links.append((text, href))
                elif text and len(text) > 3:  # Non-empty meaningful text
                    other_links.append((text, href))
            
            print(f"\nFound {len(game_links)} game/product links:")
            for i, (text, href) in enumerate(game_links[:10]):  # Show first 10
                print(f"  {i+1}. {text} -> {href}")
            
            if len(game_links) > 10:
                print(f"  ... and {len(game_links) - 10} more game links")
            
            print(f"\nFound {len(other_links)} other links with text:")
            for i, (text, href) in enumerate(other_links[:5]):  # Show first 5
                print(f"  {i+1}. {text} -> {href}")
            
            # Look for specific selectors
            selectors_to_try = [
                'a[href*="/game/"]',
                'a[href*="/games/"]',
                '.product-link',
                '.search-result a',
                'div.row a',
                '.col a',
                'table a'
            ]
            
            print(f"\nTesting different selectors:")
            for selector in selectors_to_try:
                results = soup.select(selector)
                if results:
                    print(f"  {selector}: {len(results)} results")
                    if results:
                        first_result = results[0]
                        text = first_result.get_text().strip()
                        href = first_result.get('href', '')
                        print(f"    First: {text} -> {href}")
                else:
                    print(f"  {selector}: 0 results")
            
            # Save the HTML for manual inspection (first 5000 chars)
            html_snippet = response.text[:5000]
            print(f"\nFirst 500 chars of HTML:")
            print(html_snippet[:500])
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Test several search terms"""
    
    print("🐛 PRICECHARTING RESULTS DEBUG")
    print("=" * 60)
    
    test_searches = [
        "Charizard V 154",
        "Charizard V",
        "Brilliant Stars Booster Box",
        "Lost Origin Elite Trainer Box",
        "Pikachu 58",
        "Lugia V 138"
    ]
    
    for search_term in test_searches:
        debug_search_results(search_term)
        time.sleep(2)  # Be nice to the server
        
    print("\n✅ Debug complete")

if __name__ == "__main__":
    main() 