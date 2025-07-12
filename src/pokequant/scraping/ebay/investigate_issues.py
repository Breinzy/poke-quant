#!/usr/bin/env python3
"""
Investigate Specific Issues
Focus on the $2 card problem and card number mismatches
"""

import sys
import os
from typing import List, Dict, Any
from collections import Counter
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

def investigate_low_price_cards():
    """Investigate suspiciously low-priced cards"""
    
    print("🔍 INVESTIGATING LOW-PRICED CARDS")
    print("=" * 50)
    
    try:
        # Get listings under $10
        result = supabase.table("ebay_sold_listings").select("""
            *,
            pokemon_cards!inner(card_name, set_name, card_number, rarity)
        """).lt("price", 10).order("price", desc=False).limit(20).execute()
        
        if not result.data:
            print("❌ No low-priced listings found")
            return
        
        print(f"📊 Found {len(result.data)} listings under $10:")
        print()
        
        for i, listing in enumerate(result.data):
            price = listing.get('price', 0)
            title = listing.get('title', '')
            card_name = listing.get('pokemon_cards', {}).get('card_name', '')
            set_name = listing.get('pokemon_cards', {}).get('set_name', '')
            rarity = listing.get('pokemon_cards', {}).get('rarity', '')
            search_terms = listing.get('search_terms', '')
            condition = listing.get('condition', '')
            
            print(f"   {i+1}. ${price:.2f} | {condition}")
            print(f"      Expected: {card_name} | {set_name} | {rarity}")
            print(f"      Title: {title[:80]}...")
            print(f"      Search: {search_terms}")
            print()
        
    except Exception as e:
        print(f"❌ Error investigating low prices: {e}")

def investigate_dragonite_numbers():
    """Investigate the Dragonite card number issue specifically"""
    
    print("\n🐉 INVESTIGATING DRAGONITE CARD NUMBERS")
    print("=" * 50)
    
    try:
        # Get all Dragonite cards in database
        cards_result = supabase.table("pokemon_cards").select("*").ilike("card_name", "%dragonite%").execute()
        
        if cards_result.data:
            print(f"📋 Dragonite cards in database:")
            for card in cards_result.data:
                print(f"   {card['card_name']} | {card['set_name']} | #{card['card_number']} | {card['rarity']}")
            print()
        
        # Get Dragonite listings and analyze card numbers in titles
        listings_result = supabase.table("ebay_sold_listings").select("""
            *,
            pokemon_cards!inner(card_name, set_name, card_number)
        """).ilike("pokemon_cards.card_name", "%dragonite%").limit(30).execute()
        
        if not listings_result.data:
            print("❌ No Dragonite listings found")
            return
        
        print(f"📊 Analyzing {len(listings_result.data)} Dragonite listings:")
        
        # Extract card numbers from titles
        number_analysis = {}
        
        for listing in listings_result.data:
            title = listing.get('title', '')
            expected_card = listing.get('pokemon_cards', {})
            expected_number = expected_card.get('card_number', '')
            
            # Find all card numbers in title
            found_numbers = re.findall(r'\b\d+/\d+\b', title)
            
            key = f"{expected_card.get('card_name', '')} (expects #{expected_number})"
            if key not in number_analysis:
                number_analysis[key] = {'found_numbers': [], 'titles': []}
            
            number_analysis[key]['found_numbers'].extend(found_numbers)
            number_analysis[key]['titles'].append({
                'title': title,
                'price': listing.get('price', 0),
                'found_numbers': found_numbers
            })
        
        # Show analysis
        for card_key, data in number_analysis.items():
            print(f"\n🎯 {card_key}:")
            
            # Count found numbers
            number_counts = Counter(data['found_numbers'])
            print(f"   Card numbers found in titles:")
            for number, count in number_counts.most_common():
                print(f"     {number}: {count} times")
            
            # Show sample titles
            print(f"   Sample titles:")
            for i, title_data in enumerate(data['titles'][:3]):
                print(f"     ${title_data['price']:.2f} | Numbers: {title_data['found_numbers']}")
                print(f"     {title_data['title'][:70]}...")
        
    except Exception as e:
        print(f"❌ Error investigating Dragonite: {e}")

