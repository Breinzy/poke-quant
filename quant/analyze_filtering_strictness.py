#!/usr/bin/env python3
"""
Analyze Filtering Strictness
Determine if we're being too aggressive and missing legitimate data
"""

import sys
import os
from datetime import datetime
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase
from quant.enhanced_outlier_filter import EnhancedOutlierFilter

def analyze_what_were_filtering():
    """Analyze exactly what we're filtering out to see if we're too strict"""
    
    print("🔍 Detailed Analysis: Are We Too Strict?")
    print("=" * 80)
    
    # Get the product
    sealed_query = supabase.table('sealed_products').select('*').ilike('product_name', '%Brilliant Stars Booster Box%').limit(1).execute()
    product = sealed_query.data[0]
    product_id = str(product['id'])
    
    # Get all listings
    ebay_query = supabase.table('ebay_sealed_listings').select('*').eq('sealed_product_id', product_id).execute()
    listings = ebay_query.data
    
    print(f"📦 Product: {product['product_name']}")
    print(f"📊 Total listings: {len(listings)}")
    
    # Categorize ALL listings manually to understand the data
    categories = {
        'actual_booster_boxes': [],
        'elite_trainer_boxes': [],
        'single_packs': [],
        'small_bundles': [],  # 2-12 packs
        'blister_packs': [],
        'other_products': [],
        'damaged_empty': [],
        'wrong_set': []
    }
    
    for listing in listings:
        title = listing.get('title', '').lower()
        price = float(listing.get('price', 0))
        
        # Categorize based on title analysis
        if any(phrase in title for phrase in ['empty', 'box only', 'damaged', 'opened']):
            categories['damaged_empty'].append(listing)
        elif any(phrase in title for phrase in ['etb', 'elite trainer']):
            categories['elite_trainer_boxes'].append(listing)
        elif 'blister' in title:
            categories['blister_packs'].append(listing)
        elif re.search(r'\b(?:1|2|3|4|5|6|7|8|9|10|11|12)\s*pack[s]?\b', title) and 'booster box' not in title:
            categories['small_bundles'].append(listing)
        elif any(phrase in title for phrase in ['booster pack', 'single pack']) and 'booster box' not in title:
            categories['single_packs'].append(listing)
        elif 'booster box' in title or ('36' in title and ('pack' in title or 'box' in title)):
            categories['actual_booster_boxes'].append(listing)
        elif any(set_name in title for set_name in ['silver tempest', 'lost origin', 'astral radiance', 'chilling reign']) and 'brilliant stars' not in title:
            categories['wrong_set'].append(listing)
        else:
            categories['other_products'].append(listing)
    
    # Print analysis
    print(f"\n📋 MANUAL CATEGORIZATION RESULTS:")
    print(f"=" * 60)
    
    for category, items in categories.items():
        if items:
            print(f"\n🏷️  {category.replace('_', ' ').title()}: {len(items)} listings")
            # Show price range
            prices = [float(item.get('price', 0)) for item in items]
            if prices:
                print(f"   💰 Price range: ${min(prices):.2f} - ${max(prices):.2f}")
            
            # Show examples
            print(f"   📝 Examples:")
            for i, item in enumerate(items[:3], 1):
                title = item.get('title', '')[:70]
                price = item.get('price', 0)
                print(f"      {i}. ${price:7.2f} - {title}")
    
    return categories

def evaluate_current_filtering_logic(categories):
    """Evaluate if our current filtering logic makes sense"""
    
    print(f"\n🧪 EVALUATING CURRENT FILTERING LOGIC")
    print("=" * 80)
    
    # What SHOULD be kept (legitimate booster box data)
    should_keep = categories['actual_booster_boxes']
    
    # What SHOULD be filtered (obviously wrong products)
    should_filter = (
        categories['single_packs'] + 
        categories['blister_packs'] + 
        categories['damaged_empty'] +
        categories['wrong_set']
    )
    
    # Questionable cases that need discussion
    questionable_etbs = categories['elite_trainer_boxes']
    questionable_bundles = categories['small_bundles']
    questionable_other = categories['other_products']
    
    print(f"✅ SHOULD DEFINITELY KEEP (Actual Booster Boxes): {len(should_keep)}")
    print(f"❌ SHOULD DEFINITELY FILTER: {len(should_filter)}")
    print(f"🤔 QUESTIONABLE - ETBs: {len(questionable_etbs)}")
    print(f"🤔 QUESTIONABLE - Small Bundles: {len(questionable_bundles)}")
    print(f"🤔 QUESTIONABLE - Other: {len(questionable_other)}")
    
    # Calculate what percentage we SHOULD filter vs what we ARE filtering
    total_listings = sum(len(cat) for cat in categories.values())
    should_filter_rate = len(should_filter) / total_listings * 100
    current_filter_rate = 70.7  # From our last test
    
    print(f"\n📊 FILTERING RATE ANALYSIS:")
    print(f"   Optimal filter rate (obvious junk): {should_filter_rate:.1f}%")
    print(f"   Current filter rate: {current_filter_rate:.1f}%")
    print(f"   Over-filtering by: {current_filter_rate - should_filter_rate:.1f}%")
    
    return should_keep, should_filter, questionable_etbs, questionable_bundles

