#!/usr/bin/env python3
"""
Debug eBay Quality Filter Issues
Investigate why the quality filter is rejecting all listings
"""

import sys
import os
import json
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from listing_quality_filter import ListingQualityFilter
from ebay_parser import eBayParser
from ebay_search import eBaySearcher

def debug_sample_listings():
    """Test the quality filter with real eBay search results"""
    
    print("🔍 DEBUGGING EBAY QUALITY FILTER")
    print("="*50)
    
    # Initialize components
    searcher = eBaySearcher()
    parser = eBayParser()
    quality_filter = ListingQualityFilter()
    
    # Test search terms that were failing
    test_searches = [
        ("Charizard V Brilliant Stars 154 pokemon", "Charizard V"),
        ("Charizard V Brilliant Stars pokemon", "Charizard V"),
        ("Pikachu VMAX Vivid Voltage 188", "Pikachu VMAX")
    ]
    
    for search_term, expected_card in test_searches:
        print(f"\n🎯 Testing search: '{search_term}'")
        print(f"   Expected card: '{expected_card}'")
        print("-" * 40)
        
        try:
            # Perform search (just 1 page, limited results)
            search_results = searcher.search_sold_listings(
                search_term,
                max_pages=1,
                max_results=10
            )
            
            if not search_results:
                print("  ❌ No search results")
                continue
            
            # Parse listings
            all_listings = []
            for page_html in search_results:
                page_listings = parser.parse_listing_html(page_html)
                all_listings.extend(page_listings)
            
            print(f"  📊 Found {len(all_listings)} raw listings")
            
            if not all_listings:
                print("  ❌ No parsed listings")
                continue
            
            # Examine first few listings in detail
            print(f"\n  📋 Sample listing titles:")
            for i, listing in enumerate(all_listings[:5]):
                title = listing.get('title', 'NO TITLE')
                price = listing.get('price', 0)
                print(f"    {i+1}. ${price} - {title}")
            
            # Test quality filter WITHOUT expected card name first
            print(f"\n  🔍 Testing quality filter (no card name filter):")
            valid_listings_no_filter, rejection_stats_no_filter = quality_filter.filter_listings_batch(all_listings)
            
            print(f"    Valid without card filter: {len(valid_listings_no_filter)}/{len(all_listings)}")
            if rejection_stats_no_filter:
                print(f"    Rejection reasons:")
                for reason, count in rejection_stats_no_filter.items():
                    print(f"      • {reason}: {count}")
            
            # Test quality filter WITH expected card name
            print(f"\n  🔍 Testing quality filter (with card name: '{expected_card}'):")
            valid_listings_with_filter, rejection_stats_with_filter = quality_filter.filter_listings_batch(all_listings, expected_card)
            
            print(f"    Valid with card filter: {len(valid_listings_with_filter)}/{len(all_listings)}")
            if rejection_stats_with_filter:
                print(f"    Rejection reasons:")
                for reason, count in rejection_stats_with_filter.items():
                    print(f"      • {reason}: {count}")
            
            # Detailed analysis of first few listings
            print(f"\n  🔬 Detailed analysis of first 3 listings:")
            for i, listing in enumerate(all_listings[:3]):
                title = listing.get('title', 'NO TITLE')
                price = listing.get('price', 0)
                
                print(f"    Listing {i+1}: ${price}")
                print(f"      Title: {title}")
                
                # Test without card name
                result_no_card = quality_filter.filter_listing(listing)
                print(f"      No card filter: {'✅' if result_no_card.is_valid else '❌'} - {result_no_card.reason}")
                
                # Test with card name
                result_with_card = quality_filter.filter_listing(listing, expected_card)
                print(f"      With card filter: {'✅' if result_with_card.is_valid else '❌'} - {result_with_card.reason}")
                
                # Check specific conditions
                title_lower = title.lower()
                has_pokemon_word = 'pokemon' in title_lower
                has_pokemon_name = any(name in title_lower for name in quality_filter.pokemon_names)
                has_expected_card = expected_card.lower() in title_lower if expected_card else False
                
                print(f"      Analysis:")
                print(f"        • Contains 'pokemon': {has_pokemon_word}")
                print(f"        • Contains Pokemon name: {has_pokemon_name}")
                print(f"        • Contains expected card '{expected_card}': {has_expected_card}")
                print()
                
        except Exception as e:
            print(f"  ❌ Error testing '{search_term}': {e}")

