#!/usr/bin/env python3
"""
Enhanced Comprehensive Scraper
Uses platform-specific search strategies and improved parsing
"""

import sys
import os
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_selector import CardSelector
from search_generator_enhanced import EnhancedSearchGenerator, SearchPlatform
from ebay_search import eBaySearcher
from ebay_parser import eBayParser
from ebay_to_supabase import eBaySupabaseUploader

class EnhancedComprehensiveScraper:
    """Enhanced scraper with platform-specific search strategies"""
    
    def __init__(self):
        # Initialize components
        self.card_selector = CardSelector()
        self.search_generator = EnhancedSearchGenerator()
        self.ebay_searcher = eBaySearcher()
        self.parser = eBayParser()
        self.uploader = eBaySupabaseUploader()
        
        # Configuration
        self.max_listings_per_search = 50
        self.delay_between_searches = 5.0
        self.delay_between_items = 3.0
    
    def run_enhanced_scraping(self, strategy: str = "curated", max_items: int = 3, 
                            test_mode: bool = True) -> Dict[str, Any]:
        """
        Run enhanced scraping with platform-specific search strategies
        
        Args:
            strategy: Selection strategy ('curated', 'diverse_sample', etc.)
            max_items: Maximum items to process
            test_mode: If True, run with conservative limits
        """
        
        print(f"🚀 ENHANCED COMPREHENSIVE SCRAPER")
        print(f"📊 Strategy: {strategy}, Max items: {max_items}")
        print(f"🧪 Test mode: {test_mode}")
        print()
        
        start_time = time.time()
        
        # Step 1: Select target items (cards + sealed products)
        print("🔍 Phase 1: Selecting target items...")
        selected_items = self._select_items_by_strategy(strategy, max_items)
        
        if not selected_items:
            print("❌ No items selected for scraping")
            return self._create_empty_results()
        
        print(f"✅ Selected {len(selected_items)} items for scraping")
        
        # Step 2: Generate platform-specific search plans
        print("\n🎯 Phase 2: Generating eBay search plans...")
        ebay_search_plan = self.search_generator.generate_batch_search_plan(
            selected_items, 
            platform=SearchPlatform.EBAY,
            max_terms_per_item=3 if test_mode else 5
        )
        
        print(f"📋 eBay search plan: {ebay_search_plan['total_searches']} searches")
        print(f"   Cards: {ebay_search_plan['cards_count']}")
        print(f"   Sealed products: {ebay_search_plan['sealed_products_count']}")
        
        # Step 3: Execute eBay searches with enhanced terms
        print(f"\n🛒 Phase 3: Executing enhanced eBay searches...")
        ebay_results = self._execute_ebay_searches(ebay_search_plan, test_mode)
        
        # Step 4: Generate PriceCharting search terms (for future use)
        print(f"\n💰 Phase 4: Generating PriceCharting search terms...")
        pricecharting_plan = self.search_generator.generate_batch_search_plan(
            selected_items,
            platform=SearchPlatform.PRICECHARTING,
            max_terms_per_item=2
        )
        
        # Save PriceCharting search terms for manual testing
        self._save_pricecharting_terms(pricecharting_plan)
        
        # Step 5: Compile final results
        final_results = {
            'strategy': strategy,
            'total_items_selected': len(selected_items),
            'test_mode': test_mode,
            'ebay_results': ebay_results,
            'pricecharting_search_plan': pricecharting_plan,
            'processing_time': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save comprehensive results
        self._save_results(final_results)
        self._print_summary(final_results)
        
        return final_results
    
    def _select_items_by_strategy(self, strategy: str, max_items: int) -> List[Dict[str, Any]]:
        """Select items using the specified strategy"""
        
        if strategy == "curated":
            # Get curated cards + sealed products
            cards = self.card_selector.get_curated_investment_targets()
            sealed_products = self.card_selector.get_sealed_products_list()
            
            # Combine and limit
            all_items = cards + sealed_products
            if max_items:
                all_items = all_items[:max_items]
            
            print(f"💎 Curated selection: {len(cards)} cards + {len(sealed_products)} sealed = {len(all_items)} total")
            return all_items
        
        elif strategy == "diverse_sample":
            # Mix of high-value cards
            sample_cards = self.card_selector.get_sample_cards(max_items or 5)
            print(f"🎯 Diverse sample: {len(sample_cards)} cards")
            return sample_cards
        
        elif strategy == "sealed_only":
            # Only sealed products
            sealed_products = self.card_selector.get_sealed_products_list()
            if max_items:
                sealed_products = sealed_products[:max_items]
            print(f"📦 Sealed only: {len(sealed_products)} products")
            return sealed_products
        
        else:
            print(f"❌ Unknown strategy: {strategy}")
            return []
    
    def _execute_ebay_searches(self, search_plan: Dict[str, Any], test_mode: bool) -> Dict[str, Any]:
        """Execute eBay searches using enhanced search terms"""
        
        results = {
            'total_searches_executed': 0,
            'total_listings_found': 0,
            'total_listings_uploaded': 0,
            'item_results': [],
            'failed_searches': [],
            'parsing_issues': []
        }
        
        max_pages = 1 if test_mode else 2
        max_results = 20 if test_mode else self.max_listings_per_search
        
        for item_plan in search_plan['search_plans']:
            item_name = item_plan['item_name']
            item_type = item_plan['item_type']
            search_terms_list = item_plan['search_terms']
            
            print(f"\n🎯 Processing: {item_name} ({item_type})")
            print(f"🔍 Enhanced eBay searches: {len(search_terms_list)} terms")
            
            item_results = {
                'item_name': item_name,
                'item_type': item_type,
                'searches_executed': 0,
                'listings_found': 0,
                'listings_uploaded': 0,
                'search_details': []
            }
            
            for search_num, search_terms in enumerate(search_terms_list, 1):
                try:
                    print(f"  🔎 Search {search_num}/{len(search_terms_list)}: '{search_terms}'")
                    
                    # Execute eBay search with enhanced terms
                    search_results = self.ebay_searcher.search_sold_listings(
                        search_terms,
                        max_pages=max_pages,
                        max_results=max_results
                    )
                    
                    item_results['searches_executed'] += 1
                    results['total_searches_executed'] += 1
                    
                    if not search_results:
                        print(f"    ⚠️ No results for search: {search_terms}")
                        continue
                    
                    # Parse all listings from all pages
                    all_listings = []
                    for page_num, page_html in enumerate(search_results, 1):
                        try:
                            page_listings = self.parser.parse_listing_html(page_html)
                            all_listings.extend(page_listings)
                            print(f"    📄 Page {page_num}: {len(page_listings)} listings parsed")
                        except Exception as parse_error:
                            print(f"    ❌ Page {page_num} parsing failed: {parse_error}")
                            results['parsing_issues'].append({
                                'search_terms': search_terms,
                                'page': page_num,
                                'error': str(parse_error)
                            })
                    
                    if all_listings:
                        print(f"    ✅ Total found: {len(all_listings)} listings")
                        item_results['listings_found'] += len(all_listings)
                        results['total_listings_found'] += len(all_listings)
                        
                        # For test mode, just count listings without uploading
                        if test_mode:
                            print(f"    🧪 Test mode: Skipping upload")
                            item_results['listings_uploaded'] += len(all_listings)
                            results['total_listings_uploaded'] += len(all_listings)
                        else:
                            # Upload to database
                            if item_type == "card":
                                upload_success = self.uploader.upload_targeted_listings(
                                    all_listings, item_plan['item_id'], search_terms
                                )
                            else:
                                # For sealed products, we'd need a new upload method
                                print(f"    ⚠️ Sealed product upload not implemented yet")
                                upload_success = False
                            
                            if upload_success:
                                item_results['listings_uploaded'] += len(all_listings)
                                results['total_listings_uploaded'] += len(all_listings)
                                print(f"    💾 Uploaded: {len(all_listings)} listings")
                            else:
                                print(f"    ❌ Upload failed")
                    
                    # Record search details
                    item_results['search_details'].append({
                        'search_terms': search_terms,
                        'listings_found': len(all_listings),
                        'pages_processed': len(search_results)
                    })
                    
                    # Rate limiting between searches
                    if search_num < len(search_terms_list):
                        print(f"    ⏳ Waiting {self.delay_between_searches}s...")
                        time.sleep(self.delay_between_searches)
                        
                except Exception as e:
                    print(f"    ❌ Search failed: {e}")
                    results['failed_searches'].append({
                        'search_terms': search_terms,
                        'error': str(e)
                    })
            
            # Item processing complete
            print(f"✅ {item_name}: {item_results['listings_found']} found, {item_results['listings_uploaded']} uploaded")
            results['item_results'].append(item_results)
            
            # Rate limiting between items
            time.sleep(self.delay_between_items)
        
        return results
    
    def _save_pricecharting_terms(self, pricecharting_plan: Dict[str, Any]):
        """Save PriceCharting search terms for manual testing"""
        
        print(f"💰 PriceCharting search terms (for manual testing):")
        
        terms_for_testing = []
        for item_plan in pricecharting_plan['search_plans']:
            item_info = {
                'item_name': item_plan['item_name'],
                'item_type': item_plan['item_type'],
                'pricecharting_search_terms': item_plan['search_terms']
            }
            terms_for_testing.append(item_info)
            
            print(f"  🎯 {item_plan['item_name']}:")
            for term in item_plan['search_terms']:
                print(f"    - '{term}'")
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/pricecharting_search_terms_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        try:
            with open(filename, 'w') as f:
                json.dump(terms_for_testing, f, indent=2)
            print(f"💾 PriceCharting terms saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save PriceCharting terms: {e}")
    
    def _create_empty_results(self) -> Dict[str, Any]:
        """Create empty results structure"""
        return {
            'total_items_selected': 0,
            'ebay_results': {
                'total_searches_executed': 0,
                'total_listings_found': 0,
                'total_listings_uploaded': 0
            },
            'processing_time': 0
        }
    
    def _save_results(self, results: Dict[str, Any]):
        """Save comprehensive scraping results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/enhanced_scraping_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print comprehensive summary"""
        
        print(f"\n{'='*60}")
        print("🚀 ENHANCED SCRAPING COMPLETE")
        print(f"{'='*60}")
        
        ebay_results = results['ebay_results']
        
        print(f"📊 SUMMARY:")
        print(f"  Items processed: {results['total_items_selected']}")
        print(f"  eBay searches: {ebay_results['total_searches_executed']}")
        print(f"  Listings found: {ebay_results['total_listings_found']}")
        print(f"  Listings uploaded: {ebay_results['total_listings_uploaded']}")
        print(f"  Processing time: {results['processing_time']:.1f}s")
        
        if ebay_results['total_searches_executed'] > 0:
            avg_listings = ebay_results['total_listings_found'] / ebay_results['total_searches_executed']
            print(f"  Avg listings per search: {avg_listings:.1f}")
        
        if ebay_results.get('parsing_issues'):
            print(f"\n⚠️ PARSING ISSUES ({len(ebay_results['parsing_issues'])}):")
            for issue in ebay_results['parsing_issues'][:3]:
                print(f"  - {issue['search_terms']}: {issue['error']}")
        
        print(f"{'='*60}")

def main():
    """Command line interface for enhanced scraping"""
    
    parser = argparse.ArgumentParser(description="Enhanced Comprehensive Scraper")
    parser.add_argument("--strategy", 
                       choices=["curated", "diverse_sample", "sealed_only"],
                       default="curated",
                       help="Item selection strategy")
    parser.add_argument("--max-items", type=int, default=3, help="Maximum items to process")
    parser.add_argument("--production", action="store_true", help="Run in production mode (uploads to DB)")
    
    args = parser.parse_args()
    
    scraper = EnhancedComprehensiveScraper()
    
    try:
        results = scraper.run_enhanced_scraping(
            strategy=args.strategy,
            max_items=args.max_items,
            test_mode=not args.production
        )
        
        if results['ebay_results']['total_listings_found'] > 0:
            print(f"\n🎉 SUCCESS: Found {results['ebay_results']['total_listings_found']} listings")
        else:
            print(f"\n⚠️ No listings found")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")

if __name__ == "__main__":
    main() 