def analyze_etb_inclusion_impact(etbs):
    """Analyze whether including ETBs would help with data volume"""
    
    print(f"\n💡 SHOULD WE INCLUDE ELITE TRAINER BOXES?")
    print("=" * 60)
    
    if not etbs:
        print("   No ETBs found in data")
        return
    
    etb_prices = [float(item.get('price', 0)) for item in etbs]
    print(f"   📊 ETB Count: {len(etbs)}")
    print(f"   💰 ETB Price Range: ${min(etb_prices):.2f} - ${max(etb_prices):.2f}")
    print(f"   📈 ETB Average: ${sum(etb_prices)/len(etb_prices):.2f}")
    
    # ETBs are a different product type but could provide comparative data
    print(f"\n   🤔 Considerations for including ETBs:")
    print(f"      ✅ Pro: Would add {len(etbs)} more data points")
    print(f"      ✅ Pro: ETBs are legitimate sealed products")
    print(f"      ❌ Con: Different product type (8-11 packs vs 36 packs)")
    print(f"      ❌ Con: Different price point (might skew analysis)")
    
    # Show some examples
    print(f"\n   📝 ETB Examples:")
    for i, etb in enumerate(etbs[:5], 1):
        title = etb.get('title', '')[:70]
        price = etb.get('price', 0)
        print(f"      {i}. ${price:7.2f} - {title}")

def propose_filtering_adjustments(should_keep, should_filter, questionable_etbs, questionable_bundles):
    """Propose adjustments to get more data while maintaining quality"""
    
    print(f"\n🔧 PROPOSED FILTERING ADJUSTMENTS")
    print("=" * 80)
    
    total_available = len(should_keep) + len(should_filter) + len(questionable_etbs) + len(questionable_bundles)
    
    print(f"📊 Data Availability Options:")
    print(f"   Option 1 (Strict): Only booster boxes = {len(should_keep)} data points")
    print(f"   Option 2 (Moderate): Booster boxes + ETBs = {len(should_keep) + len(questionable_etbs)} data points")
    print(f"   Option 3 (Inclusive): Add small bundles = {len(should_keep) + len(questionable_etbs) + len(questionable_bundles)} data points")
    
    # Recommendation
    if len(should_keep) < 50:
        print(f"\n💡 RECOMMENDATION: Option 2 (Moderate)")
        print(f"   ✅ Include ETBs for more data volume")
        print(f"   ✅ ETBs are legitimate products, just different type")
        print(f"   ✅ Can analyze separately or with appropriate weighting")
        print(f"   ❌ Exclude small bundles (too different from booster boxes)")
    else:
        print(f"\n💡 RECOMMENDATION: Option 1 (Strict)")
        print(f"   ✅ Sufficient booster box data available")
        print(f"   ✅ Keep analysis focused on single product type")

def check_scraping_scope_issue():
    """Check if the real issue is that scraping is too broad"""
    
    print(f"\n🎯 ROOT CAUSE ANALYSIS: Is Scraping Too Broad?")
    print("=" * 80)
    
    print(f"🔍 The fundamental issue might be:")
    print(f"   • Searching for 'Brilliant Stars Booster Box'")
    print(f"   • But eBay returns everything with 'Brilliant Stars'")
    print(f"   • Including ETBs, single packs, blister packs, etc.")
    print(f"   • Leading to massive filtering requirements")
    
    print(f"\n💡 POTENTIAL SOLUTIONS:")
    print(f"   1. Improve search terms (more specific)")
    print(f"   2. Accept that filtering is necessary (eBay search is broad)")
    print(f"   3. Include related products (ETBs) for more data")
    print(f"   4. Scrape multiple product types separately")

def main():
    """Main analysis function"""
    
    print("🔍 PokeQuant Filtering Strictness Analysis")
    print("=" * 80)
    
    # Manual categorization
    categories = analyze_what_were_filtering()
    
    # Evaluate current logic
    should_keep, should_filter, questionable_etbs, questionable_bundles = evaluate_current_filtering_logic(categories)
    
    # ETB inclusion analysis
    analyze_etb_inclusion_impact(questionable_etbs)
    
    # Propose adjustments
    propose_filtering_adjustments(should_keep, should_filter, questionable_etbs, questionable_bundles)
    
    # Root cause analysis
    check_scraping_scope_issue()
    
    print(f"\n🎯 CONCLUSIONS:")
    print(f"   • Current 70% filtering might be appropriate given data mix")
    print(f"   • Real issue: eBay search returns too many irrelevant products")
    print(f"   • Solution: Either improve scraping OR accept broader product inclusion")
    print(f"   • For now: Consider including ETBs to boost data volume")

if __name__ == "__main__":
    main() 