def check_premium_card_selection():
    """Check if our premium card selection is working correctly"""
    
    print("\n💎 CHECKING PREMIUM CARD SELECTION")
    print("=" * 50)
    
    try:
        # Get the cards we're scraping
        result = supabase.table("ebay_sold_listings").select("""
            card_id,
            pokemon_cards!inner(card_name, set_name, rarity)
        """).limit(1000).execute()
        
        if not result.data:
            print("❌ No listings found")
            return
        
        # Analyze rarities
        rarity_counts = Counter()
        cards_by_rarity = {}
        
        for listing in result.data:
            card_data = listing.get('pokemon_cards', {})
            rarity = card_data.get('rarity', 'Unknown')
            card_name = card_data.get('card_name', '')
            
            rarity_counts[rarity] += 1
            
            if rarity not in cards_by_rarity:
                cards_by_rarity[rarity] = set()
            cards_by_rarity[rarity].add(card_name)
        
        print(f"📊 Rarity distribution in scraped data:")
        for rarity, count in rarity_counts.most_common():
            unique_cards = len(cards_by_rarity.get(rarity, set()))
            print(f"   {rarity}: {count} listings ({unique_cards} unique cards)")
        
        print(f"\n🎯 Cards by rarity:")
        for rarity, cards in cards_by_rarity.items():
            if rarity in ['Double Rare', 'Illustration Rare', 'Special Illustration Rare', 'Hyper Rare']:
                print(f"\n   {rarity}:")
                for card in sorted(cards):
                    print(f"     {card}")
        
    except Exception as e:
        print(f"❌ Error checking premium selection: {e}")

def analyze_price_vs_rarity():
    """Analyze if low prices correlate with specific rarities or issues"""
    
    print("\n💰 ANALYZING PRICE VS RARITY")
    print("=" * 50)
    
    try:
        # Get all listings with price and rarity
        result = supabase.table("ebay_sold_listings").select("""
            price, condition,
            pokemon_cards!inner(card_name, rarity)
        """).order("price", desc=False).limit(100).execute()
        
        if not result.data:
            print("❌ No listings found")
            return
        
        # Group by price ranges
        price_ranges = {
            'Under $5': [],
            '$5-$10': [],
            '$10-$25': [],
            '$25-$50': [],
            '$50+': []
        }
        
        for listing in result.data:
            price = float(listing.get('price', 0))
            card_data = listing.get('pokemon_cards', {})
            rarity = card_data.get('rarity', 'Unknown')
            card_name = card_data.get('card_name', '')
            condition = listing.get('condition', '')
            
            entry = f"{card_name} ({rarity}) - {condition}"
            
            if price < 5:
                price_ranges['Under $5'].append(entry)
            elif price < 10:
                price_ranges['$5-$10'].append(entry)
            elif price < 25:
                price_ranges['$10-$25'].append(entry)
            elif price < 50:
                price_ranges['$25-$50'].append(entry)
            else:
                price_ranges['$50+'].append(entry)
        
        for range_name, entries in price_ranges.items():
            if entries:
                print(f"\n💵 {range_name} ({len(entries)} listings):")
                for entry in entries[:5]:  # Show first 5
                    print(f"   {entry}")
                if len(entries) > 5:
                    print(f"   ... and {len(entries) - 5} more")
        
    except Exception as e:
        print(f"❌ Error analyzing price vs rarity: {e}")

def main():
    """Main investigation function"""
    
    print("🔍 INVESTIGATING SPECIFIC ISSUES")
    print("=" * 60)
    
    investigate_low_price_cards()
    investigate_dragonite_numbers()
    check_premium_card_selection()
    analyze_price_vs_rarity()
    
    print(f"\n{'='*60}")
    print("✅ Investigation complete!")

if __name__ == "__main__":
    main() 