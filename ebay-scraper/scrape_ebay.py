#!/usr/bin/env python3
"""
eBay Scraper - Main Entry Point
Runs the scraper loop to fetch sold listings from eBay
"""

import sys
import os

# Add current directory to path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from ebay_search import eBaySearcher

def main():
    """Main scraper function"""
    print("🕵️‍♂️ eBay Scraper v2 - Starting...")
    
    # Phase 2 test: Search functionality
    print("\n📋 Phase 2: Testing Search & Fetch...")
    
    searcher = eBaySearcher()
    
    # Test URL building
    test_url = searcher.build_search_url("charizard pokemon card", page=1, min_price=50)
    print(f"🔗 Test URL: {test_url}")
    
    # Test a small search (1 page only for testing)
    print("\n🧪 Testing search with 1 page...")
    try:
        html_pages = searcher.search_sold_listings("pikachu pokemon card", max_pages=1)
        
        if html_pages:
            print(f"✅ Successfully fetched {len(html_pages)} page(s)")
            print(f"📏 First page length: {len(html_pages[0])} characters")
            
            # Quick check for expected content
            if "eBay" in html_pages[0] and "sold" in html_pages[0].lower():
                print("✅ Content appears to be valid eBay search results")
            else:
                print("⚠️ Content may not be valid eBay results")
        else:
            print("❌ No pages retrieved")
            
    except Exception as e:
        print(f"❌ Search test failed: {e}")
    
    print("\n📝 Phase 2 Complete - Search & Fetch implemented")

if __name__ == "__main__":
    main() 