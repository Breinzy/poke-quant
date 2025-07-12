#!/usr/bin/env python3
"""
Test Sealed Product Upload Directly
"""

from card_selector import CardSelector
from search_generator import SearchGenerator
from ebay_search import eBaySearcher
from ebay_parser import eBayParser
from ebay_to_supabase import eBaySupabaseUploader

def test_sealed_product_upload():
    print("📦 TESTING SEALED PRODUCT UPLOAD DIRECTLY")
    print("=" * 60)
    
    # Initialize components
    selector = CardSelector()
    search_gen = SearchGenerator()
    searcher = eBaySearcher()
    parser = eBayParser()
    uploader = eBaySupabaseUploader()
    
    # Get first sealed product
    sealed_products = selector.get_sealed_products_list()
    if not sealed_products:
        print("❌ No sealed products found!")
        return
    
    product = sealed_products[0]  # Brilliant Stars Booster Box
    product_id = product['id']
    product_name = product['product_name']
    
    print(f"🎯 Testing with: {product_name} (ID: {product_id})")
    print(f"📋 Product fields: {list(product.keys())}")
    
    # Test detection
    is_sealed = 'product_type' in product
    print(f"✅ Detected as sealed product: {is_sealed}")
    
    # Generate search terms
    search_terms_list = search_gen.generate_search_terms(product)
    print(f"🔍 Generated {len(search_terms_list)} search terms:")
    for i, term in enumerate(search_terms_list[:3], 1):
        print(f"  {i}. '{term}'")
    
    # Test one search
    test_search = search_terms_list[0]
    print(f"\n🔎 Testing search: '{test_search}'")
    
    try:
        # Search eBay (limited results for testing)
        search_results = searcher.search_sold_listings(test_search, max_pages=1, max_results=10)
        
        if not search_results:
            print("❌ No search results returned")
            return
        
        print(f"✅ Got {len(search_results)} pages of results")
        
        # Parse listings
        all_listings = []
        for page_html in search_results:
            page_listings = parser.parse_listing_html(page_html)
            all_listings.extend(page_listings)
        
        print(f"📋 Parsed {len(all_listings)} listings")
        
        if not all_listings:
            print("❌ No listings parsed")
            return
        
        # Show sample listing
        sample = all_listings[0]
        print(f"📝 Sample listing: {sample['title'][:60]}... - ${sample['price']}")
        
        # Test upload using sealed product method
        print(f"\n📤 Testing upload to sealed product table...")
        success = uploader.upload_sealed_product_listings(all_listings, product_id, test_search)
        
        if success:
            print(f"✅ Upload successful!")
            
            # Check count
            count = uploader.get_sealed_product_listing_count(product_id)
            print(f"📊 New listing count: {count}")
        else:
            print(f"❌ Upload failed!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sealed_product_upload() 