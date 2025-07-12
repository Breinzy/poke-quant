#!/usr/bin/env python3
"""
Test the fixed eBay parser
"""

from ebay_parser import eBayParser

def test_parser():
    print("🔧 TESTING FIXED EBAY PARSER")
    print("="*50)
    
    parser = eBayParser()
    
    # Read the HTML file
    with open('debug_fresh_ebay_html.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    print(f"📄 HTML size: {len(html):,} characters")
    
    # Parse the listings
    listings = parser.parse_listing_html(html, 'Charizard V')
    
    print(f"🎯 EXTRACTED {len(listings)} LISTINGS")
    print()
    
    # Show first 5 listings
    for i, listing in enumerate(listings[:5]):
        title = listing['title'][:80] + '...' if len(listing['title']) > 80 else listing['title']
        price = listing['price']
        sold_date = listing.get('sold_date', 'N/A')
        print(f"{i+1}. {title}")
        print(f"   💰 Price: ${price}")
        print(f"   📅 Sold: {sold_date}")
        print()
    
    if len(listings) > 5:
        print(f"... and {len(listings) - 5} more listings")
    
    return len(listings)

if __name__ == "__main__":
    test_parser() 