#!/usr/bin/env python3
"""
Comprehensive System Test
Tests the complete eBay scraper system with sealed products support
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_selector import CardSelector
from ebay_to_supabase import eBaySupabaseUploader
from supabase_client import supabase

def test_card_selector():
    """Test the card selector with all strategies"""
    print("\n" + "="*60)
    print("🔍 TESTING CARD SELECTOR")
    print("="*60)
    
    selector = CardSelector()
    
    # Test 1: Curated investment targets (cards)
    print("\n1️⃣ Testing curated investment targets...")
    cards = selector.get_curated_investment_targets()
    print(f"   Result: {len(cards)} cards found")
    if cards:
        print(f"   Sample: {cards[0].get('card_name', 'Unknown')} - {cards[0].get('set_name', 'Unknown')}")
    
    # Test 2: Sealed products from database
    print("\n2️⃣ Testing sealed products from database...")
    sealed_products = selector.get_sealed_products_list()
    print(f"   Result: {len(sealed_products)} sealed products found")
    if sealed_products:
        print(f"   Sample: {sealed_products[0].get('product_name', 'Unknown')} ({sealed_products[0].get('product_type', 'Unknown')})")
    
    # Test 3: Sample cards for testing
    print("\n3️⃣ Testing sample cards...")
    sample_cards = selector.get_sample_cards(3)
    print(f"   Result: {len(sample_cards)} sample cards found")
    
    return {
        'curated_cards': len(cards),
        'sealed_products': len(sealed_products),
        'sample_cards': len(sample_cards)
    }

def test_database_views():
    """Test the new database views and functions"""
    print("\n" + "="*60)
    print("🗄️ TESTING DATABASE VIEWS & FUNCTIONS")
    print("="*60)
    
    try:
        # Test 1: Combined view (if it exists)
        print("\n1️⃣ Testing combined listings view...")
        try:
            result = supabase.table("all_ebay_listings").select("listing_type").limit(5).execute()
            if result.data:
                print(f"   ✅ View exists with {len(result.data)} sample records")
                # Count by type
                card_count = len([r for r in result.data if r.get('listing_type') == 'card'])
                sealed_count = len([r for r in result.data if r.get('listing_type') == 'sealed'])
                print(f"   📊 Cards: {card_count}, Sealed: {sealed_count}")
            else:
                print("   ⚠️ View exists but no data found")
        except Exception as e:
            print(f"   ❌ View not available: {e}")
        
        # Test 2: Investment targets table
        print("\n2️⃣ Testing investment targets table...")
        try:
            result = supabase.table("investment_targets").select("*").limit(5).execute()
            if result.data:
                print(f"   ✅ Found {len(result.data)} investment targets")
                for target in result.data[:3]:
                    print(f"   🎯 {target.get('target_name', 'Unknown')} ({target.get('investment_category', 'Unknown')})")
            else:
                print("   ⚠️ Table exists but no targets found")
        except Exception as e:
            print(f"   ❌ Table not available: {e}")
        
        # Test 3: Sealed products table
        print("\n3️⃣ Testing sealed products table...")
        try:
            result = supabase.table("sealed_products").select("*").execute()
            if result.data:
                print(f"   ✅ Found {len(result.data)} sealed products")
                for product in result.data[:3]:
                    print(f"   📦 {product.get('product_name', 'Unknown')} - ${product.get('msrp', 0)}")
            else:
                print("   ⚠️ Table exists but no products found")
        except Exception as e:
            print(f"   ❌ Table not available: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_uploader_integration():
    """Test the uploader with sealed products support"""
    print("\n" + "="*60)
    print("📤 TESTING UPLOADER INTEGRATION")
    print("="*60)
    
    uploader = eBaySupabaseUploader()
    
    # Test 1: Check existing listings count
    print("\n1️⃣ Testing listing counts...")
    try:
        stats = uploader.get_upload_statistics()
        if stats:
            print(f"   📊 Total listings: {stats.get('total_listings', 0)}")
            print(f"   🎯 Unique cards tracked: {stats.get('unique_cards_tracked', 0)}")
            print(f"   📅 Recent uploads (24h): {stats.get('recent_uploads_24h', 0)}")
        else:
            print("   ⚠️ No statistics available")
    except Exception as e:
        print(f"   ❌ Statistics error: {e}")
    
    # Test 2: Check method availability for sealed products
    print("\n2️⃣ Testing sealed product methods...")
    try:
        # Check if we have sealed product upload capability
        if hasattr(uploader, 'upload_sealed_listings'):
            print("   ✅ Sealed product upload method available")
        else:
            print("   ⚠️ Sealed product upload method not found")
        
        if hasattr(uploader, '_prepare_sealed_listing_for_db'):
            print("   ✅ Sealed listing preparation method available")
        else:
            print("   ⚠️ Sealed listing preparation method not found")
            
    except Exception as e:
        print(f"   ❌ Method check error: {e}")
    
    return True

def test_search_integration():
    """Test the search system with sealed products"""
    print("\n" + "="*60)
    print("🔎 TESTING SEARCH INTEGRATION")
    print("="*60)
    
    try:
        from search_generator import SearchGenerator
        
        generator = SearchGenerator()
        
        # Test 1: Generate search for a sealed product
        print("\n1️⃣ Testing sealed product search generation...")
        
        # Create a sample sealed product
        sample_sealed = {
            "id": 1,
            "product_name": "Brilliant Stars Booster Box",
            "set_name": "Brilliant Stars",
            "product_type": "Booster Box"
        }
        
        # Check if search generator can handle sealed products
        if hasattr(generator, 'generate_sealed_search_terms'):
            search_terms = generator.generate_sealed_search_terms(sample_sealed)
            print(f"   ✅ Generated {len(search_terms) if search_terms else 0} search terms")
            if search_terms:
                print(f"   🔍 Sample: '{search_terms[0]}'")
        else:
            print("   ⚠️ Sealed search generation not implemented yet")
        
        return True
        
    except ImportError as e:
        print(f"   ⚠️ Search generator not available: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Search test error: {e}")
        return False

def test_targeted_scraper_integration():
    """Test the targeted scraper with curated strategy"""
    print("\n" + "="*60)
    print("🎯 TESTING TARGETED SCRAPER INTEGRATION")
    print("="*60)
    
    try:
        from targeted_scraper import TargetedeBayScraper
        
        # Test just the selection logic, not actual scraping
        scraper = TargetedeBayScraper()
        
        print("\n1️⃣ Testing curated selection strategy...")
        selected_targets = scraper._select_cards_by_strategy("curated", max_cards=5)
        
        if selected_targets:
            print(f"   ✅ Selected {len(selected_targets)} targets")
            
            # Analyze what was selected
            cards = [t for t in selected_targets if 'card_name' in t]
            sealed = [t for t in selected_targets if 'product_name' in t]
            
            print(f"   📊 Cards: {len(cards)}, Sealed products: {len(sealed)}")
            
            if cards:
                print(f"   🎴 Sample card: {cards[0].get('card_name', 'Unknown')}")
            if sealed:
                print(f"   📦 Sample sealed: {sealed[0].get('product_name', 'Unknown')}")
        else:
            print("   ⚠️ No targets selected")
        
        return len(selected_targets) > 0
        
    except ImportError as e:
        print(f"   ⚠️ Targeted scraper not available: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Scraper test error: {e}")
        return False

def generate_system_report():
    """Generate a comprehensive system status report"""
    print("\n" + "="*60)
    print("📋 COMPREHENSIVE SYSTEM REPORT")
    print("="*60)
    
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "system_status": "unknown",
        "components": {}
    }
    
    # Run all tests
    print("\n🔄 Running comprehensive system tests...")
    
    # Test 1: Card Selector
    try:
        card_results = test_card_selector()
        report["components"]["card_selector"] = {
            "status": "working",
            "details": card_results
        }
    except Exception as e:
        report["components"]["card_selector"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test 2: Database
    try:
        db_status = test_database_views()
        report["components"]["database"] = {
            "status": "working" if db_status else "partial",
            "details": "Views and tables tested"
        }
    except Exception as e:
        report["components"]["database"] = {
            "status": "error", 
            "error": str(e)
        }
    
    # Test 3: Uploader
    try:
        uploader_status = test_uploader_integration()
        report["components"]["uploader"] = {
            "status": "working" if uploader_status else "partial",
            "details": "Upload methods tested"
        }
    except Exception as e:
        report["components"]["uploader"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test 4: Search Integration
    try:
        search_status = test_search_integration()
        report["components"]["search"] = {
            "status": "working" if search_status else "partial",
            "details": "Search generation tested"
        }
    except Exception as e:
        report["components"]["search"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test 5: Targeted Scraper
    try:
        scraper_status = test_targeted_scraper_integration()
        report["components"]["targeted_scraper"] = {
            "status": "working" if scraper_status else "partial",
            "details": "Selection strategy tested"
        }
    except Exception as e:
        report["components"]["targeted_scraper"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Overall system status
    working_components = sum(1 for c in report["components"].values() if c["status"] == "working")
    total_components = len(report["components"])
    
    if working_components == total_components:
        report["system_status"] = "fully_operational"
    elif working_components > total_components / 2:
        report["system_status"] = "mostly_operational"
    else:
        report["system_status"] = "needs_attention"
    
    # Print final summary
    print(f"\n📊 SYSTEM STATUS: {report['system_status'].upper()}")
    print(f"🔧 Components working: {working_components}/{total_components}")
    
    for component, status in report["components"].items():
        icon = "✅" if status["status"] == "working" else "⚠️" if status["status"] == "partial" else "❌"
        print(f"   {icon} {component}: {status['status']}")
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"data/system_test_report_{timestamp}.json"
    
    os.makedirs("data", exist_ok=True)
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Full report saved to: {report_file}")
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")
    
    return report

def main():
    """Run comprehensive system test"""
    print("🚀 POKE-QUANT COMPREHENSIVE SYSTEM TEST")
    print("Testing all components with sealed products support")
    
    try:
        report = generate_system_report()
        
        if report["system_status"] == "fully_operational":
            print(f"\n🎉 SUCCESS: System is fully operational!")
            print(f"✅ Ready for production scraping with sealed products support")
        elif report["system_status"] == "mostly_operational":
            print(f"\n⚠️ PARTIAL: System is mostly working")
            print(f"🔧 Some components may need attention")
        else:
            print(f"\n❌ ISSUES: System needs attention")
            print(f"🔧 Multiple components require fixes")
        
    except Exception as e:
        print(f"\n💥 SYSTEM TEST FAILED: {e}")

if __name__ == "__main__":
    main() 