def test_quality_filter_patterns():
    """Test the quality filter patterns against realistic titles"""
    
    print(f"\n🧪 TESTING QUALITY FILTER PATTERNS")
    print("="*50)
    
    quality_filter = ListingQualityFilter()
    
    # Sample realistic Pokemon card titles
    test_titles = [
        # Should PASS
        "2022 Pokemon Sword & Shield Brilliant Stars Charizard V #154 PSA 10",
        "Pokemon Charizard V 154/172 Brilliant Stars Alt Art Ultra Rare NM",
        "Charizard V 154/172 Alt Art Sword & Shield: Brilliant Stars Pokemon TCG NM",
        "Pokemon Pikachu VMAX 188/185 Vivid Voltage Secret Rare Rainbow Holo",
        "Pikachu VMAX 188/185 Vivid Voltage Rainbow Rare Pokemon Card NM/M",
        
        # Borderline cases (might fail due to missing 'pokemon' word)
        "Charizard V 154/172 Brilliant Stars Alt Art Ultra Rare NM Sword Shield",
        "Pikachu VMAX 188/185 Vivid Voltage Secret Rare Rainbow Holo Card",
        "Rayquaza V 110/203 Evolving Skies Ultra Rare Holo Card NM",
        
        # Should FAIL  
        "34 Pokemon Card Lot Mixed Condition Vintage",
        "Pokemon Card Collection 100+ Cards Bulk Sale",
        "Charizard V Damaged Creased Water Damage As Is",
        "Pokemon Card Sleeves Ultra Pro Deck Protectors",
        "Mystery Pokemon Card Pack Random Booster"
    ]
    
    for title in test_titles:
        print(f"\n📋 Testing: {title}")
        
        # Test basic filtering (no expected card)
        listing = {'title': title, 'price': 25.0}
        result = quality_filter.filter_listing(listing)
        
        print(f"  Basic filter: {'✅' if result.is_valid else '❌'} - {result.reason}")
        
        # Test specific card filtering
        if 'charizard' in title.lower():
            card_result = quality_filter.filter_listing(listing, "Charizard V")
            print(f"  Card filter (Charizard V): {'✅' if card_result.is_valid else '❌'} - {card_result.reason}")
        elif 'pikachu' in title.lower():
            card_result = quality_filter.filter_listing(listing, "Pikachu VMAX")
            print(f"  Card filter (Pikachu VMAX): {'✅' if card_result.is_valid else '❌'} - {card_result.reason}")

def analyze_pokemon_name_coverage():
    """Analyze if our Pokemon name list is comprehensive enough"""
    
    print(f"\n📊 ANALYZING POKEMON NAME COVERAGE")
    print("="*50)
    
    quality_filter = ListingQualityFilter()
    
    # Common Pokemon that might be missing from our list
    additional_pokemon = [
        'charizard', 'pikachu', 'blastoise', 'venusaur',  # Starter evolutions
        'mewtwo', 'mew', 'lugia', 'ho-oh',  # Legendaries
        'rayquaza', 'groudon', 'kyogre',  # Hoenn legendaries
        'dialga', 'palkia', 'giratina',  # Sinnoh legendaries
        'reshiram', 'zekrom', 'kyurem',  # Unova legendaries
        'xerneas', 'yveltal', 'zygarde',  # Kalos legendaries
        'solgaleo', 'lunala', 'necrozma',  # Alola legendaries
        'zacian', 'zamazenta', 'eternatus'  # Galar legendaries
    ]
    
    print(f"Current Pokemon list size: {len(quality_filter.pokemon_names)}")
    print(f"Checking coverage for common Pokemon:")
    
    for pokemon in additional_pokemon:
        in_list = pokemon in quality_filter.pokemon_names
        status = "✅" if in_list else "❌"
        print(f"  {status} {pokemon}")
        
    # Check for variations (V, VMAX, etc.)
    print(f"\nCard type suffixes: {quality_filter.card_types}")

def propose_quality_filter_fixes():
    """Propose fixes for the quality filter"""
    
    print(f"\n🔧 PROPOSED QUALITY FILTER FIXES")
    print("="*50)
    
    fixes = [
        "1. Relax Pokemon name requirement:",
        "   - Allow 'TCG' or 'trading card' instead of requiring specific Pokemon names",
        "   - Look for card numbers (e.g., '154/172') as Pokemon indicator",
        "",
        "2. Improve card name matching:",
        "   - Case-insensitive matching",
        "   - Allow partial matches (e.g., 'Charizard' matches 'Charizard V')",
        "   - Handle common variations and abbreviations",
        "",
        "3. Expand Pokemon name list:",
        "   - Add missing popular Pokemon",
        "   - Include common misspellings",
        "   - Add card-specific terms (V, VMAX, VSTAR, EX, GX)",
        "",
        "4. Better pattern matching:",
        "   - Look for 'TCG', 'Pokemon TCG', 'Pokemon Card'",
        "   - Recognize grading companies (PSA, BGS, CGC, SGC)",
        "   - Identify set names and card numbers",
        "",
        "5. Adjust confidence scoring:",
        "   - Lower the threshold for requiring 'pokemon' in title",
        "   - Give higher weight to graded cards and specific card numbers",
        "   - Consider search context (if we searched for 'Charizard V', expect that in results)"
    ]
    
    for fix in fixes:
        print(fix)

def main():
    """Run all debug tests"""
    
    # Test with sample search results
    debug_sample_listings()
    
    # Test filter patterns
    test_quality_filter_patterns()
    
    # Analyze Pokemon name coverage
    analyze_pokemon_name_coverage()
    
    # Propose fixes
    propose_quality_filter_fixes()

if __name__ == "__main__":
    main() 