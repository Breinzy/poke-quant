#!/usr/bin/env python3
"""
Test Enhanced Filtering with Verbose Output
"""

import sys
import os
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant.enhanced_outlier_filter import EnhancedOutlierFilter
from quant.price_data_service import PriceDataService
from supabase_client import supabase

def test_enhanced_filtering():
    """Test enhanced filtering with verbose output"""
    
    print("🧪 Testing Enhanced Outlier Filtering")
    print("=" * 60)
    
    # Get the price data service
    price_service = PriceDataService()
    
    # Find Brilliant Stars Booster Box
    try:
        sealed_query = supabase.table('sealed_products').select('*').ilike('product_name', '%Brilliant Stars Booster Box%').limit(1).execute()
        if sealed_query.data:
            product_data = sealed_query.data[0]
            product_info = {
                'type': 'sealed',
                'id': str(product_data['id']),
                'name': product_data['product_name'],
                'set_name': product_data.get('set_name', ''),
                'display_name': product_data['product_name'],
                'raw_data': product_data
            }
            print(f"✅ Found product: {product_info['name']}")
        else:
            print("❌ Product not found")
            return
    except Exception as e:
        print(f"❌ Error finding product: {e}")
        return
    
    # Get the pokequant product ID
    pokequant_product_id = price_service.ensure_product_exists(
        product_info['type'], 
        product_info['id'], 
        product_info['name'], 
        product_info.get('set_name')
    )
    
    # Load price data
    price_data = price_service.get_price_series(pokequant_product_id)
    
    if not price_data['success']:
        print(f"❌ No price data found: {price_data['error']}")
        return
    
    raw_data = price_data['raw_data']
    
    # Add title information for eBay data
    print(f"\n📊 Preparing data for filtering...")
    print(f"Raw data points: {len(raw_data)}")
    
    # Show some sample data
    print(f"\n🔍 Sample data points:")
    for i, point in enumerate(raw_data[:5]):
        print(f"  {i+1}. ${point['price']} from {point['source']} ({point['condition_category']})")
        if 'sample_titles' in point:
            titles = point.get('sample_titles', [])
            if titles:
                print(f"     Title: {titles[0][:80]}...")
    
    # Apply enhanced filtering with verbose output
    print(f"\n🔍 Applying Enhanced Filtering...")
    
    filter_system = EnhancedOutlierFilter()
    
    # Test product type detection
    detected_type = filter_system._determine_product_type(product_info)
    print(f"Detected product type: {detected_type}")
    
    # Apply filtering
    filter_result = filter_system.filter_price_data(raw_data, product_info)
    
    # Print detailed report
    filter_system.print_filter_report(filter_result, product_info)
    
    # Show price comparison
    original_prices = [p['price'] for p in raw_data]
    filtered_prices = [p['price'] for p in filter_result['filtered_data']]
    
    print(f"\n📊 PRICE COMPARISON:")
    print(f"Original: ${min(original_prices):.2f} - ${max(original_prices):.2f}")
    print(f"Filtered: ${min(filtered_prices):.2f} - ${max(filtered_prices):.2f}")
    print(f"Removed {len(original_prices) - len(filtered_prices)} outliers")
    
    # Show what was removed
    if filter_result['removed_suspicious']:
        print(f"\n🚨 REMOVED SUSPICIOUS PRICES:")
        for i, item in enumerate(filter_result['removed_suspicious'][:10], 1):
            price = item['point']['price']
            reason = item['reason']
            print(f"  {i}. ${price} - {reason}")
    
    if filter_result['removed_statistical']:
        print(f"\n📊 REMOVED STATISTICAL OUTLIERS:")
        for i, item in enumerate(filter_result['removed_statistical'][:10], 1):
            price = item['point']['price']
            reason = item['reason']
            print(f"  {i}. ${price} - {reason}")

if __name__ == "__main__":
    test_enhanced_filtering() 