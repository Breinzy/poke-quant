#!/usr/bin/env python3
"""
Test PriceCharting scraper with just 1 item
"""

from card_selector import CardSelector
from pricecharting_scraper import PriceChartingScraper

def test_single_card():
    print("🧪 Testing PriceCharting Scraper - Single Card")
    print("=" * 50)
    
    try:
        # Get one curated card
        selector = CardSelector()
        cards = selector.get_curated_investment_targets()
        
        if not cards:
            print("❌ No curated cards found")
            return False
            
        # Use the first card
        test_card = cards[0]
        card_name = test_card.get('card_name', 'Unknown')
        set_name = test_card.get('set_name', 'Unknown')
        
        print(f"\n🎯 Testing with: {card_name} - {set_name}")
        
        # Test PriceCharting scraper
        scraper = PriceChartingScraper()
        
        print(f"\n🔍 Step 1: Searching PriceCharting...")
        pc_url = scraper.search_card_on_pricecharting(card_name, set_name, card_data=test_card)
        
        if pc_url:
            print(f"✅ Found URL: {pc_url}")
            
            print(f"\n📈 Step 2: Scraping price data...")
            price_data = scraper.scrape_price_history(pc_url)
            
            if price_data:
                print(f"✅ Price data retrieved!")
                print(f"   Current prices: {price_data.get('current_prices', {})}")
                print(f"   Product info: {price_data.get('product_info', {})}")
                print(f"   URL: {price_data.get('url', '')}")
                return True
            else:
                print(f"❌ Failed to scrape price data")
                return False
        else:
            print(f"❌ Card not found on PriceCharting")
            return False
            
    except Exception as e:
        print(f"❌ Error testing PriceCharting: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_single_sealed_product():
    print("\n🧪 Testing PriceCharting Scraper - Single Sealed Product")
    print("=" * 50)
    
    try:
        # Get one sealed product
        selector = CardSelector()
        sealed_products = selector.get_sealed_products_list()
        
        if not sealed_products:
            print("❌ No sealed products found")
            return False
            
        # Use the first sealed product
        test_product = sealed_products[0]
        product_name = test_product.get('product_name', 'Unknown')
        
        print(f"\n📦 Testing with: {product_name}")
        
        # Test PriceCharting scraper
        scraper = PriceChartingScraper()
        
        print(f"\n🔍 Step 1: Searching PriceCharting...")
        pc_url = scraper.search_sealed_product_on_pricecharting(product_name)
        
        if pc_url:
            print(f"✅ Found URL: {pc_url}")
            
            print(f"\n📈 Step 2: Scraping price data...")
            price_data = scraper.scrape_price_history(pc_url)
            
            if price_data:
                print(f"✅ Price data retrieved!")
                print(f"   Current prices: {price_data.get('current_prices', {})}")
                print(f"   Product info: {price_data.get('product_info', {})}")
                return True
            else:
                print(f"❌ Failed to scrape price data")
                return False
        else:
            print(f"❌ Sealed product not found on PriceCharting")
            return False
            
    except Exception as e:
        print(f"❌ Error testing sealed product: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 PRICECHARTING SCRAPER TEST")
    print("=" * 60)
    
    # Test single card
    card_success = test_single_card()
    
    # Test single sealed product  
    sealed_success = test_single_sealed_product()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"Card test: {'✅ PASS' if card_success else '❌ FAIL'}")
    print(f"Sealed product test: {'✅ PASS' if sealed_success else '❌ FAIL'}")
    
    if card_success or sealed_success:
        print(f"\n🎉 PriceCharting scraper is working!")
        print(f"Ready to test with more items.")
    else:
        print(f"\n⚠️ PriceCharting scraper needs debugging.")
        print(f"Check network connection and site availability.") 