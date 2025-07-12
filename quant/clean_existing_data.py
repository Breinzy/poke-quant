#!/usr/bin/env python3
"""
Clean Existing Data in PokeQuant Database
Remove dirty data that was stored before filtering was implemented
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase
from quant.price_data_service import PriceDataService

def clean_pokequant_price_series():
    """Clean existing data in pokequant_price_series table"""
    
    print("🧹 Cleaning Existing PokeQuant Price Series Data")
    print("=" * 60)
    
    try:
        # Get all products that have price series data
        products_query = supabase.table('pokequant_products').select('*').execute()
        
        if not products_query.data:
            print("   ℹ️ No products found in pokequant_products table")
            return
        
        print(f"   📊 Found {len(products_query.data)} products with potential data")
        
        total_cleaned = 0
        
        for product in products_query.data:
            product_id = product['id']
            product_name = product['product_name']
            
            print(f"\n🔍 Checking product: {product_name}")
            
            # Get existing price series data
            price_series_query = supabase.table('pokequant_price_series').select('*').eq('pokequant_product_id', product_id).execute()
            
            if not price_series_query.data:
                print(f"   ℹ️ No price series data found")
                continue
            
            print(f"   📊 Found {len(price_series_query.data)} price series entries")
            
            # For now, we'll just delete all existing data so it can be re-aggregated with filtering
            # In a production system, you might want more sophisticated cleaning
            delete_result = supabase.table('pokequant_price_series').delete().eq('pokequant_product_id', product_id).execute()
            
            deleted_count = len(price_series_query.data)  # Approximate
            total_cleaned += deleted_count
            
            print(f"   🗑️ Deleted {deleted_count} price series entries")
            
            # Reset the product's last_data_update to force re-aggregation
            supabase.table('pokequant_products').update({
                'last_data_update': None,
                'data_quality_score': 0.0
            }).eq('id', product_id).execute()
            
            print(f"   🔄 Reset product timestamps to force re-aggregation")
        
        print(f"\n✅ Cleaning Complete!")
        print(f"   🗑️ Total entries cleaned: {total_cleaned}")
        print(f"   🔄 Products reset: {len(products_query.data)}")
        
    except Exception as e:
        print(f"❌ Error during cleaning: {e}")

def re_aggregate_with_filtering():
    """Re-aggregate data with new filtering in place"""
    
    print(f"\n🔄 Re-aggregating Data with Filtering")
    print("=" * 60)
    
    price_service = PriceDataService()
    
    # Test with Brilliant Stars Booster Box
    try:
        sealed_query = supabase.table('sealed_products').select('*').ilike('product_name', '%Brilliant Stars Booster Box%').limit(1).execute()
        
        if sealed_query.data:
            product = sealed_query.data[0]
            product_id = str(product['id'])
            
            print(f"   🎯 Re-aggregating: {product['product_name']}")
            
            result = price_service.aggregate_ebay_data(
                product_type='sealed',
                product_id=product_id,
                product_name=product['product_name'],
                set_name=product.get('set_name')
            )
            
            if result['success']:
                print(f"   ✅ Re-aggregation successful!")
                print(f"   📈 Raw listings: {result['raw_listings']}")
                print(f"   🧹 Filtered listings: {result['filtered_listings']}")
                print(f"   🚫 Removed listings: {result['removed_listings']}")
                print(f"   📊 Stored clean points: {result['stored_points']}")
                
                if result['raw_listings'] > 0:
                    filter_rate = result['removed_listings'] / result['raw_listings'] * 100
                    print(f"   📈 Filtering effectiveness: {filter_rate:.1f}% outliers removed")
            else:
                print(f"   ❌ Re-aggregation failed: {result.get('error')}")
        else:
            print(f"   ⚠️ Test product not found")
            
    except Exception as e:
        print(f"❌ Error during re-aggregation: {e}")

def verify_data_quality():
    """Verify that cleaned data meets quality standards"""
    
    print(f"\n🔍 Verifying Data Quality")
    print("=" * 60)
    
    try:
        # Check for suspicious prices in cleaned data
        price_query = supabase.table('pokequant_price_series').select('*').lt('price', 50).execute()
        
        if price_query.data:
            print(f"   ⚠️ Found {len(price_query.data)} entries with prices under $50:")
            for entry in price_query.data[:5]:  # Show first 5
                print(f"      ${entry['price']:.2f} on {entry['price_date']} from {entry['source']}")
        else:
            print(f"   ✅ No suspicious low prices found (< $50)")
        
        # Check for extremely high prices
        high_price_query = supabase.table('pokequant_price_series').select('*').gt('price', 1000).execute()
        
        if high_price_query.data:
            print(f"   ⚠️ Found {len(high_price_query.data)} entries with prices over $1000:")
            for entry in high_price_query.data[:5]:  # Show first 5
                print(f"      ${entry['price']:.2f} on {entry['price_date']} from {entry['source']}")
        else:
            print(f"   ✅ No extremely high prices found (> $1000)")
        
        # Overall data quality summary
        total_query = supabase.table('pokequant_price_series').select('price').execute()
        total_count = len(total_query.data) if total_query.data else 0
        
        print(f"\n📊 Data Quality Summary:")
        print(f"   📈 Total price points: {total_count}")
        
        if total_count > 0:
            prices = [float(entry['price']) for entry in total_query.data]
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            print(f"   💰 Price range: ${min_price:.2f} - ${max_price:.2f}")
            print(f"   📊 Average price: ${avg_price:.2f}")
            
            # Check if we still have unrealistic prices
            unrealistic_count = sum(1 for p in prices if p < 25 or p > 2000)
            unrealistic_rate = unrealistic_count / len(prices) * 100
            
            print(f"   🎯 Potentially unrealistic prices: {unrealistic_count} ({unrealistic_rate:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

def main():
    """Main cleaning function"""
    
    print("🧹 PokeQuant Data Cleaning Utility")
    print("=" * 60)
    print("This script will clean existing dirty data and re-aggregate with filtering")
    print("⚠️  WARNING: This will delete existing pokequant_price_series data")
    
    # Ask for confirmation
    response = input("\nProceed with cleaning? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("❌ Cleaning cancelled")
        return
    
    # Run cleaning process
    clean_pokequant_price_series()
    re_aggregate_with_filtering()
    verify_data_quality()
    
    print(f"\n🎉 Data Cleaning Complete!")
    print(f"\n💡 Next Steps:")
    print(f"   1. Run normal PokeQuant analysis to see improved data quality")
    print(f"   2. Future data will be filtered before storage automatically")
    print(f"   3. No more $40 'booster boxes' or similar outliers")

if __name__ == "__main__":
    main() 