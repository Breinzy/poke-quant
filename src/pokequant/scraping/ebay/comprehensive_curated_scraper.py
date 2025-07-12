#!/usr/bin/env python3
"""
Comprehensive Curated Scraper
Combines eBay scraping and PriceCharting historical data collection for our curated investment targets
"""

import sys
import os
import time
import json
from typing import List, Dict, Any
from datetime import datetime
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_selector import CardSelector
from search_generator import SearchGenerator
from ebay_search import eBaySearcher
from ebay_parser import eBayParser
from ebay_to_supabase import eBaySupabaseUploader
from market_analyzer import MarketAnalyzer
from targeted_scraper import TargetedeBayScraper
from pricecharting_scraper_fixed import PriceChartingScraperFixed
from listing_quality_filter_fixed import ListingQualityFilterFixed

class ComprehensiveCuratedScraper:
    """Comprehensive scraper for curated investment targets"""
    
    def __init__(self):
        self.card_selector = CardSelector()
        self.ebay_scraper = TargetedeBayScraper()  # Keep for compatibility
        self.search_generator = SearchGenerator()
        self.ebay_searcher = eBaySearcher()
        self.parser = eBayParser()
        self.uploader = eBaySupabaseUploader()
        self.analyzer = MarketAnalyzer()
        
        # Use fixed quality filter
        self.quality_filter = ListingQualityFilterFixed()
        
        self.pc_scraper = PriceChartingScraperFixed()
        
    def run_full_analysis(self, ebay_comprehensive: bool = True, 
                         include_pricecharting: bool = True,
                         max_cards: int = None) -> Dict[str, Any]:
        """
        Run comprehensive analysis of curated investment targets
        
        Args:
            ebay_comprehensive: Use comprehensive eBay scraping settings
            include_pricecharting: Include PriceCharting historical data
            max_cards: Limit number of items to process
        """
        
        print("🚀 STARTING COMPREHENSIVE CURATED INVESTMENT ANALYSIS")
        print("=" * 70)
        
        start_time = time.time()
        
        # Phase 1: Get curated targets
        print("\n📊 Phase 1: Getting curated investment targets...")
        cards = self.card_selector.get_curated_investment_targets()
        sealed_products = self.card_selector.get_sealed_products_list()
        
        # Apply limits if specified
        if max_cards:
            total_items = len(cards) + len(sealed_products)
            if total_items > max_cards:
                # Prioritize cards over sealed products
                if len(cards) >= max_cards:
                    cards = cards[:max_cards]
                    sealed_products = []
                else:
                    remaining = max_cards - len(cards)
                    sealed_products = sealed_products[:remaining]
        
        print(f"✅ Selected {len(cards)} cards and {len(sealed_products)} sealed products")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'cards_analyzed': len(cards),
            'sealed_products_analyzed': len(sealed_products),
            'ebay_results': {},
            'pricecharting_results': {},
            'processing_time': 0,
            'status': 'started'
        }
        
        # Phase 2: eBay scraping
        print(f"\n🎯 Phase 2: eBay comprehensive scraping...")
        try:
            ebay_results = self.ebay_scraper.run_targeted_scraping(
                selection_strategy="curated",
                max_cards=len(cards) + len(sealed_products),
                comprehensive=ebay_comprehensive
            )
            results['ebay_results'] = ebay_results
            print(f"✅ eBay scraping completed")
            
        except Exception as e:
            print(f"❌ eBay scraping failed: {e}")
            results['ebay_results'] = {'error': str(e)}
        
        # Phase 3: PriceCharting historical data
        if include_pricecharting:
            print(f"\n📈 Phase 3: PriceCharting historical data collection...")
            try:
                # Create a temporary method for compatibility
                pc_results = {
                    'cards': [],
                    'sealed_products': [],
                    'total_items_processed': 0,
                    'successful_scrapes': 0,
                    'failed_scrapes': 0,
                    'errors': []
                }
                
                # Process cards with fixed scraper
                for card in cards:
                    try:
                        card_name = card.get('card_name', 'Unknown')
                        set_name = card.get('set_name', '')
                        
                        # Search for the card
                        pc_url = self.pc_scraper.search_card_on_pricecharting(card_name, set_name, card_data=card)
                        
                        if pc_url:
                            # Use the fixed scrape method
                            price_data = self.pc_scraper.scrape_price_history_fixed(pc_url)
                            
                            if price_data:
                                card_result = {
                                    'card_id': card.get('id'),
                                    'card_name': card_name,
                                    'set_name': set_name,
                                    'pricecharting_data': price_data
                                }
                                pc_results['cards'].append(card_result)
                                pc_results['successful_scrapes'] += 1
                            else:
                                pc_results['failed_scrapes'] += 1
                        else:
                            pc_results['failed_scrapes'] += 1
                        
                        pc_results['total_items_processed'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing card {card.get('card_name', 'Unknown')}: {e}"
                        print(f"  ❌ {error_msg}")
                        pc_results['errors'].append(error_msg)
                        pc_results['failed_scrapes'] += 1
                
                # Process sealed products with fixed scraper
                for product in sealed_products:
                    try:
                        product_name = product.get('product_name', 'Unknown')
                        
                        # Search for the product
                        pc_url = self.pc_scraper.search_sealed_product_on_pricecharting(product_name)
                        
                        if pc_url:
                            # Use the fixed scrape method
                            price_data = self.pc_scraper.scrape_price_history_fixed(pc_url)
                            
                            if price_data:
                                product_result = {
                                    'product_id': product.get('id'),
                                    'product_name': product_name,
                                    'product_type': product.get('product_type', ''),
                                    'pricecharting_data': price_data
                                }
                                pc_results['sealed_products'].append(product_result)
                                pc_results['successful_scrapes'] += 1
                            else:
                                pc_results['failed_scrapes'] += 1
                        else:
                            pc_results['failed_scrapes'] += 1
                        
                        pc_results['total_items_processed'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing product {product.get('product_name', 'Unknown')}: {e}"
                        print(f"  ❌ {error_msg}")
                        pc_results['errors'].append(error_msg)
                        pc_results['failed_scrapes'] += 1
                results['pricecharting_results'] = pc_results
                
                # Save PriceCharting data
                self.pc_scraper.save_historical_data(pc_results)
                print(f"✅ PriceCharting scraping completed")
                
            except Exception as e:
                print(f"❌ PriceCharting scraping failed: {e}")
                results['pricecharting_results'] = {'error': str(e)}
        else:
            print(f"⏭️ Skipping PriceCharting data collection")
        
        # Phase 4: Summary and next steps
        results['processing_time'] = time.time() - start_time
        results['status'] = 'completed'
        
        self._save_comprehensive_results(results)
        self._print_comprehensive_summary(results)
        self._provide_next_steps_guidance(results)
        
        return results
    
    def _save_comprehensive_results(self, results: Dict[str, Any]):
        """Save comprehensive results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/comprehensive_analysis_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Comprehensive results saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save comprehensive results: {e}")
    
    def _print_comprehensive_summary(self, results: Dict[str, Any]):
        """Print comprehensive analysis summary"""
        
        print(f"\n{'='*70}")
        print("🎯 COMPREHENSIVE INVESTMENT ANALYSIS COMPLETE")
        print(f"{'='*70}")
        
        # Overview
        print(f"📊 OVERVIEW:")
        print(f"  Items analyzed: {results['cards_analyzed']} cards + {results['sealed_products_analyzed']} sealed products")
        print(f"  Processing time: {results['processing_time']:.1f}s")
        print(f"  Status: {results['status']}")
        
        # eBay results
        ebay_results = results.get('ebay_results', {})
        if ebay_results and not ebay_results.get('error'):
            print(f"\n🎯 EBAY SCRAPING RESULTS:")
            print(f"  Searches executed: {ebay_results.get('total_searches_executed', 0)}")
            print(f"  Listings found: {ebay_results.get('total_listings_found', 0)}")
            print(f"  Listings uploaded: {ebay_results.get('total_listings_uploaded', 0)}")
            
            if ebay_results.get('total_searches_executed', 0) > 0:
                avg_listings = ebay_results.get('total_listings_found', 0) / ebay_results.get('total_searches_executed', 1)
                print(f"  Avg listings per search: {avg_listings:.1f}")
        else:
            print(f"\n❌ EBAY SCRAPING: Failed or skipped")
        
        # PriceCharting results
        pc_results = results.get('pricecharting_results', {})
        if pc_results and not pc_results.get('error'):
            print(f"\n📈 PRICECHARTING RESULTS:")
            print(f"  Items processed: {pc_results.get('total_items_processed', 0)}")
            print(f"  Successful scrapes: {pc_results.get('successful_scrapes', 0)}")
            print(f"  Failed scrapes: {pc_results.get('failed_scrapes', 0)}")
            print(f"  Cards with historical data: {len(pc_results.get('cards', []))}")
            print(f"  Sealed products with data: {len(pc_results.get('sealed_products', []))}")
        else:
            print(f"\n📈 PRICECHARTING: Failed or skipped")
        
        print(f"{'='*70}")
    
    def _provide_next_steps_guidance(self, results: Dict[str, Any]):
        """Provide guidance on next steps for quant analysis"""
        
        print(f"\n🚀 NEXT STEPS FOR QUANT ANALYSIS:")
        print(f"{'='*50}")
        
        # Data readiness assessment
        ebay_data = results.get('ebay_results', {}).get('total_listings_uploaded', 0) > 0
        pc_data = len(results.get('pricecharting_results', {}).get('cards', [])) > 0
        
        print(f"📊 DATA READINESS:")
        print(f"  ✅ eBay data: {'Available' if ebay_data else 'Missing'}")
        print(f"  ✅ Historical data: {'Available' if pc_data else 'Missing'}")
        
        if ebay_data and pc_data:
            print(f"\n🎯 RECOMMENDED NEXT STEPS:")
            print(f"  1. 📈 Start building quant models in /quant directory")
            print(f"  2. 🔗 Join eBay data with PriceCharting historical data")
            print(f"  3. 📊 Calculate key metrics (volatility, trends, momentum)")
            print(f"  4. 🤖 Build predictive models for price movements")
            print(f"  5. 📱 Set up alerts for investment opportunities")
            
        elif ebay_data:
            print(f"\n⚠️ PARTIAL DATA - EBAY ONLY:")
            print(f"  1. Consider running PriceCharting scraper separately")
            print(f"  2. Can still do basic analysis with eBay data")
            print(f"  3. Focus on recent market trends and condition premiums")
            
        elif pc_data:
            print(f"\n⚠️ PARTIAL DATA - HISTORICAL ONLY:")
            print(f"  1. Consider running eBay scraper again")
            print(f"  2. Can analyze long-term trends with PriceCharting data")
            print(f"  3. Focus on historical performance analysis")
            
        else:
            print(f"\n❌ INSUFFICIENT DATA:")
            print(f"  1. Re-run both scrapers with debug enabled")
            print(f"  2. Check database connectivity and card selection")
            print(f"  3. Verify target cards exist in pokemon_cards table")
        
        print(f"\n💡 QUANT MODEL IDEAS:")
        print(f"  • Price momentum indicators")
        print(f"  • Volatility-based risk scoring")
        print(f"  • Condition premium analysis (PSA 10 vs raw)")
        print(f"  • Seasonal trend detection")
        print(f"  • Market liquidity scoring")
        print(f"  • Cross-set correlation analysis")
        
        print(f"\n📝 FILES TO CREATE IN /quant:")
        print(f"  • data_preparation.py (join eBay + PriceCharting data)")
        print(f"  • feature_engineering.py (calculate technical indicators)")
        print(f"  • price_prediction_model.py (ML models)")
        print(f"  • portfolio_optimizer.py (investment allocation)")
        print(f"  • alert_system.py (opportunity detection)")
        
        print(f"{'='*50}")

def main():
    """Command line interface for comprehensive curated scraping"""
    
    parser = argparse.ArgumentParser(description="Comprehensive Curated Investment Analysis")
    parser.add_argument("--skip-ebay", action="store_true", help="Skip eBay scraping")
    parser.add_argument("--skip-pricecharting", action="store_true", help="Skip PriceCharting scraping")
    parser.add_argument("--max-items", type=int, help="Maximum items to process")
    parser.add_argument("--light-mode", action="store_true", help="Use lighter scraping settings")
    
    args = parser.parse_args()
    
    scraper = ComprehensiveCuratedScraper()
    
    try:
        results = scraper.run_full_analysis(
            ebay_comprehensive=not args.light_mode,
            include_pricecharting=not args.skip_pricecharting,
            max_cards=args.max_items
        )
        
        if results['status'] == 'completed':
            print(f"\n🎉 SUCCESS: Comprehensive analysis completed!")
        else:
            print(f"\n⚠️ PARTIAL SUCCESS: Some components failed")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")

if __name__ == "__main__":
    main() 