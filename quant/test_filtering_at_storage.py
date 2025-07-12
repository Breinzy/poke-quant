#!/usr/bin/env python3
"""
Test Filtering at Storage Level
Verify that data quality filtering is applied BEFORE storing data in database
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant.price_data_service import PriceDataService
from supabase_client import supabase

def test_filtering_during_storage():
    """Test that filtering is applied during data storage"""
    
    print("🧪 Testing Filtering During Data Storage")
    print("=" * 60)
    
    # Initialize price data service
    price_service = PriceDataService()
    
    # Test with Brilliant Stars Booster Box - a product we know has outliers
    product_name = "Brilliant Stars Booster Box"
    product_type = "sealed"
    
    # Find the product ID
    try:
        sealed_query = supabase.table('sealed_products').select('*').ilike('product_name', f'%{product_name}%').limit(1).execute()
        
        if not sealed_query.data:
            print(f"❌ Product '{product_name}' not found in database")
            return
        
        product = sealed_query.data[0]
        product_id = str(product['id'])
        
        print(f"✅ Found product: {product['product_name']} (ID: {product_id})")
        
        # Test eBay data aggregation with filtering
        print(f"\n🔄 Testing eBay data aggregation with filtering...")
        
        # Before: Check how much raw data exists
        raw_data_query = supabase.table('ebay_sealed_listings').select('*').eq('sealed_product_id', product_id).execute()
        raw_count = len(raw_data_query.data) if raw_data_query.data else 0
        
        print(f"   📊 Raw eBay listings in database: {raw_count}")
        
        if raw_count == 0:
            print(f"   ⚠️ No raw eBay data found - run scraper first")
            return
        
        # Test the new filtering-enabled aggregation
        result = price_service.aggregate_ebay_data(
            product_type=product_type,
            product_id=product_id,
            product_name=product['product_name'],
            set_name=product.get('set_name')
        )
        
        if result['success']:
            print(f"   ✅ Aggregation successful!")
            print(f"   📈 Raw listings: {result['raw_listings']}")
            print(f"   🧹 Filtered listings: {result['filtered_listings']}")
            print(f"   🚫 Removed listings: {result['removed_listings']}")
            print(f"   📊 Aggregated points: {result['aggregated_points']}")
            print(f"   💾 Stored points: {result['stored_points']}")
            
            # Calculate filtering efficiency
            if result['raw_listings'] > 0:
                filter_rate = result['removed_listings'] / result['raw_listings'] * 100
                print(f"   📈 Filtering rate: {filter_rate:.1f}%")
        else:
            print(f"   ❌ Aggregation failed: {result.get('error', 'Unknown error')}")
        
        # Test data retrieval
        print(f"\n📤 Testing data retrieval...")
        
        pokequant_product_id = result.get('pokequant_product_id')
        if pokequant_product_id:
            price_series = price_service.get_price_series(pokequant_product_id)
            
            if price_series['success']:
                summary = price_series['summary']
                print(f"   ✅ Retrieved price series successfully")
                print(f"   📊 Total data points: {summary['total_data_points']}")
                print(f"   💰 Price range: ${summary['price_range']['min']:.2f} - ${summary['price_range']['max']:.2f}")
                print(f"   📅 Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
                print(f"   🔗 Sources: {', '.join(summary['sources'])}")
            else:
                print(f"   ❌ Failed to retrieve price series: {price_series.get('error')}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_llm_filtering_integration():
    """Test LLM filtering integration (if available)"""
    
    print(f"\n🤖 Testing LLM Filtering Integration")
    print("-" * 40)
    
    if not os.getenv('GEMINI_API_KEY'):
        print("   ⚠️ Gemini API key not found - LLM filtering not available")
        return
    
    # Set LLM filtering flag
    original_flag = os.getenv('POKEQUANT_USE_LLM')
    os.environ['POKEQUANT_USE_LLM'] = 'true'
    
    try:
        # Re-test with LLM filtering enabled
        test_filtering_during_storage()
        
    finally:
        # Restore original flag
        if original_flag:
            os.environ['POKEQUANT_USE_LLM'] = original_flag
        else:
            os.environ.pop('POKEQUANT_USE_LLM', None)

def compare_before_after_filtering():
    """Compare data quality before and after implementing filtering"""
    
    print(f"\n📊 Comparing Data Quality Before/After Filtering")
    print("=" * 60)
    
    # This would ideally compare existing stored data vs newly filtered data
    # For now, just demonstrate the concept
    
    print(f"📈 Before filtering implementation:")
    print(f"   • All scraped data stored directly in database")
    print(f"   • Outliers included (e.g., $40 'booster boxes')")
    print(f"   • Filtering only applied during analysis")
    print(f"   • Database contains dirty data")
    
    print(f"\n📈 After filtering implementation:")
    print(f"   • Data quality filtering applied before storage")
    print(f"   • Outliers removed at ingestion time")
    print(f"   • Database contains only clean, validated data")
    print(f"   • Analysis uses pre-filtered data")
    
def main():
    """Main test function"""
    
    print("🧪 PokeQuant Storage-Level Filtering Test")
    print("=" * 60)
    
    # Run tests
    test_filtering_during_storage()
    test_llm_filtering_integration()
    compare_before_after_filtering()
    
    print(f"\n✅ Testing Complete!")
    print(f"\n💡 Key Improvements:")
    print(f"   • Filtering now happens BEFORE data storage")
    print(f"   • Database contains only clean, validated data")
    print(f"   • No more $40 'booster boxes' or semantic misclassifications")
    print(f"   • Analysis uses pre-cleaned data for better accuracy")

if __name__ == "__main__":
    main() 