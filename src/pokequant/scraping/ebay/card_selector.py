"""
Card Selector Module
Selects specific cards from the database to track on eBay
"""

import sys
import os
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

class CardSelector:
    """Selects cards from database based on various strategies"""
    
    def __init__(self):
        self.supabase = supabase
    
    def get_high_value_cards(self, min_rarity_rank: int = 3) -> List[Dict[str, Any]]:
        """Get high-value cards based on rarity and popularity"""
        print(f"🎯 Selecting high-value cards (min rarity rank: {min_rarity_rank})...")
        
        try:
            # Query for cards that are likely to be valuable
            # Adjust the query based on your actual pokemon_cards table structure
            result = self.supabase.table("pokemon_cards").select("*").execute()
            
            if result.data:
                print(f"✅ Found {len(result.data)} total cards in database")
                
                # Filter for high-value characteristics
                high_value_cards = []
                for card in result.data:
                    if self._is_high_value_card(card):
                        high_value_cards.append(card)
                
                print(f"🎯 Selected {len(high_value_cards)} high-value cards")
                return high_value_cards
            else:
                print("⚠️ No cards found in database")
                return []
                
        except Exception as e:
            print(f"❌ Error querying cards: {e}")
            return []
    
    def get_cards_by_set(self, set_names: List[str]) -> List[Dict[str, Any]]:
        """Get all cards from specific sets"""
        print(f"📦 Selecting cards from sets: {set_names}")
        
        try:
            cards = []
            for set_name in set_names:
                result = self.supabase.table("pokemon_cards").select("*").eq("set_name", set_name).execute()
                if result.data:
                    cards.extend(result.data)
                    print(f"  ✅ {set_name}: {len(result.data)} cards")
                else:
                    print(f"  ⚠️ {set_name}: No cards found")
            
            print(f"🎯 Total selected: {len(cards)} cards from {len(set_names)} sets")
            return cards
            
        except Exception as e:
            print(f"❌ Error querying sets: {e}")
            return []
    
    def get_cards_by_pokemon(self, pokemon_names: List[str]) -> List[Dict[str, Any]]:
        """Get all cards featuring specific Pokémon"""
        print(f"🐾 Selecting cards for Pokémon: {pokemon_names}")
        
        try:
            cards = []
            for pokemon in pokemon_names:
                # Use ilike for case-insensitive partial matching
                result = self.supabase.table("pokemon_cards").select("*").ilike("card_name", f"%{pokemon}%").execute()
                if result.data:
                    cards.extend(result.data)
                    print(f"  ✅ {pokemon}: {len(result.data)} cards")
                else:
                    print(f"  ⚠️ {pokemon}: No cards found")
            
            # Remove duplicates (same card might match multiple searches)
            unique_cards = self._remove_duplicates(cards)
            print(f"🎯 Total selected: {len(unique_cards)} unique cards")
            return unique_cards
            
        except Exception as e:
            print(f"❌ Error querying Pokémon: {e}")
            return []
    
    def get_sample_cards(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get a small sample of cards for testing"""
        print(f"🧪 Getting {limit} sample cards for testing...")
        
        try:
            result = self.supabase.table("pokemon_cards").select("*").limit(limit).execute()
            
            if result.data:
                print(f"✅ Selected {len(result.data)} sample cards")
                return result.data
            else:
                print("⚠️ No sample cards found")
                return []
                
        except Exception as e:
            print(f"❌ Error getting sample cards: {e}")
            return []
    
    def get_cards_by_custom_filter(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get cards using custom filters"""
        print(f"🔍 Applying custom filters: {filters}")
        
        try:
            query = self.supabase.table("pokemon_cards").select("*")
            
            # Apply filters dynamically
            for field, value in filters.items():
                if isinstance(value, list):
                    query = query.in_(field, value)
                else:
                    query = query.eq(field, value)
            
            result = query.execute()
            
            if result.data:
                print(f"✅ Custom filter returned {len(result.data)} cards")
                return result.data
            else:
                print("⚠️ No cards matched custom filters")
                return []
                
        except Exception as e:
            print(f"❌ Error with custom filter: {e}")
            return []
    
    def _is_high_value_card(self, card: Dict[str, Any]) -> bool:
        """Determine if a card is likely to be high-value"""
        # Adjust these criteria based on your actual data structure
        card_name = card.get('card_name', '').lower()
        rarity = card.get('rarity', '').lower()
        
        # High-value Pokémon
        high_value_pokemon = [
            'charizard', 'pikachu', 'rayquaza', 'lugia', 'mewtwo',
            'mew', 'dragonite', 'gyarados', 'blastoise', 'venusaur'
        ]
        
        # High-value rarities  
        high_value_rarities = [
            'rare holo', 'ultra rare', 'secret rare', 'rainbow rare',
            'gold rare', 'full art', 'alternate art'
        ]
        
        # Check for high-value Pokémon
        for pokemon in high_value_pokemon:
            if pokemon in card_name:
                return True
        
        # Check for high-value rarities
        for rarity_type in high_value_rarities:
            if rarity_type in rarity:
                return True
        
        return False
    
    def _remove_duplicates(self, cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate cards based on card_name + set_name + card_number"""
        seen = set()
        unique_cards = []
        
        for card in cards:
            # Create a unique identifier
            card_id = f"{card.get('card_name', '')}|{card.get('set_name', '')}|{card.get('card_number', '')}"
            
            if card_id not in seen:
                seen.add(card_id)
                unique_cards.append(card)
        
        return unique_cards
    
    def get_tracking_summary(self, cards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of selected cards for tracking"""
        if not cards:
            return {"total": 0}
        
        summary = {
            "total": len(cards),
            "sets": set(),
            "pokemon": set(),
            "rarities": set()
        }
        
        for card in cards:
            if card.get('set_name'):
                summary["sets"].add(card['set_name'])
            if card.get('card_name'):
                summary["pokemon"].add(card['card_name'])
            if card.get('rarity'):
                summary["rarities"].add(card['rarity'])
        
        # Convert sets to lists for JSON serialization
        summary["sets"] = list(summary["sets"])
        summary["pokemon"] = list(summary["pokemon"])
        summary["rarities"] = list(summary["rarities"])
        
        return summary
    
    def get_all_cards_batch(self, batch_size: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all cards from database in batches for comprehensive scraping"""
        print(f"📋 Getting cards batch: size={batch_size}, offset={offset}")
        
        try:
            query = self.supabase.table("pokemon_cards").select("*")
            
            # Apply offset and limit
            if offset > 0:
                query = query.range(offset, offset + batch_size - 1)
            else:
                query = query.limit(batch_size)
            
            result = query.execute()
            
            if result.data:
                print(f"✅ Retrieved {len(result.data)} cards from database")
                return result.data
            else:
                print("⚠️ No cards found in batch")
                return []
                
        except Exception as e:
            print(f"❌ Error getting cards batch: {e}")
            return []
    
    def get_total_card_count(self) -> int:
        """Get total number of cards in database"""
        try:
            result = self.supabase.table("pokemon_cards").select("*", count="exact").execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"❌ Error getting total card count: {e}")
            return 0
    
    def get_curated_investment_targets(self) -> List[Dict[str, Any]]:
        """Get a curated list of specific high-value cards and sealed products for investment tracking"""
        print("💎 Selecting curated investment targets...")
        
        # Specific high-value cards we want to track
        target_cards = [
            # Charizard cards (specific valuable ones)
            {"card_name": "Charizard V", "set_name": "Brilliant Stars", "card_number": "154"},
            {"card_name": "Charizard VSTAR", "set_name": "Brilliant Stars", "card_number": "155"},
            {"card_name": "Charizard", "set_name": "Base Set", "card_number": "4"},
            {"card_name": "Charizard", "set_name": "Base Set 2", "card_number": "4"},
            
            # Pikachu cards (iconic ones)
            {"card_name": "Pikachu V", "set_name": "Scarlet & Violet", "card_number": "220"},
            {"card_name": "Pikachu", "set_name": "Base Set", "card_number": "58"},
            {"card_name": "Pikachu VMAX", "set_name": "Vivid Voltage", "card_number": "188"},
            
            # Modern high-value cards
            {"card_name": "Lugia V", "set_name": "Silver Tempest", "card_number": "138"},
            {"card_name": "Lugia VSTAR", "set_name": "Silver Tempest", "card_number": "139"},
            {"card_name": "Rayquaza V", "set_name": "Evolving Skies", "card_number": "110"},
            {"card_name": "Rayquaza VMAX", "set_name": "Evolving Skies", "card_number": "111"},
            
            # Alternative art cards (highly valuable)
            {"card_name": "Umbreon V", "set_name": "Evolving Skies", "card_number": "189"},
            {"card_name": "Espeon V", "set_name": "Evolving Skies", "card_number": "195"},
            
            # Japanese exclusive/promo cards
            {"card_name": "Pikachu", "set_name": "Promo", "card_number": "SWSH001"},
            {"card_name": "Charizard", "set_name": "Promo", "card_number": "SWSH050"},
        ]
        
        # Find matching cards in database
        found_cards = []
        for target in target_cards:
            try:
                # Try exact match first
                result = self.supabase.table("pokemon_cards").select("*").match({
                    "card_name": target["card_name"],
                    "set_name": target["set_name"],
                    "card_number": target["card_number"]
                }).execute()
                
                if result.data:
                    found_cards.extend(result.data)
                    print(f"  ✅ Found: {target['card_name']} - {target['set_name']} #{target['card_number']}")
                else:
                    # Try partial match if exact fails
                    result = self.supabase.table("pokemon_cards").select("*").ilike(
                        "card_name", f"%{target['card_name']}%"
                    ).ilike("set_name", f"%{target['set_name']}%").execute()
                    
                    if result.data:
                        # Take first match for partial results
                        found_cards.append(result.data[0])
                        print(f"  ⚠️ Partial match: {target['card_name']} - {target['set_name']}")
                    else:
                        print(f"  ❌ Not found: {target['card_name']} - {target['set_name']} #{target['card_number']}")
                        
            except Exception as e:
                print(f"  ❌ Error finding {target['card_name']}: {e}")
        
        # Remove duplicates
        unique_cards = self._remove_duplicates(found_cards)
        print(f"💎 Selected {len(unique_cards)} curated investment targets")
        
        return unique_cards
    
    def get_sealed_products_list(self) -> List[Dict[str, Any]]:
        """Get sealed products from database for tracking"""
        print("📦 Getting sealed products from database...")
        
        try:
            # Query the sealed_products table we created
            result = self.supabase.table("sealed_products").select("*").execute()
            
            if result.data:
                print(f"📦 Found {len(result.data)} sealed products in database")
                return result.data
            else:
                print("⚠️ No sealed products found in database, using fallback list")
                # Fallback to hardcoded list if database is empty
                return self._get_fallback_sealed_products()
                
        except Exception as e:
            print(f"❌ Error querying sealed products: {e}")
            print("⚠️ Using fallback sealed products list")
            return self._get_fallback_sealed_products()
    
    def _get_fallback_sealed_products(self) -> List[Dict[str, Any]]:
        """Fallback sealed products list if database query fails"""
        return [
            {
                "id": 1, 
                "product_name": "Brilliant Stars Booster Box",
                "set_name": "Brilliant Stars",
                "product_type": "Booster Box",
                "msrp": 144.00
            },
            {
                "id": 2,
                "product_name": "Brilliant Stars Elite Trainer Box",
                "set_name": "Brilliant Stars", 
                "product_type": "Elite Trainer Box",
                "msrp": 49.99
            },
            {
                "id": 3,
                "product_name": "Evolving Skies Booster Box", 
                "set_name": "Evolving Skies",
                "product_type": "Booster Box",
                "msrp": 144.00
            },
            {
                "id": 4,
                "product_name": "Evolving Skies Elite Trainer Box",
                "set_name": "Evolving Skies",
                "product_type": "Elite Trainer Box", 
                "msrp": 49.99
            },
            {
                "id": 9,
                "product_name": "Base Set Booster Box",
                "set_name": "Base Set",
                "product_type": "Booster Box", 
                "msrp": 2500.00  # Vintage pricing
            }
        ] 