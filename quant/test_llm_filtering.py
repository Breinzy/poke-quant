#!/usr/bin/env python3
"""
Test LLM-Enhanced Filtering vs Regular Filtering
Demonstrates the power of LLM filtering for better data quality
"""

import sys
import os
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant.enhanced_outlier_filter import EnhancedOutlierFilter
from quant.llm_enhanced_filter import LLMEnhancedFilter

def create_test_data() -> List[Dict]:
    """Create realistic test data with various edge cases"""
    
    return [
        # Legitimate booster box listings
        {
            'title': 'Pokemon Brilliant Stars Booster Box 36 Packs Factory Sealed',
            'description': 'Brand new, factory sealed Pokemon Brilliant Stars booster box with 36 packs',
            'price': 149.99,
            'sample_titles': ['Pokemon Brilliant Stars Booster Box 36 Packs Factory Sealed']
        },
        {
            'title': 'Pokemon TCG Brilliant Stars Booster Box English',
            'description': 'Factory sealed English booster box',
            'price': 139.99,
            'sample_titles': ['Pokemon TCG Brilliant Stars Booster Box English']
        },
        
        # Problematic listings that should be filtered out
        {
            'title': 'Pokemon Brilliant Stars Booster Box - 4 Packs Only',
            'description': 'Four loose booster packs from brilliant stars set',
            'price': 29.99,
            'sample_titles': ['Pokemon Brilliant Stars Booster Box - 4 Packs Only']
        },
        {
            'title': 'Pokemon Brilliant Stars "Booster Box" Bundle 8 Packs',
            'description': 'Eight packs bundled together, not a full box',
            'price': 39.99,
            'sample_titles': ['Pokemon Brilliant Stars "Booster Box" Bundle 8 Packs']
        },
        {
            'title': 'ポケモンカード ブリリアントスター 1BOX 日本語版',
            'description': 'Japanese Pokemon Brilliant Stars booster box',
            'price': 89.99,
            'sample_titles': ['ポケモンカード ブリリアントスター 1BOX 日本語版']
        },
        {
            'title': 'Pokemon Brilliant Stars Empty Booster Box Display Case',
            'description': 'Empty box for display purposes only',
            'price': 15.99,
            'sample_titles': ['Pokemon Brilliant Stars Empty Booster Box Display Case']
        },
        {
            'title': 'Pokemon Brilliant Stars Booster Box DAMAGED/OPENED',
            'description': 'Box has been opened, some packs may be missing',
            'price': 69.99,
            'sample_titles': ['Pokemon Brilliant Stars Booster Box DAMAGED/OPENED']
        },
        {
            'title': 'Pokemon Brilliant Stars Booster Box Proxy/Reproduction',
            'description': 'Custom made reproduction box',
            'price': 45.99,
            'sample_titles': ['Pokemon Brilliant Stars Booster Box Proxy/Reproduction']
        },
        
        # Edge cases
        {
            'title': 'Pokemon Brilliant Stars Booster Box',
            'description': 'No description provided',
            'price': 89.99,
            'sample_titles': ['Pokemon Brilliant Stars Booster Box']
        },
        {
            'title': 'Pokemon Brilliant Stars Booster Box Collection - 2 Boxes',
            'description': 'Two complete booster boxes',
            'price': 299.99,
            'sample_titles': ['Pokemon Brilliant Stars Booster Box Collection - 2 Boxes']
        },
        
        # Legitimate but edge pricing
        {
            'title': 'Pokemon Brilliant Stars Booster Box - SALE!',
            'description': 'Clearance sale on factory sealed boxes',
            'price': 99.99,
            'sample_titles': ['Pokemon Brilliant Stars Booster Box - SALE!']
        },
        {
            'title': 'Pokemon Brilliant Stars Booster Box Premium Edition',
            'description': 'Special edition with bonus items',
            'price': 299.99,
            'sample_titles': ['Pokemon Brilliant Stars Booster Box Premium Edition']
        }
    ]

def test_enhanced_filtering():
    """Test the enhanced filtering (rule-based)"""
    
    print("🔧 Testing Enhanced Filtering (Rule-Based)")
    print("=" * 60)
    
    test_data = create_test_data()
    
    # Product info for filtering
    product_info = {
        'name': 'Brilliant Stars Booster Box',
        'type': 'sealed'
    }
    
    enhanced_filter = EnhancedOutlierFilter()
    
    # Apply enhanced filtering
    filtered_results = enhanced_filter.filter_price_data(
        test_data, 
        product_info, 
        verbose=True
    )
    
    print(f"\n📊 Enhanced Filtering Results:")
    print(f"   Original: {len(test_data)} listings")
    print(f"   Kept: {len(filtered_results['filtered_data'])} listings")
    print(f"   Removed: {len(filtered_results['removed_suspicious']) + len(filtered_results['removed_statistical'])} listings")
    
    print(f"\n❌ Removed Listings:")
    for item in filtered_results['removed_suspicious'] + filtered_results['removed_statistical']:
        print(f"   • ${item['point']['price']:.2f} - {item['reason']}")
    
    return filtered_results

