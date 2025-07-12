#!/usr/bin/env python3
"""
Targeted eBay Scraper
Scrapes specific cards from database with targeted searches and multiple selection strategies
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
from search_generator import SearchGenerator
from ebay_search import eBaySearcher
from ebay_parser import eBayParser
from ebay_to_supabase import eBaySupabaseUploader
from market_analyzer import MarketAnalyzer
from listing_quality_filter_fixed import ListingQualityFilterFixed

class TargetedeBayScraper:
    """Targeted eBay scraper with multiple selection strategies"""
    
    def __init__(self):
        # Initialize components
        self.card_selector = CardSelector()
        self.search_generator = SearchGenerator()
        self.ebay_searcher = eBaySearcher()
        self.parser = eBayParser()
        self.uploader = eBaySupabaseUploader()
        self.analyzer = MarketAnalyzer()
        
        # Scraping configuration
        self.cards_per_batch = 5
        self.searches_per_card = 3
        self.delay_between_searches = 4.0
        self.delay_between_cards = 2.0
        self.max_listings_per_search = 30
        
        # Progress tracking
        self.total_cards_processed = 0
        self.total_searches_executed = 0
        self.total_listings_found = 0
        self.total_listings_uploaded = 0
        self.start_time = None
    
    def run_targeted_scraping(self, selection_strategy: str = "diverse_sample", max_cards: int = None, 
                            set_name: str = None, pokemon_name: str = None, comprehensive: bool = False,
                            offset: int = 0) -> Dict[str, Any]:
        """
        Run targeted scraping with specified strategy
        
        Args:
            selection_strategy: Strategy for selecting cards
            max_cards: Maximum cards to process
            set_name: Specific set name (for by_set strategy)
            pokemon_name: Specific Pokemon name (for by_pokemon strategy)
            comprehensive: Use comprehensive scraping settings
            offset: Starting offset for card selection
        """
        
        print(f"🎯 Starting Targeted eBay Scraping...")
        print(f"📊 Strategy: {selection_strategy}, Max cards: {max_cards}")
        print()
        
        self.start_time = time.time()
        
        # Adjust settings for comprehensive mode
        if comprehensive:
            self.max_listings_per_search = 200
            self.delay_between_searches = 6.0
            print("🌟 COMPREHENSIVE MODE: Increased limits and delays")
        
        # Phase 4: Select target cards
        print("🔍 Phase 4: Selecting target cards...")
        selected_cards = self._select_cards_by_strategy(
            selection_strategy, max_cards, set_name, pokemon_name, offset
        )
        
        if not selected_cards:
            print("❌ No cards selected for scraping")
            return self._create_empty_results()
        
        print(f"✅ Selected {len(selected_cards)} cards for scraping")
        
        # Process cards in batches
        batch_size = self.cards_per_batch
        total_batches = (len(selected_cards) + batch_size - 1) // batch_size
        
        overall_results = {
            'selection_strategy': selection_strategy,
            'total_cards_selected': len(selected_cards),
            'total_cards_processed': 0,
            'total_searches_executed': 0,
            'total_listings_found': 0,
            'total_listings_uploaded': 0,
            'failed_cards': [],
            'errors': [],
            'batch_results': []
        }
        
        print(f"\n📦 Processing {len(selected_cards)} cards in {total_batches} batches")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(selected_cards))
            batch_cards = selected_cards[start_idx:end_idx]
            
            print(f"\n📦 Processing batch {batch_num + 1}/{total_batches} ({len(batch_cards)} cards)")
            
            batch_results = self._process_card_batch(batch_cards, batch_num + 1)
            overall_results['batch_results'].append(batch_results)
            
            # Aggregate results
            overall_results['total_cards_processed'] += batch_results['cards_processed']
            overall_results['total_searches_executed'] += batch_results['searches_executed']
            overall_results['total_listings_found'] += batch_results['listings_found']
            overall_results['total_listings_uploaded'] += batch_results['listings_uploaded']
            overall_results['failed_cards'].extend(batch_results['failed_cards'])
            overall_results['errors'].extend(batch_results['errors'])
            
            # Update progress tracking
            self.total_cards_processed = overall_results['total_cards_processed']
            self.total_searches_executed = overall_results['total_searches_executed']
            self.total_listings_found = overall_results['total_listings_found']
            self.total_listings_uploaded = overall_results['total_listings_uploaded']
        
        # Final processing
        overall_results['processing_time'] = time.time() - self.start_time
        self._save_results(overall_results)
        self._print_summary(overall_results)
        
        return overall_results
    
    def _select_cards_by_strategy(self, strategy: str, max_cards: int = None, 
                                set_name: str = None, pokemon_name: str = None,
                                offset: int = 0) -> List[Dict[str, Any]]:
        """Select cards based on the specified strategy"""
        
        if strategy == "high_value":
            return self.card_selector.get_high_value_cards()[:max_cards] if max_cards else self.card_selector.get_high_value_cards()
        
        elif strategy == "curated":
            # NEW: Get our handpicked investment targets (cards + sealed products)
            cards = self.card_selector.get_curated_investment_targets()
            sealed_products = self.card_selector.get_sealed_products_list()
            
            # Combine cards and sealed products
            all_targets = cards + sealed_products
            
            if max_cards:
                all_targets = all_targets[:max_cards]
            
            print(f"💎 Selected curated targets: {len(cards)} cards + {len(sealed_products)} sealed products = {len(all_targets)} total")
            return all_targets
        
        elif strategy == "diverse_sample":
            # Get a diverse sample: Charizard + Pikachu + random sample
            charizard_cards = self.card_selector.get_cards_by_pokemon(["Charizard"])
            pikachu_cards = self.card_selector.get_cards_by_pokemon(["Pikachu"])
            sample_cards = self.card_selector.get_sample_cards(4)
            
            # Combine and limit
            all_cards = charizard_cards + pikachu_cards + sample_cards
            unique_cards = self.card_selector._remove_duplicates(all_cards)
            
            if max_cards:
                unique_cards = unique_cards[:max_cards]
            
            print(f"🎯 Selected diverse sample: {len(unique_cards)} cards")
            return unique_cards
        
        elif strategy == "by_set":
            if not set_name:
                print("⚠️ Set name required for by_set strategy")
                return []
            return self.card_selector.get_cards_by_set([set_name])[:max_cards] if max_cards else self.card_selector.get_cards_by_set([set_name])
        
        elif strategy == "by_pokemon":
            if not pokemon_name:
                print("⚠️ Pokemon name required for by_pokemon strategy")
                return []
            return self.card_selector.get_cards_by_pokemon([pokemon_name])[:max_cards] if max_cards else self.card_selector.get_cards_by_pokemon([pokemon_name])
        
        elif strategy == "custom":
            # Custom filters can be added here
            filters = {"rarity": "Rare Holo"}  # Example
            return self.card_selector.get_cards_by_custom_filter(filters)[:max_cards] if max_cards else self.card_selector.get_cards_by_custom_filter(filters)
        
        elif strategy == "all_cards":
            return self.card_selector.get_all_cards_batch(
                batch_size=max_cards if max_cards else 1000,
                offset=offset
            )
        
        else:
            print(f"❌ Unknown selection strategy: {strategy}")
            return []
    
    def _process_card_batch(self, cards: List[Dict[str, Any]], batch_num: int) -> Dict[str, Any]:
        """Process a batch of cards"""
        
        batch_results = {
            'batch_number': batch_num,
            'cards_processed': 0,
            'searches_executed': 0,
            'listings_found': 0,
            'listings_uploaded': 0,
            'failed_cards': [],
            'errors': []
        }
        
        for card_idx, card in enumerate(cards, 1):
            card_id = card['id']
            
            # Detect if this is a sealed product or card
            is_sealed_product = 'product_type' in card
            
            if is_sealed_product:
                item_name = card.get('product_name', 'Unknown Product')
                print(f"\n📦 Processing: {item_name} (Sealed Product ID: {card_id})")
            else:
                item_name = card.get('card_name', 'Unknown Card')
                print(f"\n🎯 Processing: {item_name} (Card ID: {card_id})")
            
            try:
                # Check existing data using appropriate method
                if is_sealed_product:
                    existing_count = self.uploader.get_sealed_product_listing_count(card_id)
                else:
                    existing_count = self.uploader.get_card_listing_count(card_id)
                    
                if existing_count > 0:
                    print(f"📊 {item_name} already has {existing_count} listings")
                
                # Generate search plan
                search_plan = self.search_generator.generate_batch_search_plan([card])
                
                if not search_plan or not search_plan.get('search_plans'):
                    print(f"⚠️ No search plans generated for {item_name}")
                    batch_results['failed_cards'].append(card_id)
                    continue
                
                card_search_plan = search_plan['search_plans'][0]
                search_terms_list = card_search_plan.get('search_terms', [])
                
                print(f"🔍 Generated {len(search_terms_list)} targeted search terms for {item_name}")
                print(f"🔍 Executing {len(search_terms_list)} searches for {item_name}")
                
                card_listings_uploaded = 0
                
                # Execute each search
                for search_num, search_terms in enumerate(search_terms_list, 1):
                    try:
                        print(f"  🔎 Search {search_num}/{len(search_terms_list)}: '{search_terms}'")
                        
                        # Search eBay
                        search_results = self.ebay_searcher.search_sold_listings(
                            search_terms,
                            max_pages=2,  # Conservative for targeted scraping
                            max_results=self.max_listings_per_search
                        )
                        
                        batch_results['searches_executed'] += 1
                        
                        if not search_results:
                            print(f"    ⚠️ No results for search: {search_terms}")
                            continue
                        
                        # Parse all listings from all pages
                        all_listings = []
                        for page_html in search_results:
                            page_listings = self.parser.parse_listing_html(page_html)
                            all_listings.extend(page_listings)
                        
                        if all_listings:
                            print(f"    ✅ Found {len(all_listings)} listings")
                            batch_results['listings_found'] += len(all_listings)
                            
                            # Upload to Supabase using appropriate method
                            if is_sealed_product:
                                upload_success = self.uploader.upload_sealed_product_listings(
                                    all_listings, card_id, search_terms
                                )
                            else:
                                upload_success = self.uploader.upload_targeted_listings(
                                    all_listings, card_id, search_terms
                                )
                            
                            if upload_success:
                                card_listings_uploaded += len(all_listings)
                                batch_results['listings_uploaded'] += len(all_listings)
                                print(f"    💾 Uploaded: {len(all_listings)} listings")
                            else:
                                batch_results['errors'].append(f"Upload failed for {search_terms}")
                        
                        # Rate limiting between searches
                        if search_num < len(search_terms_list):
                            print(f"    ⏳ Waiting {self.delay_between_searches}s before next search...")
                            time.sleep(self.delay_between_searches)
                            
                    except Exception as e:
                        print(f"    ❌ Search failed: {e}")
                        batch_results['errors'].append(f"Search '{search_terms}' failed: {e}")
                
                # Card/Product processing complete
                if card_listings_uploaded > 0:
                    print(f"✅ {item_name}: {card_listings_uploaded} listings uploaded")
                else:
                    print(f"⚠️ {item_name}: No listings uploaded")
                    batch_results['failed_cards'].append(card_id)
                
                batch_results['cards_processed'] += 1
                
                # Rate limiting between cards
                if card_idx < len(cards):
                    print(f"⏳ Waiting {self.delay_between_cards}s before next card...")
                    time.sleep(self.delay_between_cards)
                    
            except Exception as e:
                print(f"❌ Error processing {item_name}: {e}")
                batch_results['failed_cards'].append(card_id)
                batch_results['errors'].append(f"Item {item_name}: {e}")
        
        return batch_results
    
    def _create_empty_results(self) -> Dict[str, Any]:
        """Create empty results structure"""
        return {
            'total_cards_processed': 0,
            'total_searches_executed': 0,
            'total_listings_found': 0,
            'total_listings_uploaded': 0,
            'failed_cards': [],
            'errors': [],
            'processing_time': 0
        }
    
    def _save_results(self, results: Dict[str, Any]):
        """Save scraping results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/logs/targeted_scraping_{timestamp}.json"
        
        os.makedirs("data/logs", exist_ok=True)
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print comprehensive scraping summary"""
        
        print(f"\n{'='*60}")
        print("🎯 TARGETED SCRAPING COMPLETE")
        print(f"{'='*60}")
        
        print(f"📊 SUMMARY:")
        print(f"  Cards processed: {results['total_cards_processed']}")
        print(f"  Searches executed: {results['total_searches_executed']}")
        print(f"  Listings found: {results['total_listings_found']}")
        print(f"  Listings uploaded: {results['total_listings_uploaded']}")
        print(f"  Processing time: {results['processing_time']:.1f}s")
        
        if results['failed_cards']:
            print(f"\n⚠️ FAILED CARDS ({len(results['failed_cards'])}):")
            for card_id in results['failed_cards'][:5]:  # Show first 5
                print(f"  - Card ID: {card_id}")
            if len(results['failed_cards']) > 5:
                print(f"  ... and {len(results['failed_cards']) - 5} more")
        
        if results['errors']:
            print(f"\n❌ ERRORS ({len(results['errors'])}):")
            for error in results['errors'][:5]:  # Show first 5
                print(f"  - {error}")
            if len(results['errors']) > 5:
                print(f"  ... and {len(results['errors']) - 5} more errors")
        
        # Efficiency metrics
        if results['total_searches_executed'] > 0:
            listings_per_search = results['total_listings_found'] / results['total_searches_executed']
            upload_rate = (results['total_listings_uploaded'] / results['total_listings_found']) * 100 if results['total_listings_found'] > 0 else 0
            
            print(f"\n📈 EFFICIENCY:")
            print(f"  Avg listings per search: {listings_per_search:.1f}")
            print(f"  Upload success rate: {upload_rate:.1f}%")
        
        # Get upload statistics
        try:
            upload_stats = self.uploader.get_upload_statistics()
            if upload_stats:
                print(f"\n📊 DATABASE STATISTICS:")
                print(f"  Total listings in DB: {upload_stats.get('total_listings', 0)}")
                print(f"  Unique cards tracked: {upload_stats.get('unique_cards_tracked', 0)}")
                print(f"  Recent uploads (24h): {upload_stats.get('recent_uploads_24h', 0)}")
        except Exception as e:
            print(f"⚠️ Error getting upload statistics: {e}")
        
        print(f"{'='*60}")

def main():
    """Command line interface for targeted scraping"""
    
    parser = argparse.ArgumentParser(description="Targeted eBay Scraper")
    parser.add_argument("--strategy", 
                       choices=["high_value", "curated", "diverse_sample", "by_set", "by_pokemon", "custom", "all_cards"],
                       default="diverse_sample",
                       help="Card selection strategy")
    parser.add_argument("--max-cards", type=int, help="Maximum cards to process")
    parser.add_argument("--set-name", help="Set name (for by_set strategy)")
    parser.add_argument("--pokemon-name", help="Pokemon name (for by_pokemon strategy)")
    parser.add_argument("--comprehensive", action="store_true", help="Use comprehensive scraping settings")
    parser.add_argument("--offset", type=int, default=0, help="Starting offset for card selection")
    
    args = parser.parse_args()
    
    scraper = TargetedeBayScraper()
    
    try:
        results = scraper.run_targeted_scraping(
            selection_strategy=args.strategy,
            max_cards=args.max_cards,
            set_name=args.set_name,
            pokemon_name=args.pokemon_name,
            comprehensive=args.comprehensive,
            offset=args.offset
        )
        
        if results['total_cards_processed'] > 0:
            print(f"\n🎉 SUCCESS: Processed {results['total_cards_processed']} cards")
        else:
            print(f"\n⚠️ No cards were processed")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")

if __name__ == "__main__":
    main() 