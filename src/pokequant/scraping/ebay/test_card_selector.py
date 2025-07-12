#!/usr/bin/env python3
"""
Test script for card selector
"""

from card_selector import CardSelector

def test_card_selector():
    print("🧪 Testing Card Selector")
    print("=" * 30)
    
    try:
        selector = CardSelector()
        
        # Test curated cards
        print("\n🎯 Testing curated investment targets...")
        cards = selector.get_curated_investment_targets()
        print(f"Found {len(cards)} curated cards")
        
        if cards:
            print("\nFirst 3 cards found:")
            for i, card in enumerate(cards[:3]):
                name = card.get('card_name', 'Unknown')
                set_name = card.get('set_name', 'Unknown') 
                number = card.get('card_number', '?')
                card_id = card.get('id', 'no-id')
                print(f"  {i+1}. {name} - {set_name} #{number} (ID: {card_id})")
        else:
            print("❌ No curated cards found in database")
            
        # Test sealed products
        print("\n📦 Testing sealed products...")
        sealed = selector.get_sealed_products_list()
        print(f"Found {len(sealed)} sealed products")
        
        if sealed:
            print("\nFirst sealed product:")
            product = sealed[0]
            name = product.get('product_name', 'Unknown')
            prod_type = product.get('product_type', 'Unknown')
            print(f"  1. {name} ({prod_type})")
        
        print(f"\n✅ Card selector test complete!")
        return len(cards) > 0 or len(sealed) > 0
        
    except Exception as e:
        print(f"❌ Error testing card selector: {e}")
        return False

if __name__ == "__main__":
    test_card_selector() 