def test_llm_filtering():
    """Test the LLM-enhanced filtering"""
    
    print("\n🤖 Testing LLM-Enhanced Filtering")
    print("=" * 60)
    
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable to test LLM filtering.")
        return None
    
    test_data = create_test_data()
    
    # Product info for filtering
    product_info = {
        'name': 'Brilliant Stars Booster Box',
        'type': 'sealed'
    }
    
    llm_filter = LLMEnhancedFilter()
    
    # Convert test data to LLM format
    listings = []
    for point in test_data:
        title = point['sample_titles'][0] if point['sample_titles'] else point['title']
        listings.append({
            'title': title,
            'description': point.get('description', ''),
            'price': point['price'],
            'original_data': point
        })
    
    # Apply LLM filtering
    print("🧠 Analyzing listings with LLM...")
    llm_results = llm_filter.batch_filter_listings(listings, 'booster_box', max_concurrent=2)
    
    print(f"\n📊 LLM Filtering Results:")
    summary = llm_results['analysis_summary']
    print(f"   Original: {summary['total_analyzed']} listings")
    print(f"   Kept: {summary['kept_count']} listings")
    print(f"   Removed: {summary['removed_count']} listings") 
    print(f"   Flagged: {summary['flagged_count']} listings")
    print(f"   Average Confidence: {summary['avg_confidence']:.2f}")
    
    if summary.get('languages_detected'):
        print(f"   Languages Detected: {summary['languages_detected']}")
    
    if summary.get('product_types_detected'):
        print(f"   Product Types Detected: {summary['product_types_detected']}")
    
    print(f"\n✅ Kept Listings:")
    for item in llm_results['kept'][:3]:  # Show first 3
        decision = item['filter_decision']
        print(f"   • ${item['price']:.2f} - {item['title'][:50]}... ({decision.confidence:.2f} confidence)")
    
    print(f"\n❌ Removed Listings:")
    for item in llm_results['removed']:
        decision = item['filter_decision']
        print(f"   • ${item['price']:.2f} - {decision.reason}")
    
    print(f"\n⚠️ Flagged Listings:")
    for item in llm_results['flagged']:
        decision = item['filter_decision']
        print(f"   • ${item['price']:.2f} - {decision.reason}")
    
    return llm_results

def compare_filtering_methods():
    """Compare both filtering methods side by side"""
    
    print("\n🔍 Filtering Method Comparison")
    print("=" * 60)
    
    # Test both methods
    enhanced_results = test_enhanced_filtering()
    llm_results = test_llm_filtering()
    
    if not llm_results:
        print("Cannot compare - LLM filtering not available")
        return
    
    print(f"\n📈 Comparison Summary:")
    print(f"{'Method':<20} {'Kept':<8} {'Removed':<8} {'Precision':<10}")
    print("-" * 50)
    
    enhanced_kept = len(enhanced_results['filtered_data'])
    enhanced_removed = len(enhanced_results['removed_suspicious']) + len(enhanced_results['removed_statistical'])
    enhanced_total = enhanced_kept + enhanced_removed
    
    llm_kept = llm_results['analysis_summary']['kept_count']
    llm_removed = llm_results['analysis_summary']['removed_count'] + llm_results['analysis_summary']['flagged_count']
    llm_total = llm_kept + llm_removed
    
    print(f"{'Enhanced (Rules)':<20} {enhanced_kept:<8} {enhanced_removed:<8} {enhanced_kept/enhanced_total:.1%}")
    print(f"{'LLM-Enhanced':<20} {llm_kept:<8} {llm_removed:<8} {llm_kept/llm_total:.1%}")
    
    # Show unique catches
    print(f"\n🎯 Unique Advantages:")
    print(f"Enhanced Filtering: Good at statistical outliers and basic price thresholds")
    print(f"LLM Filtering: Understands semantic meaning, language detection, context awareness")

def main():
    """Main test function"""
    
    print("🧪 PokeQuant Filtering System Test")
    print("=" * 60)
    
    compare_filtering_methods()
    
    print(f"\n💡 Recommendations:")
    print(f"   • Use LLM filtering for maximum accuracy when API key is available")
    print(f"   • Enhanced filtering provides good baseline without API costs")
    print(f"   • LLM filtering excels at semantic understanding and language detection")
    print(f"   • Combined approach ensures robustness")

if __name__ == "__main__":
    main() 