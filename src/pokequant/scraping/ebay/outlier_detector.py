#!/usr/bin/env python3
"""
Outlier Detector for eBay Listings
Identifies potential card mismatches and price anomalies
"""

import sys
import os
import json
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
import re
import statistics

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

class OutlierDetector:
    """Detects outliers and potential card mismatches in eBay listings"""
    
    def __init__(self):
        self.supabase = supabase
    
    def get_all_listings_with_cards(self) -> List[Dict[str, Any]]:
        """Get all listings with card information"""
        print(f"📋 Fetching all listings with card details...")
        
        try:
            # Get listings with card information
            result = self.supabase.table("ebay_sold_listings").select("""
                *,
                pokemon_cards!inner(card_name, set_name, card_number, rarity)
            """).order("created_at", desc=True).limit(10000).execute()
            
            if result.data:
                print(f"✅ Found {len(result.data)} listings with card details")
                return result.data
            else:
                print("⚠️ No listings found")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching listings: {e}")
            return []
    
    def detect_price_outliers(self, listings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Detect price outliers for each card"""
        
        print(f"🔍 Detecting price outliers...")
        
        # Group by card_id and condition
        card_groups = defaultdict(lambda: defaultdict(list))
        
        for listing in listings:
            card_id = listing.get('card_id')
            condition = self.normalize_condition(listing.get('condition', ''))
            price = float(listing.get('price', 0))
            
            if card_id and price > 0:
                card_groups[card_id][condition].append({
                    'listing': listing,
                    'price': price
                })
        
        outliers = {}
        
        for card_id, conditions in card_groups.items():
            card_outliers = []
            
            for condition, price_data in conditions.items():
                if len(price_data) >= 5:  # Need at least 5 listings to detect outliers
                    prices = [item['price'] for item in price_data]
                    
                    # Calculate IQR method outliers
                    q1 = statistics.quantiles(prices, n=4)[0]  # 25th percentile
                    q3 = statistics.quantiles(prices, n=4)[2]  # 75th percentile
                    iqr = q3 - q1
                    
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    # Also check for extreme outliers (3x IQR)
                    extreme_lower = q1 - 3 * iqr
                    extreme_upper = q3 + 3 * iqr
                    
                    for item in price_data:
                        price = item['price']
                        listing = item['listing']
                        
                        outlier_type = None
                        if price < extreme_lower or price > extreme_upper:
                            outlier_type = 'extreme'
                        elif price < lower_bound or price > upper_bound:
                            outlier_type = 'moderate'
                        
                        if outlier_type:
                            card_outliers.append({
                                'listing': listing,
                                'price': price,
                                'condition': condition,
                                'outlier_type': outlier_type,
                                'q1': q1,
                                'q3': q3,
                                'median': statistics.median(prices),
                                'expected_range': f"${lower_bound:.2f} - ${upper_bound:.2f}"
                            })
            
            if card_outliers:
                outliers[card_id] = card_outliers
        
        return outliers
    
    def detect_title_mismatches(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect potential card name mismatches in titles"""
        
        print(f"🔍 Detecting potential title mismatches...")
        
        mismatches = []
        
        for listing in listings:
            card_name = listing.get('pokemon_cards', {}).get('card_name', '')
            title = listing.get('title', '')
            search_terms = listing.get('search_terms', '')
            
            if not card_name or not title:
                continue
            
            # Check for potential mismatches
            mismatch_reasons = []
            
            # 1. Card name not in title at all
            card_name_clean = self.clean_name_for_matching(card_name)
            title_clean = self.clean_name_for_matching(title)
            
            if not self.fuzzy_name_match(card_name_clean, title_clean):
                mismatch_reasons.append("Card name not found in title")
            
            # 2. Different Pokemon entirely
            expected_pokemon = self.extract_pokemon_name(card_name)
            title_pokemon = self.extract_pokemon_name(title)
            
            if expected_pokemon and title_pokemon and expected_pokemon != title_pokemon:
                mismatch_reasons.append(f"Different Pokemon: expected {expected_pokemon}, found {title_pokemon}")
            
            # 3. Set mismatch (if we can detect it)
            expected_set = listing.get('pokemon_cards', {}).get('set_name', '')
            if expected_set and len(expected_set) > 3:
                set_clean = self.clean_name_for_matching(expected_set)
                if set_clean not in title_clean and not self.fuzzy_name_match(set_clean, title_clean):
                    # Only flag if title mentions a different set
                    if self.contains_set_name(title):
                        mismatch_reasons.append(f"Potential set mismatch: expected {expected_set}")
            
            # 4. Card number mismatch
            expected_number = listing.get('pokemon_cards', {}).get('card_number', '')
            if expected_number:
                title_numbers = re.findall(r'\b\d+/\d+\b', title)
                if title_numbers and expected_number not in title_numbers:
                    mismatch_reasons.append(f"Card number mismatch: expected {expected_number}")
            
            if mismatch_reasons:
                mismatches.append({
                    'listing': listing,
                    'card_name': card_name,
                    'title': title,
                    'search_terms': search_terms,
                    'mismatch_reasons': mismatch_reasons,
                    'confidence': len(mismatch_reasons)  # More reasons = higher confidence it's wrong
                })
        
        return mismatches
    
    def normalize_condition(self, condition: str) -> str:
        """Normalize condition strings"""
        condition = condition.lower().strip()
        
        if 'psa 10' in condition or condition == 'psa 10':
            return 'PSA 10'
        elif 'psa 9' in condition or condition == 'psa 9':
            return 'PSA 9'
        elif 'psa' in condition:
            return 'PSA Other'
        elif 'bgs' in condition or 'bgS' in condition:
            return 'BGS'
        elif 'cgc' in condition:
            return 'CGC'
        elif condition in ['new (other)', 'new', 'mint']:
            return 'Raw NM'
        elif condition in ['pre-owned', 'used']:
            return 'Raw Used'
        else:
            return 'Other'
    
    def clean_name_for_matching(self, name: str) -> str:
        """Clean name for fuzzy matching"""
        if not name:
            return ""
        
        # Convert to lowercase and remove special characters
        clean = re.sub(r'[^\w\s]', ' ', name.lower())
        # Remove extra whitespace
        clean = ' '.join(clean.split())
        return clean
    
    def fuzzy_name_match(self, name1: str, name2: str) -> bool:
        """Check if two names match fuzzily"""
        if not name1 or not name2:
            return False
        
        # Direct substring match
        if name1 in name2 or name2 in name1:
            return True
        
        # Word-based matching
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        # Remove common words
        common_words = {'pokemon', 'card', 'tcg', 'holo', 'rare', 'ex', 'gx', 'v', 'vmax', 'vstar'}
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        if not words1 or not words2:
            return False
        
        # Check if significant overlap
        overlap = len(words1.intersection(words2))
        min_words = min(len(words1), len(words2))
        
        return overlap / min_words >= 0.6  # 60% word overlap
    
    def extract_pokemon_name(self, text: str) -> str:
        """Extract the main Pokemon name from text"""
        if not text:
            return ""
        
        # Common Pokemon name patterns
        text_clean = self.clean_name_for_matching(text)
        
        # Look for Pokemon names (simplified - would need full list for production)
        pokemon_names = [
            'charizard', 'pikachu', 'mew', 'mewtwo', 'lugia', 'rayquaza', 'dragonite',
            'blastoise', 'venusaur', 'gyarados', 'alakazam', 'machamp', 'gengar',
            'eevee', 'vaporeon', 'jolteon', 'flareon', 'espeon', 'umbreon',
            'leafeon', 'glaceon', 'sylveon'
        ]
        
        for pokemon in pokemon_names:
            if pokemon in text_clean:
                return pokemon
        
        # If no match, try to extract first word (often the Pokemon name)
        words = text_clean.split()
        if words:
            return words[0]
        
        return ""
    
    def contains_set_name(self, title: str) -> bool:
        """Check if title contains a set name"""
        title_lower = title.lower()
        
        # Common set indicators
        set_indicators = [
            'base set', 'jungle', 'fossil', 'team rocket', 'gym heroes', 'gym challenge',
            'neo genesis', 'neo discovery', 'neo destiny', 'neo revelation',
            'expedition', 'aquapolis', 'skyridge', 'ruby sapphire', 'sandstorm',
            'dragon', 'team magma', 'team aqua', 'hidden legends', 'firered leafgreen',
            'team rocket returns', 'deoxys', 'emerald', 'unseen forces', 'delta species',
            'legend maker', 'holon phantoms', 'crystal guardians', 'dragon frontiers',
            'power keepers', 'diamond pearl', 'mysterious treasures', 'secret wonders',
            'great encounters', 'majestic dawn', 'legends awakened', 'stormfront',
            'platinum', 'rising rivals', 'supreme victors', 'arceus', 'heartgold soulsilver',
            'unleashed', 'undaunted', 'triumphant', 'black white', 'emerging powers',
            'noble victories', 'next destinies', 'dark explorers', 'dragons exalted',
            'boundaries crossed', 'plasma storm', 'plasma freeze', 'plasma blast',
            'legendary treasures', 'xy', 'flashfire', 'furious fists', 'phantom forces',
            'primal clash', 'roaring skies', 'ancient origins', 'breakthrough',
            'breakpoint', 'generations', 'fates collide', 'steam siege', 'evolutions',
            'sun moon', 'guardians rising', 'burning shadows', 'shining legends',
            'crimson invasion', 'ultra prism', 'forbidden light', 'celestial storm',
            'dragon majesty', 'lost thunder', 'team up', 'detective pikachu',
            'unbroken bonds', 'unified minds', 'hidden fates', 'cosmic eclipse',
            'sword shield', 'rebel clash', 'darkness ablaze', 'champions path',
            'vivid voltage', 'shining fates', 'battle styles', 'chilling reign',
            'evolving skies', 'celebrations', 'fusion strike', 'brilliant stars',
            'astral radiance', 'pokemon go', 'lost origin', 'silver tempest',
            'crown zenith', 'paldea evolved', 'obsidian flames', 'paradox rift'
        ]
        
        return any(set_name in title_lower for set_name in set_indicators)
    
    def print_outlier_report(self, price_outliers: Dict[str, List], title_mismatches: List):
        """Print comprehensive outlier report"""
        
        print(f"\n{'='*80}")
        print(f"🚨 OUTLIER DETECTION REPORT")
        print(f"{'='*80}")
        
        # Price outliers
        total_price_outliers = sum(len(outliers) for outliers in price_outliers.values())
        print(f"\n💰 PRICE OUTLIERS: {total_price_outliers}")
        
        if price_outliers:
            # Get card names
            card_ids = list(price_outliers.keys())
            try:
                result = self.supabase.table("pokemon_cards").select("id, card_name").in_("id", card_ids).execute()
                card_names = {card['id']: card['card_name'] for card in result.data} if result.data else {}
            except:
                card_names = {}
            
            for card_id, outliers in price_outliers.items():
                card_name = card_names.get(card_id, f"Unknown ({card_id[:8]}...)")
                print(f"\n🎯 {card_name} ({len(outliers)} outliers):")
                
                # Group by outlier type
                extreme = [o for o in outliers if o['outlier_type'] == 'extreme']
                moderate = [o for o in outliers if o['outlier_type'] == 'moderate']
                
                if extreme:
                    print(f"   🔴 EXTREME OUTLIERS ({len(extreme)}):")
                    for outlier in extreme[:3]:  # Show top 3
                        listing = outlier['listing']
                        print(f"      ${outlier['price']:.2f} | {outlier['condition']} | Expected: {outlier['expected_range']}")
                        print(f"      Title: {listing.get('title', '')[:80]}...")
                
                if moderate:
                    print(f"   🟡 MODERATE OUTLIERS ({len(moderate)}):")
                    for outlier in moderate[:2]:  # Show top 2
                        listing = outlier['listing']
                        print(f"      ${outlier['price']:.2f} | {outlier['condition']} | Expected: {outlier['expected_range']}")
        
        # Title mismatches
        print(f"\n🏷️ TITLE MISMATCHES: {len(title_mismatches)}")
        
        if title_mismatches:
            # Sort by confidence (more reasons = higher confidence it's wrong)
            sorted_mismatches = sorted(title_mismatches, key=lambda x: x['confidence'], reverse=True)
            
            print(f"\n🔴 HIGH CONFIDENCE MISMATCHES:")
            high_confidence = [m for m in sorted_mismatches if m['confidence'] >= 2]
            
            for i, mismatch in enumerate(high_confidence[:10]):  # Show top 10
                print(f"\n   {i+1}. Expected: {mismatch['card_name']}")
                print(f"      Title: {mismatch['title'][:100]}...")
                print(f"      Issues: {', '.join(mismatch['mismatch_reasons'])}")
                print(f"      Search: {mismatch['search_terms']}")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"📊 OUTLIER SUMMARY:")
        print(f"   Price outliers: {total_price_outliers}")
        print(f"   Title mismatches: {len(title_mismatches)}")
        
        high_confidence_mismatches = len([m for m in title_mismatches if m['confidence'] >= 2])
        print(f"   High confidence mismatches: {high_confidence_mismatches}")
        
        if total_price_outliers + high_confidence_mismatches == 0:
            print(f"   ✅ No significant outliers detected!")
        elif total_price_outliers + high_confidence_mismatches < 50:
            print(f"   ⚠️ Few outliers detected - data quality looks good")
        else:
            print(f"   🚨 Many outliers detected - review recommended")

def main():
    """Main function"""
    
    print("🚨 EBAY LISTINGS OUTLIER DETECTOR")
    print("=" * 50)
    
    detector = OutlierDetector()
    
    # Get all listings with card details
    listings = detector.get_all_listings_with_cards()
    
    if not listings:
        print("❌ No listings found")
        return
    
    # Detect price outliers
    price_outliers = detector.detect_price_outliers(listings)
    
    # Detect title mismatches
    title_mismatches = detector.detect_title_mismatches(listings)
    
    # Print report
    detector.print_outlier_report(price_outliers, title_mismatches)
    
    print(f"\n✅ Outlier detection complete!")

if __name__ == "__main__":
    main() 