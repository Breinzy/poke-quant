#!/usr/bin/env python3
"""
Test script to demonstrate PokeQuant analysis caching functionality
"""

import time
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant.pokequant_main import PokeQuantOrchestrator

def test_analysis_caching():
    """Test analysis caching functionality"""
    
    print("🧪 Testing PokeQuant Analysis Caching")
    print("=" * 50)
    
    # Use short cache time for testing
    orchestrator = PokeQuantOrchestrator(max_age_days=7, analysis_cache_hours=1)
    
    # Test product
    product_name = "Brilliant Stars Booster Box"
    
    print(f"\n🎯 Testing with product: {product_name}")
    
    # Run first analysis
    print("\n1️⃣ Running first analysis...")
    start_time = time.time()
    result1 = orchestrator.analyze_product(product_name)
    time1 = time.time() - start_time
    
    if result1['success']:
        print(f"✅ First analysis completed in {time1:.1f} seconds")
        print(f"   Used cached: {result1.get('used_cached_analysis', False)}")
        print(f"   Recommendation: {result1['final_analysis']['recommendation']['recommendation']}")
    else:
        print(f"❌ First analysis failed: {result1.get('error')}")
        return
    
    # Run second analysis immediately (should use cache)
    print("\n2️⃣ Running second analysis immediately...")
    start_time = time.time()
    result2 = orchestrator.analyze_product(product_name)
    time2 = time.time() - start_time
    
    if result2['success']:
        print(f"✅ Second analysis completed in {time2:.1f} seconds")
        print(f"   Used cached: {result2.get('used_cached_analysis', False)}")
        print(f"   Recommendation: {result2['final_analysis']['recommendation']['recommendation']}")
        print(f"   Speed improvement: {time1/time2:.1f}x faster")
    else:
        print(f"❌ Second analysis failed: {result2.get('error')}")
        return
    
    # Run third analysis with force flag
    print("\n3️⃣ Running third analysis with force flag...")
    start_time = time.time()
    result3 = orchestrator.analyze_product(product_name, force_analysis=True)
    time3 = time.time() - start_time
    
    if result3['success']:
        print(f"✅ Third analysis completed in {time3:.1f} seconds")
        print(f"   Used cached: {result3.get('used_cached_analysis', False)}")
        print(f"   Recommendation: {result3['final_analysis']['recommendation']['recommendation']}")
    else:
        print(f"❌ Third analysis failed: {result3.get('error')}")
        return
    
    # Check analysis history
    print("\n4️⃣ Checking analysis history...")
    history = orchestrator.get_analysis_history(product_name)
    
    print(f"   Found {len(history)} analysis records")
    for i, analysis in enumerate(history[:3], 1):
        print(f"   #{i}: {analysis['analysis_date'][:19]} - {analysis['recommendation']}")
    
    print("\n🎉 Caching test completed successfully!")
    
    # Summary
    print("\n📊 Performance Summary:")
    print(f"   First analysis (fresh): {time1:.1f}s")
    print(f"   Second analysis (cached): {time2:.1f}s")
    print(f"   Third analysis (forced): {time3:.1f}s")
    print(f"   Cache speedup: {time1/time2:.1f}x")

if __name__ == "__main__":
    test_analysis_caching() 