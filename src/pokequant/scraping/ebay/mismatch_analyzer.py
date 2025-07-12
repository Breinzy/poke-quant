#!/usr/bin/env python3
"""
Mismatch Analyzer
Focused analysis of the specific card mismatch patterns detected
"""

import sys
import os
from typing import List, Dict, Any
from collections import Counter
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

def analyze_dragonite_issue():
    """Analyze the Dragonite VSTAR card number mismatch issue"""
    
    print("🔍 ANALYZING DRAGONITE VSTAR ISSUE")
    print("=" * 50)
    
    try:
        # Get the Dragonite VSTAR card details
        card_result = supabase.table("pokemon_cards").select("*").eq("card_name", "Dragonite VSTAR").execute()
        
        if not card_result.data:
            print("❌ Dragonite VSTAR card not found in database")
            return
        
        card = card_result.data[0]
        print(f"📋 Database Card Details:")
        print(f"   Name: {card.get('card_name')}")
        print(f"   Set: {card.get('set_name')}")
        print(f"   Number: {card.get('card_number')}")
        print(f"   Rarity: {card.get('rarity')}")
        
        # Get listings for this card
        listings_result = supabase.table("ebay_sold_listings").select("*").eq("card_id", card['id']).limit(20).execute()
        
        if not listings_result.data:
            print("❌ No listings found for this card")
            return
        
        print(f"\n📊 Found {len(listings_result.data)} listings")
        
        # Analyze card numbers in titles
        card_numbers = []
        for listing in listings_result.data:
            title = listing.get('title', '')
            numbers = re.findall(r'\b\d+/\d+\b', title)
            card_numbers.extend(numbers)
        
        number_counts = Counter(card_numbers)
        print(f"\n🔢 Card Numbers Found in Titles:")
        for number, count in number_counts.most_common():
            print(f"   {number}: {count} times")
        
        # Show sample titles
        print(f"\n📝 Sample Titles:")
        for i, listing in enumerate(listings_result.data[:5]):
            title = listing.get('title', '')
            search_terms = listing.get('search_terms', '')
            price = listing.get('price', 0)
            print(f"   {i+1}. ${price:.2f} - {title[:80]}...")
            print(f"      Search: {search_terms}")
            print()
        
    except Exception as e:
        print(f"❌ Error analyzing Dragonite issue: {e}")

def analyze_search_precision():
    """Analyze how precise our search terms are"""
    
    print("\n🎯 ANALYZING SEARCH PRECISION")
    print("=" * 50)
    
    try:
        # Get sample of recent listings with search terms
        result = supabase.table("ebay_sold_listings").select("""
            search_terms, title, price,
            pokemon_cards!inner(card_name, set_name, card_number)
        """).order("created_at", desc=True).limit(100).execute()
        
        if not result.data:
            print("❌ No listings found")
            return
        
        # Analyze search term patterns
        search_patterns = {}
        
        for listing in result.data:
            search_terms = listing.get('search_terms', '')
            card_name = listing.get('pokemon_cards', {}).get('card_name', '')
            
            if search_terms and card_name:
                if card_name not in search_patterns:
                    search_patterns[card_name] = []
                search_patterns[card_name].append(search_terms)
        
        print(f"📋 Search Patterns by Card:")
        for card_name, searches in search_patterns.items():
            unique_searches = list(set(searches))
            print(f"\n🎯 {card_name}:")
            for search in unique_searches:
                print(f"   '{search}'")
        
    except Exception as e:
        print(f"❌ Error analyzing search precision: {e}")

def check_card_variants():
    """Check if we have multiple variants of the same card causing confusion"""
    
    print("\n🔄 CHECKING FOR CARD VARIANTS")
    print("=" * 50)
    
    try:
        # Look for cards with similar names
        result = supabase.table("pokemon_cards").select("card_name, set_name, card_number, rarity").execute()
        
        if not result.data:
            print("❌ No cards found")
            return
        
        # Group by base Pokemon name
        pokemon_groups = {}
        
        for card in result.data:
            card_name = card.get('card_name', '')
            
            # Extract base Pokemon name
            base_name = card_name.split()[0] if card_name else ''
            
            if base_name:
                if base_name not in pokemon_groups:
                    pokemon_groups[base_name] = []
                pokemon_groups[base_name].append(card)
        
        # Show Pokemon with multiple variants
        print(f"🔍 Pokemon with Multiple Variants:")
        for pokemon, variants in pokemon_groups.items():
            if len(variants) > 1:
                print(f"\n🎯 {pokemon} ({len(variants)} variants):")
                for variant in variants:
                    print(f"   {variant['card_name']} | {variant['set_name']} | {variant['card_number']}")
        
    except Exception as e:
        print(f"❌ Error checking variants: {e}")

def suggest_search_improvements():
    """Suggest improvements to search terms based on analysis"""
    
    print("\n💡 SEARCH IMPROVEMENT SUGGESTIONS")
    print("=" * 50)
    
    suggestions = [
        "1. Include exact card numbers in search terms to reduce mismatches",
        "2. Use more specific set names instead of generic terms",
        "3. Add negative keywords to exclude wrong variants (e.g., -'076/078' when searching for 081/078)",
        "4. Consider separate searches for different card numbers of the same Pokemon",
        "5. Implement stricter title filtering based on card numbers",
        "6. Add validation to reject listings with wrong card numbers",
        "7. Use set-specific search terms to avoid cross-set contamination"
    ]
    
    for suggestion in suggestions:
        print(f"   {suggestion}")
    
    print(f"\n🎯 PRIORITY FIXES:")
    print(f"   1. Fix Dragonite VSTAR card number (expecting 81, finding 050/076/081)")
    print(f"   2. Add card number validation to quality filter")
    print(f"   3. Review all cards for similar number mismatches")

def main():
    """Main analysis function"""
    
    print("🔍 MISMATCH PATTERN ANALYZER")
    print("=" * 60)
    
    # Analyze specific issues
    analyze_dragonite_issue()
    analyze_search_precision()
    check_card_variants()
    suggest_search_improvements()
    
    print(f"\n{'='*60}")
    print("✅ Mismatch analysis complete!")

if __name__ == "__main__":
    main() 