#!/usr/bin/env python3
"""
Debug PriceCharting connectivity and search
"""

import requests
from bs4 import BeautifulSoup
import time

def test_basic_connectivity():
    """Test if we can access PriceCharting at all"""
    print("🌐 Testing basic PriceCharting connectivity...")
    
    try:
        response = requests.get("https://www.pricecharting.com", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Can access PriceCharting")
            return True
        else:
            print(f"❌ Got status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_search_page():
    """Test if we can access the search page"""
    print("\n🔍 Testing search page access...")
    
    try:
        # Try a simple search
        search_url = "https://www.pricecharting.com/search-products?q=charizard+pokemon&console=&genre=TCG+Card"
        print(f"   URL: {search_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for any search results
            results = soup.find_all('a')
            print(f"   Found {len(results)} total links")
            
            # Look for specific patterns
            pokemon_links = [link for link in results if 'pokemon' in link.get_text().lower()]
            print(f"   Found {len(pokemon_links)} Pokemon-related links")
            
            if pokemon_links:
                print("   First few Pokemon results:")
                for i, link in enumerate(pokemon_links[:3]):
                    text = link.get_text().strip()
                    href = link.get('href', '')
                    print(f"     {i+1}. {text} -> {href}")
                    
            return True
        else:
            print(f"❌ Search failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

def test_simple_search_terms():
    """Test with very simple search terms"""
    print("\n🧪 Testing simple search terms...")
    
    search_terms = [
        "charizard pokemon",
        "pikachu pokemon", 
        "pokemon card charizard",
        "brilliant stars booster box"
    ]
    
    for term in search_terms:
        print(f"\n   Testing: '{term}'")
        
        try:
            search_url = f"https://www.pricecharting.com/search-products?q={term.replace(' ', '+')}&console=&genre=TCG+Card"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for common PriceCharting elements
                title = soup.find('title')
                if title:
                    print(f"     Page title: {title.get_text()}")
                
                # Look for search results or product links
                links = soup.find_all('a')
                relevant_links = []
                
                for link in links:
                    text = link.get_text().lower()
                    href = link.get('href', '')
                    
                    if any(word in text for word in ['pokemon', 'charizard', 'pikachu', 'card']):
                        if href and href.startswith('/game/'):
                            relevant_links.append((text.strip(), href))
                
                print(f"     Found {len(relevant_links)} relevant results")
                if relevant_links:
                    print(f"     First result: {relevant_links[0][0]} -> {relevant_links[0][1]}")
                    
            else:
                print(f"     ❌ Status: {response.status_code}")
                
            time.sleep(1)  # Be nice to the server
            
        except Exception as e:
            print(f"     ❌ Error: {e}")

if __name__ == "__main__":
    print("🐛 PRICECHARTING DEBUG TEST")
    print("=" * 40)
    
    # Test basic connectivity
    basic_ok = test_basic_connectivity()
    
    if basic_ok:
        # Test search functionality
        search_ok = test_search_page()
        
        if search_ok:
            # Test specific search terms
            test_simple_search_terms()
        else:
            print("\n❌ Search page not accessible")
    else:
        print("\n❌ Cannot access PriceCharting - check internet connection")
    
    print("\n✅ Debug test complete") 