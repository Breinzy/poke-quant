#!/usr/bin/env python3
"""
Test Sealed Product Detection and Routing
"""

from card_selector import CardSelector
from ebay_to_supabase import eBaySupabaseUploader

def test_sealed_product_detection():
    print("🔍 TESTING SEALED PRODUCT DETECTION:")
    print("=" * 50)
    
    selector = CardSelector()
    uploader = eBaySupabaseUploader()
    
    # Get curated targets (mix of cards + sealed products)
    curated_items = selector.get_curated_investment_targets()
    sealed_products = selector.get_sealed_products_list()
    
    print(f"📊 Curated cards: {len(curated_items)}")
    print(f"📦 Sealed products: {len(sealed_products)}")
    
    # Test first few items from each
    print("\n🎯 TESTING CARD DETECTION:")
    for i, item in enumerate(curated_items[:3]):
        is_sealed = 'product_type' in item
        item_name = item.get('card_name', 'Unknown')
        print(f"  {i+1}. {item_name} - Sealed? {is_sealed}")
        print(f"     Fields: {list(item.keys())}")
        
        # Test listing count method
        try:
            if is_sealed:
                count = uploader.get_sealed_product_listing_count(item['id'])
                print(f"     Listing count (sealed): {count}")
            else:
                count = uploader.get_card_listing_count(item['id'])
                print(f"     Listing count (card): {count}")
        except Exception as e:
            print(f"     ❌ Error getting count: {e}")
        print()
    
    print("\n📦 TESTING SEALED PRODUCT DETECTION:")
    for i, item in enumerate(sealed_products[:3]):
        is_sealed = 'product_type' in item
        item_name = item.get('product_name', 'Unknown')
        print(f"  {i+1}. {item_name} - Sealed? {is_sealed}")
        print(f"     Fields: {list(item.keys())}")
        
        # Test listing count method
        try:
            if is_sealed:
                count = uploader.get_sealed_product_listing_count(item['id'])
                print(f"     Listing count (sealed): {count}")
            else:
                count = uploader.get_card_listing_count(item['id'])
                print(f"     Listing count (card): {count}")
        except Exception as e:
            print(f"     ❌ Error getting count: {e}")
        print()

if __name__ == "__main__":
    test_sealed_product_detection() 