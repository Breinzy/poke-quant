#!/usr/bin/env python3
"""
PokeQuant Integration Test
Tests the complete flow with PriceCharting integration and price data service
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant.pokequant_main import PokeQuantOrchestrator
from quant.price_data_service import PriceDataService

def test_price_data_service():
    """Test the price data service functionality"""
    
    print("🧪 Testing Price Data Service")
    print("=" * 50)
    
    service = PriceDataService()
    
    # Test product creation
    test_product_id = service.ensure_product_exists(
        'sealed', '1', 'Test Booster Box', 'Test Set'
    )
    
    if test_product_id:
        print(f"✅ Successfully created/found product: {test_product_id}")
        
        # Test price series retrieval
        price_data = service.get_price_series(test_product_id)
        print(f"📊 Price series result: {price_data['success']}")
        
        if price_data['success']:
            print(f"   Data points: {price_data['summary']['total_data_points']}")
            print(f"   Sources: {price_data['summary']['sources']}")
        
        # Test data quality calculation
        quality_score = service.calculate_data_quality_score(test_product_id)
        print(f"📈 Data quality score: {quality_score:.2f}")
        
    else:
        print("❌ Failed to create/find product")
    
    print()

def test_pokequant_main_flow():
    """Test the main PokeQuant flow with enhanced integration"""
    
    print("🚀 Testing Complete PokeQuant Flow")
    print("=" * 50)
    
    orchestrator = PokeQuantOrchestrator(max_age_days=7)
    
    # Test with Brilliant Stars Booster Box (known to have data)
    test_product = "Brilliant Stars Booster Box"
    
    print(f"🎯 Testing with: {test_product}")
    print()
    
    try:
        result = orchestrator.analyze_product(test_product, force_refresh=False)
        
        if result['success']:
            print(f"✅ Analysis completed successfully!")
            print()
            
            # Display key results
            final_analysis = result['final_analysis']
            
            print("📊 ANALYSIS SUMMARY")
            print("-" * 30)
            
            # Product info
            product_info = final_analysis['product']['product']
            print(f"Product: {product_info['display_name']}")
            print(f"Type: {product_info['type']}")
            print()
            
            # Data summary
            data_summary = final_analysis.get('data_summary', {})
            if data_summary:
                print(f"Data Points: {data_summary.get('total_data_points', 'N/A')}")
                print(f"Sources: {', '.join(data_summary.get('sources', []))}")
                print(f"Price Range: ${data_summary.get('price_range', {}).get('min', 'N/A')} - ${data_summary.get('price_range', {}).get('max', 'N/A')}")
                print()
            
            # Metrics
            metrics = final_analysis.get('metrics', {})
            if metrics:
                price_stats = metrics.get('price_stats', {})
                print(f"Average Price: ${price_stats.get('average', 'N/A')}")
                print(f"Volatility: {price_stats.get('volatility_percent', 'N/A')}%")
                
                trend = metrics.get('trend_analysis', {})
                print(f"Trend: {trend.get('direction', 'N/A')} ({trend.get('strength', 'N/A')}%)")
                
                # Data sources breakdown
                data_sources = metrics.get('data_sources', {})
                if data_sources:
                    print(f"Source Breakdown:")
                    for source, info in data_sources.items():
                        print(f"  {source}: {info['count']} points, avg ${info['average']}")
                print()
            
            # Recommendation
            recommendation = final_analysis.get('recommendation', {})
            if recommendation:
                print(f"💡 RECOMMENDATION: {recommendation.get('recommendation', 'N/A')}")
                print(f"Confidence: {recommendation.get('confidence', 'N/A')}")
                print(f"Risk Level: {recommendation.get('risk_level', 'N/A')}")
                
                target_prices = recommendation.get('target_prices', {})
                if target_prices:
                    print(f"Target Buy: ${target_prices.get('buy_below', 'N/A')}")
                    print(f"Target Sell: ${target_prices.get('sell_above', 'N/A')}")
                
                reasoning = recommendation.get('reasoning', [])
                if reasoning:
                    print("Reasoning:")
                    for reason in reasoning:
                        print(f"  • {reason}")
                print()
            
            # Stage results
            print("🔍 STAGE RESULTS")
            print("-" * 30)
            stages = result['stages']
            
            for stage_name, stage_result in stages.items():
                if isinstance(stage_result, dict):
                    status = stage_result.get('status', stage_result.get('success', 'unknown'))
                    print(f"{stage_name}: {status}")
                    
                    # Show additional details for data collection
                    if stage_name == 'data_collection' and isinstance(stage_result, dict):
                        if 'ebay_scraping' in stage_result:
                            ebay_status = stage_result['ebay_scraping'].get('status', 'unknown')
                            print(f"  eBay: {ebay_status}")
                        
                        if 'pricecharting_scraping' in stage_result:
                            pc_status = stage_result['pricecharting_scraping'].get('status', 'unknown')
                            print(f"  PriceCharting: {pc_status}")
                        
                        if 'ebay_aggregation' in stage_result:
                            agg_result = stage_result['ebay_aggregation']
                            if agg_result.get('success'):
                                print(f"  eBay Aggregation: {agg_result.get('stored_points', 0)} points stored")
                        
                        if 'pricecharting_aggregation' in stage_result:
                            agg_result = stage_result['pricecharting_aggregation']
                            if agg_result.get('success'):
                                print(f"  PriceCharting Aggregation: {agg_result.get('stored_points', 0)} points stored")
            
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            
            # Show stage results even on failure
            stages = result.get('stages', {})
            if stages:
                print("\n🔍 STAGE RESULTS")
                print("-" * 30)
                for stage_name, stage_result in stages.items():
                    print(f"{stage_name}: {stage_result}")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

def test_pricecharting_integration():
    """Test PriceCharting scraper integration specifically"""
    
    print("💰 Testing PriceCharting Integration")
    print("=" * 50)
    
    orchestrator = PokeQuantOrchestrator()
    
    # Test PriceCharting scraping for a known product
    test_result = orchestrator._scrape_pricecharting_data(
        'sealed', '1', 'Pokemon Brilliant Stars Booster Box'
    )
    
    print(f"PriceCharting scraping result: {test_result.get('status', 'unknown')}")
    
    if test_result.get('status') == 'success':
        print(f"✅ Found {test_result.get('data_points', 0)} historical data points")
        print(f"URL: {test_result.get('url', 'N/A')}")
        
        current_prices = test_result.get('current_prices', {})
        if current_prices:
            print("Current prices:")
            for condition, price in current_prices.items():
                print(f"  {condition}: ${price}")
    elif test_result.get('status') == 'failed':
        print(f"❌ PriceCharting scraping failed: {test_result.get('error', 'Unknown error')}")
    else:
        print(f"⚠️ PriceCharting scraping: {test_result}")
    
    print()

def main():
    """Run all integration tests"""
    
    print("🧪 PokeQuant Integration Test Suite")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test 1: Price Data Service
    test_price_data_service()
    
    # Test 2: PriceCharting Integration
    test_pricecharting_integration()
    
    # Test 3: Complete Flow
    test_pokequant_main_flow()
    
    print("✅ Integration test suite completed!")

if __name__ == "__main__":
    main() 