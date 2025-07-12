#!/usr/bin/env python3
"""
Investigate High Removal Rate in PokeQuant Filtering
Analyze why 81% of listings are being filtered out
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase
from quant.enhanced_outlier_filter import EnhancedOutlierFilter

def analyze_brilliant_stars_data():
    """Analyze the Brilliant Stars Booster Box data to understand removal rate"""
    
    print("🔍 Investigating High Removal Rate in Brilliant Stars Booster Box Data")
    print("=" * 80)
    
    # Get the product
    sealed_query = supabase.table('sealed_products').select('*').ilike('product_name', '%Brilliant Stars Booster Box%').limit(1).execute()
    
    if not sealed_query.data:
        print("❌ Product not found")
        return
    
    product = sealed_query.data[0]
    product_id = str(product['id'])
    product_name = product['product_name']
    
    print(f"📦 Product: {product_name} (ID: {product_id})")
    
    # Get all eBay listings for this product
    ebay_query = supabase.table('ebay_sealed_listings').select('*').eq('sealed_product_id', product_id).execute()
    
    if not ebay_query.data:
        print("❌ No eBay data found")
        return
    
    listings = ebay_query.data
    print(f"📊 Total listings found: {len(listings)}")
    
    # Sample some listings to see what we're working with
    print(f"\n📋 Sample Listings (first 10):")
    for i, listing in enumerate(listings[:10], 1):
        title = listing.get('title', 'No title')[:80]
        price = listing.get('price', 0)
        condition = listing.get('condition_category', 'Unknown')
        print(f"  {i:2d}. ${price:8.2f} - {condition:10s} - {title}")
    
    # Price distribution analysis
    prices = [float(listing.get('price', 0)) for listing in listings if listing.get('price')]
    prices.sort()
    
    print(f"\n💰 Price Distribution:")
    print(f"   Min: ${min(prices):.2f}")
    print(f"   Max: ${max(prices):.2f}")
    print(f"   Median: ${prices[len(prices)//2]:.2f}")
    print(f"   Average: ${sum(prices)/len(prices):.2f}")
    
    # Show price ranges
    under_50 = len([p for p in prices if p < 50])
    under_75 = len([p for p in prices if p < 75])
    over_200 = len([p for p in prices if p > 200])
    over_500 = len([p for p in prices if p > 500])
    
    print(f"\n📈 Price Range Breakdown:")
    print(f"   Under $50: {under_50} ({under_50/len(prices)*100:.1f}%)")
    print(f"   Under $75: {under_75} ({under_75/len(prices)*100:.1f}%)")
    print(f"   Over $200: {over_200} ({over_200/len(prices)*100:.1f}%)")
    print(f"   Over $500: {over_500} ({over_500/len(prices)*100:.1f}%)")
    
    return listings, prices

def test_filtering_step_by_step(listings):
    """Test filtering step by step to understand what's being removed"""
    
    print(f"\n🧪 Step-by-Step Filtering Analysis")
    print("=" * 80)
    
    # Initialize filter
    filter_system = EnhancedOutlierFilter()
    
    product_info = {
        'name': 'Brilliant Stars Booster Box',
        'type': 'sealed',
        'set_name': 'Brilliant Stars'
    }
    
    # Convert to filtering format
    price_data = []
    for listing in listings:
        price_point = {
            'price': float(listing.get('price', 0)),
            'source': 'ebay',
            'title': listing.get('title', ''),
            'condition_category': listing.get('condition_category', 'unknown'),
            'original_data': listing
        }
        price_data.append(price_point)
    
    print(f"📊 Starting with {len(price_data)} listings")
    
    # Step 1: Price threshold filtering - use same logic as storage pipeline
    product_type = filter_system._determine_product_type(product_info)
    thresholds = filter_system.price_thresholds.get(product_type, filter_system.price_thresholds['card'])
    
    print(f"\n🎯 Step 1: Price Threshold Filtering")
    print(f"   Valid range for {product_type}: ${thresholds['min']} - ${thresholds['max']}")
    
    price_filtered = []
    price_removed = []
    
    for point in price_data:
        price = point['price']
        if price < thresholds['min'] or price > thresholds['max']:
            price_removed.append(point)
        else:
            price_filtered.append(point)
    
    print(f"   ✅ Kept: {len(price_filtered)} listings")
    print(f"   ❌ Removed by price: {len(price_removed)} listings ({len(price_removed)/len(price_data)*100:.1f}%)")
    
    # Show what was removed by price
    if price_removed:
        print(f"\n   🚫 Examples of price-removed listings:")
        for i, point in enumerate(price_removed[:5], 1):
            print(f"      {i}. ${point['price']:.2f} - {point['title'][:60]}")
    
    # Step 2: Title pattern filtering
    print(f"\n📝 Step 2: Title Pattern Filtering")
    
    title_filtered = []
    title_removed = []
    
    for point in price_filtered:
        title = point.get('title', '')
        if filter_system._is_suspicious_title(title, product_type):
            title_removed.append(point)
        else:
            title_filtered.append(point)
    
    print(f"   ✅ Kept after title filtering: {len(title_filtered)} listings")
    print(f"   ❌ Removed by title patterns: {len(title_removed)} listings ({len(title_removed)/len(price_filtered)*100:.1f}%)")
    
    # Show what was removed by title
    if title_removed:
        print(f"\n   🚫 Examples of title-removed listings:")
        for i, point in enumerate(title_removed[:10], 1):
            print(f"      {i}. ${point['price']:.2f} - {point['title']}")
    
    # Step 3: Statistical outlier removal
    print(f"\n📊 Step 3: Statistical Outlier Filtering")
    
    if len(title_filtered) >= 5:
        final_filtered, stat_removed = filter_system._remove_statistical_outliers(title_filtered)
        print(f"   ✅ Final kept: {len(final_filtered)} listings")
        print(f"   ❌ Removed by statistics: {len(stat_removed)} listings")
    else:
        final_filtered = title_filtered
        stat_removed = []
        print(f"   ℹ️ Not enough data for statistical filtering")
    
    # Summary
    total_removed = len(price_removed) + len(title_removed) + len(stat_removed)
    print(f"\n📋 FILTERING SUMMARY:")
    print(f"   Original: {len(price_data)} listings")
    print(f"   Price filtering: -{len(price_removed)} ({len(price_removed)/len(price_data)*100:.1f}%)")
    print(f"   Title filtering: -{len(title_removed)} ({len(title_removed)/len(price_data)*100:.1f}%)")
    print(f"   Statistical filtering: -{len(stat_removed)} ({len(stat_removed)/len(price_data)*100:.1f}%)")
    print(f"   Total removed: {total_removed} ({total_removed/len(price_data)*100:.1f}%)")
    print(f"   Final kept: {len(final_filtered)} ({len(final_filtered)/len(price_data)*100:.1f}%)")
    
    return {
        'original': price_data,
        'price_removed': price_removed,
        'title_removed': title_removed,
        'stat_removed': stat_removed,
        'final_kept': final_filtered
    }

