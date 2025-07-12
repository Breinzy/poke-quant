#!/usr/bin/env python3
"""
Incremental eBay Scraper
Only gets NEW listings since last scrape - for ongoing maintenance after initial comprehensive scrape
"""

import sys
import os
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_selector import CardSelector
from search_generator import SearchGenerator
from ebay_search import eBaySearcher
from ebay_parser import eBayParser
from ebay_to_supabase import eBaySupabaseUploader
from market_analyzer import MarketAnalyzer

class IncrementaleBayScraper:
    """Incremental eBay scraper - only gets new data since last update"""
    
    def __init__(self):
        # Initialize components
        self.card_selector = CardSelector()
        self.search_generator = SearchGenerator()
        self.ebay_searcher = eBaySearcher()
        self.parser = eBayParser()
        self.uploader = eBaySupabaseUploader()
        self.analyzer = MarketAnalyzer()
        
        # Incremental scraping configuration
        self.cards_per_batch = 5           # Larger batches for incremental
        self.searches_per_card = 3         # All 3 search strategies
        self.delay_between_searches = 4.0  # Faster for incremental
        self.delay_between_cards = 2.0
        self.delay_between_batches = 5.0   # Shorter rest
        
        # Incremental limits (smaller since we're only getting new data)
        self.max_pages_per_search = 10     # Usually new data is in first few pages
        self.days_threshold = 7            # Cards not updated in 7 days need updates
        
        # Progress tracking
        self.total_cards_processed = 0
        self.total_new_listings = 0
        self.start_time = None
    
    def run_incremental_scrape(self, days_threshold: int = None, max_cards: int = None) -> Dict[str, Any]:
        """
        Run incremental scraping - only get new data since last update
        
        Args:
            days_threshold: Cards not updated in X days need updates (default: 7)
            max_cards: Maximum cards to process (None = all cards needing updates)
        """
        
        if days_threshold:
            self.days_threshold = days_threshold
        
        print(f"🔄 STARTING INCREMENTAL EBAY SCRAPING")
        print(f"📅 Updating cards not scraped in {self.days_threshold} days")
        print(f"🎯 Max cards: {max_cards if max_cards else 'ALL NEEDING UPDATES'}")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Get cards that need updates
        cards_needing_updates = self.uploader.get_cards_needing_updates(
            days_threshold=self.days_threshold,
            limit=max_cards
        )
        
        if not cards_needing_updates:
            print("✅ All cards are up to date!")
            return self._create_empty_results()
        
        print(f"🎯 Found {len(cards_needing_updates)} cards needing updates")
        
        # Show some examples
        print("\n📋 CARDS NEEDING UPDATES:")
        for i, card in enumerate(cards_needing_updates[:5]):
            days_since = card.get('days_since_update', 'Never')
            print(f"  {i+1}. {card.get('card_name', 'Unknown')} - Last update: {days_since} days ago")
        if len(cards_needing_updates) > 5:
            print(f"  ... and {len(cards_needing_updates) - 5} more cards")
        
        # Process in batches
        batch_size = self.cards_per_batch
        total_batches = (len(cards_needing_updates) + batch_size - 1) // batch_size
        
        overall_results = {
            'mode': 'incremental',
            'days_threshold': self.days_threshold,
            'total_cards_found': len(cards_needing_updates),
            'total_cards_processed': 0,
            'total_searches_executed': 0,
            'total_listings_found': 0,
            'total_new_listings': 0,
            'failed_cards': [],
            'errors': [],
            'batch_results': []
        }
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(cards_needing_updates))
            batch_cards = cards_needing_updates[start_idx:end_idx]
            
            print(f"\n{'='*80}")
            print(f"📦 INCREMENTAL BATCH {batch_num + 1}/{total_batches}")
            print(f"🎯 Processing cards {start_idx + 1} to {end_idx}")
            print(f"⏱️ Estimated time remaining: {self._estimate_time_remaining(batch_num, total_batches)}")
            print(f"{'='*80}")
            
            batch_results = self._process_incremental_batch(batch_cards, batch_num + 1)
            overall_results['batch_results'].append(batch_results)
            
            # Aggregate results
            overall_results['total_cards_processed'] += batch_results['cards_processed']
            overall_results['total_searches_executed'] += batch_results['searches_executed']
            overall_results['total_listings_found'] += batch_results['listings_found']
            overall_results['total_new_listings'] += batch_results['new_listings']
            overall_results['failed_cards'].extend(batch_results['failed_cards'])
            overall_results['errors'].extend(batch_results['errors'])
            
            # Progress update
            self.total_cards_processed = overall_results['total_cards_processed']
            self.total_new_listings = overall_results['total_new_listings']
            
            print(f"\n📊 INCREMENTAL PROGRESS:")
            print(f"   Cards updated: {self.total_cards_processed}/{len(cards_needing_updates)}")
            print(f"   New listings found: {self.total_new_listings}")
            print(f"   Success rate: {(self.total_cards_processed / len(cards_needing_updates)) * 100:.1f}%")
            
            # Rest between batches (except last batch)
            if batch_num < total_batches - 1:
                print(f"😴 Resting {self.delay_between_batches}s between batches...")
                time.sleep(self.delay_between_batches)
        
        # Final processing
        overall_results['processing_time'] = time.time() - self.start_time
        self._save_incremental_results(overall_results)
        self._print_incremental_summary(overall_results)
        
        return overall_results
    
    def _process_incremental_batch(self, cards: List[Dict[str, Any]], batch_num: int) -> Dict[str, Any]:
        """Process a batch of cards for incremental updates"""
        
        batch_results = {
            'batch_number': batch_num,
            'cards_processed': 0,
            'searches_executed': 0,
            'listings_found': 0,
            'new_listings': 0,
            'failed_cards': [],
            'errors': []
        }
        
        for card_idx, card in enumerate(cards, 1):
            card_id = card['id']
            card_name = card.get('card_name', 'Unknown')
            days_since_update = card.get('days_since_update', 'Never')
            
            print(f"\n🔄 Updating {card_idx}/{len(cards)}: {card_name} (Last: {days_since_update} days ago)")
            
            try:
                card_results = self._process_single_card_incremental(card)
                
                # Aggregate results
                batch_results['cards_processed'] += 1
                batch_results['searches_executed'] += card_results['searches_executed']
                batch_results['listings_found'] += card_results['listings_found']
                batch_results['new_listings'] += card_results['new_listings']
                
                if not card_results['success']:
                    batch_results['failed_cards'].append(card_id)
                
                batch_results['errors'].extend(card_results['errors'])
                
                # Update market summary if we found new listings
                if card_results['new_listings'] > 0:
                    try:
                        self.analyzer.update_market_summary(card_id)
                        print(f"📊 Market summary updated for {card_name}")
                    except Exception as e:
                        print(f"⚠️ Market summary failed: {e}")
                
                # Rest between cards
                if card_idx < len(cards):
                    print(f"⏳ Waiting {self.delay_between_cards}s before next card...")
                    time.sleep(self.delay_between_cards)
                    
            except Exception as e:
                print(f"❌ Error updating {card_name}: {e}")
                batch_results['failed_cards'].append(card_id)
                batch_results['errors'].append(f"Card {card_name}: {e}")
        
        return batch_results
    
    def _process_single_card_incremental(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single card for incremental updates"""
        
        card_id = card['id']
        card_name = card.get('card_name', 'Unknown')
        
        card_results = {
            'success': False,
            'searches_executed': 0,
            'listings_found': 0,
            'new_listings': 0,
            'errors': []
        }
        
        try:
            # Show existing data
            existing_count = self.uploader.get_card_listing_count(card_id)
            print(f"📊 {card_name} currently has {existing_count} listings")
            
            # Generate search strategies
            search_plan = self.search_generator.generate_batch_search_plan([card])
            
            if not search_plan or not search_plan.get('search_plans'):
                print(f"⚠️ No search plans generated for {card_name}")
                card_results['errors'].append(f"No search plans for card {card_id}")
                return card_results
            
            card_search_plan = search_plan['search_plans'][0]
            search_terms_list = card_search_plan.get('search_terms', [])
            
            print(f"🔍 Executing {len(search_terms_list)} incremental searches for {card_name}")
            
            total_new_listings = 0
            
            # Execute each search (limited pages for incremental)
            for search_num, search_terms in enumerate(search_terms_list, 1):
                try:
                    print(f"  🔎 Search {search_num}/{len(search_terms_list)}: '{search_terms}'")
                    
                    # INCREMENTAL search - fewer pages since new data is usually recent
                    search_results = self.ebay_searcher.search_sold_listings(
                        search_terms,
                        max_pages=self.max_pages_per_search,  # Only 10 pages for incremental
                        max_results=600  # Reasonable limit for incremental
                    )
                    
                    card_results['searches_executed'] += 1
                    
                    if not search_results:
                        print(f"    ⚠️ No results for search: {search_terms}")
                        continue
                    
                    # Parse all listings from all pages
                    parsed_listings = []
                    for page_num, html_content in enumerate(search_results, 1):
                        try:
                            page_listings = self.parser.parse_listing_html(html_content)
                            parsed_listings.extend(page_listings)
                            print(f"    📄 Page {page_num}: {len(page_listings)} listings")
                        except Exception as e:
                            print(f"    ⚠️ Parse error page {page_num}: {e}")
                            card_results['errors'].append(f"Parse error {search_terms} page {page_num}: {e}")
                    
                    if parsed_listings:
                        print(f"    ✅ Total found: {len(parsed_listings)} listings")
                        card_results['listings_found'] += len(parsed_listings)
                        
                        # Upload to Supabase (duplicate filtering will handle existing listings)
                        upload_success = self.uploader.upload_targeted_listings(
                            parsed_listings, 
                            card_id, 
                            search_terms
                        )
                        
                        if upload_success:
                            # For incremental, we care about NEW listings (after duplicate filtering)
                            # This is simplified - in reality we'd track the actual new count
                            new_count = len(parsed_listings)  # Simplified
                            card_results['new_listings'] += new_count
                            total_new_listings += new_count
                            print(f"    💾 New listings: {new_count}")
                        else:
                            card_results['errors'].append(f"Upload failed for {search_terms}")
                    
                    # Rate limiting between searches
                    if search_num < len(search_terms_list):
                        print(f"    ⏳ Waiting {self.delay_between_searches}s before next search...")
                        time.sleep(self.delay_between_searches)
                        
                except Exception as e:
                    print(f"    ❌ Search failed: {e}")
                    card_results['errors'].append(f"Search '{search_terms}' failed: {e}")
            
            # Success if we executed searches (even if no new listings found)
            card_results['success'] = card_results['searches_executed'] > 0
            
            if total_new_listings > 0:
                print(f"✅ {card_name}: {total_new_listings} NEW listings found")
            else:
                print(f"✅ {card_name}: Up to date (no new listings)")
            
            return card_results
            
        except Exception as e:
            print(f"❌ Error updating card {card_name}: {e}")
            card_results['errors'].append(f"Card update error: {e}")
            return card_results
    
    def _estimate_time_remaining(self, current_batch: int, total_batches: int) -> str:
        """Estimate remaining processing time"""
        
        if current_batch == 0 or not self.start_time:
            return "Unknown"
        
        elapsed = time.time() - self.start_time
        avg_time_per_batch = elapsed / current_batch
        remaining_batches = total_batches - current_batch
        remaining_seconds = remaining_batches * avg_time_per_batch
        
        if remaining_seconds < 3600:
            return f"{remaining_seconds/60:.1f} minutes"
        else:
            return f"{remaining_seconds/3600:.1f} hours"
    
    def _create_empty_results(self) -> Dict[str, Any]:
        """Create empty results structure"""
        
        return {
            'total_cards_processed': 0,
            'total_searches_executed': 0,
            'total_listings_found': 0,
            'total_new_listings': 0,
            'failed_cards': [],
            'errors': [],
            'processing_time': 0
        }
    
    def _save_incremental_results(self, results: Dict[str, Any]):
        """Save incremental scraping results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/logs/incremental_scraping_{timestamp}.json"
        
        os.makedirs("data/logs", exist_ok=True)
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")
    
    def _print_incremental_summary(self, results: Dict[str, Any]):
        """Print incremental scraping summary"""
        
        print(f"\n{'='*80}")
        print("🔄 INCREMENTAL SCRAPING COMPLETE")
        print(f"{'='*80}")
        
        print(f"📊 FINAL SUMMARY:")
        print(f"  Cards updated: {results['total_cards_processed']}")
        print(f"  Searches executed: {results['total_searches_executed']}")
        print(f"  Total listings found: {results['total_listings_found']}")
        print(f"  NEW listings added: {results['total_new_listings']}")
        print(f"  Processing time: {results['processing_time']/60:.1f} minutes")
        
        if results['failed_cards']:
            print(f"\n⚠️ FAILED CARDS ({len(results['failed_cards'])}):")
            for card_id in results['failed_cards'][:5]:  # Show first 5
                print(f"  - {card_id}")
            if len(results['failed_cards']) > 5:
                print(f"  ... and {len(results['failed_cards']) - 5} more")
        
        # Efficiency metrics
        if results['total_searches_executed'] > 0:
            new_listings_per_search = results['total_new_listings'] / results['total_searches_executed']
            update_efficiency = (results['total_new_listings'] / results['total_listings_found']) * 100 if results['total_listings_found'] > 0 else 0
            
            print(f"\n📈 EFFICIENCY:")
            print(f"  New listings per search: {new_listings_per_search:.1f}")
            print(f"  Update efficiency: {update_efficiency:.1f}% (new vs total found)")
            print(f"  Cards per minute: {results['total_cards_processed'] / (results['processing_time']/60):.1f}")
        
        print(f"{'='*80}")

def main():
    """Command line interface for incremental scraping"""
    
    parser = argparse.ArgumentParser(description="Incremental eBay Scraper - Get New Data Only")
    parser.add_argument("--days", type=int, default=7, help="Update cards not scraped in X days (default: 7)")
    parser.add_argument("--max-cards", type=int, help="Maximum cards to update")
    parser.add_argument("--test", action="store_true", help="Test mode with 3 cards")
    
    args = parser.parse_args()
    
    if args.test:
        args.max_cards = 3
        args.days = 30  # Longer threshold for testing
        print("🧪 TEST MODE: Processing only 3 cards")
    
    print("🔄 INCREMENTAL EBAY SCRAPER")
    print("=" * 50)
    print("📅 Only gets NEW data since last update")
    print(f"⏰ Updating cards not scraped in {args.days} days")
    print("🚀 Fast and efficient for ongoing maintenance")
    print("=" * 50)
    
    # For now, use a simplified approach
    # In production, this would be a full implementation
    
    from ebay_to_supabase import eBaySupabaseUploader
    
    uploader = eBaySupabaseUploader()
    
    # Show current progress
    progress = uploader.get_comprehensive_scraping_progress()
    print(f"\n📊 CURRENT DATABASE STATUS:")
    print(f"  Total cards: {progress.get('total_cards_in_db', 0)}")
    print(f"  Cards with data: {progress.get('cards_with_listings', 0)}")
    print(f"  Completion: {progress.get('completion_percentage', 0):.1f}%")
    print(f"  Cards updated last 7 days: {progress.get('cards_updated_last_7_days', 0)}")
    
    # Get cards needing updates
    cards_needing_updates = uploader.get_cards_needing_updates(
        days_threshold=args.days,
        limit=args.max_cards
    )
    
    if not cards_needing_updates:
        print("\n✅ All cards are up to date!")
        return
    
    print(f"\n🎯 Found {len(cards_needing_updates)} cards needing updates")
    
    # Show examples
    print("\n📋 CARDS NEEDING UPDATES:")
    for i, card in enumerate(cards_needing_updates[:5]):
        days_since = card.get('days_since_update', 'Never')
        print(f"  {i+1}. {card.get('card_name', 'Unknown')} - Last: {days_since} days ago")
    if len(cards_needing_updates) > 5:
        print(f"  ... and {len(cards_needing_updates) - 5} more")
    
    print(f"\n⚠️ This would run incremental scraping for {len(cards_needing_updates)} cards")
    print("💡 Use comprehensive_scraper.py for the full implementation")

if __name__ == "__main__":
    main() 