def analyze_removal_patterns(filter_results):
    """Analyze patterns in what's being removed"""
    
    print(f"\n🔬 Analyzing Removal Patterns")
    print("=" * 80)
    
    # Analyze price removals
    price_removed = filter_results['price_removed']
    if price_removed:
        print(f"\n💰 Price Removal Analysis:")
        prices = [p['price'] for p in price_removed]
        print(f"   Removed {len(prices)} listings with prices: ${min(prices):.2f} - ${max(prices):.2f}")
        
        too_low = [p for p in prices if p < 50]
        too_high = [p for p in prices if p > 1000]
        print(f"   Too low (< $50): {len(too_low)} listings")
        print(f"   Too high (> $1000): {len(too_high)} listings")
    
    # Analyze title removals
    title_removed = filter_results['title_removed']
    if title_removed:
        print(f"\n📝 Title Removal Analysis:")
        print(f"   Removed {len(title_removed)} listings due to suspicious titles")
        
        # Common patterns in removed titles
        patterns = {}
        for item in title_removed:
            title = item['title'].lower()
            if 'pack' in title and 'box' not in title:
                patterns['single_pack'] = patterns.get('single_pack', 0) + 1
            if 'blister' in title:
                patterns['blister'] = patterns.get('blister', 0) + 1
            if any(word in title for word in ['empty', 'damaged', 'opened']):
                patterns['damaged'] = patterns.get('damaged', 0) + 1
            if any(word in title for word in ['4 pack', '8 pack', '12 pack']):
                patterns['multi_pack'] = patterns.get('multi_pack', 0) + 1
        
        print(f"   Common patterns in removed titles:")
        for pattern, count in patterns.items():
            print(f"     {pattern}: {count} listings")

def investigate_specific_cases(filter_results):
    """Look at specific cases that might be incorrectly filtered"""
    
    print(f"\n🕵️ Investigating Specific Cases")
    print("=" * 80)
    
    title_removed = filter_results['title_removed']
    
    # Look for potentially legitimate booster boxes that were filtered
    potentially_legitimate = []
    
    for item in title_removed:
        title = item['title'].lower()
        price = item['price']
        
        # Check if it has "booster box" in title and reasonable price
        if 'booster box' in title and 50 <= price <= 500:
            potentially_legitimate.append(item)
    
    if potentially_legitimate:
        print(f"🤔 Potentially Legitimate Listings That Were Filtered:")
        for i, item in enumerate(potentially_legitimate[:10], 1):
            print(f"   {i}. ${item['price']:.2f} - {item['title']}")
    else:
        print(f"✅ No obviously legitimate listings appear to have been incorrectly filtered")

def main():
    """Main investigation function"""
    
    print("🔍 PokeQuant High Removal Rate Investigation")
    print("=" * 80)
    
    # Analyze the data
    listings, prices = analyze_brilliant_stars_data()
    
    # Test filtering step by step
    filter_results = test_filtering_step_by_step(listings)
    
    # Analyze removal patterns
    analyze_removal_patterns(filter_results)
    
    # Investigate specific cases
    investigate_specific_cases(filter_results)
    
    print(f"\n🎯 Conclusions:")
    print(f"   • High removal rate likely due to mix of legitimate and non-legitimate listings")
    print(f"   • Many single packs, blisters, and bundles mixed in with booster box search")
    print(f"   • Some legitimate booster boxes may be caught by overly strict title filtering")
    print(f"   • Consider adjusting thresholds or improving pattern matching")

if __name__ == "__main__":
    main() 