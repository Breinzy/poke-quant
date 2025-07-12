"""
eBay to Supabase Module
Handles uploading parsed eBay data to Supabase with direct card_id foreign keys
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

class eBaySupabaseUploader:
    """Handles uploading eBay data to Supabase with targeted approach"""
    
    def __init__(self):
        self.supabase = supabase
        self.batch_size = 25  # Conservative batch size for rate limiting
    
    def parse_ebay_date(self, date_string: str) -> Optional[str]:
        """Parse eBay date strings into ISO format"""
        if not date_string:
            return None
            
        try:
            original_string = date_string
            date_string = date_string.strip()
            
            # Remove "Sold" or "Ended" prefix
            date_string = re.sub(r'^(Sold|Ended)\s*', '', date_string, flags=re.IGNORECASE)
            date_string = date_string.strip()
            
            # Try direct parsing for common formats first
            formats_to_try = [
                '%b %d, %Y',   # "Jun 28, 2025"
                '%b %d %Y',    # "Jun 28 2025"  
                '%m/%d/%Y',    # "6/28/2025"
                '%m/%d/%y',    # "6/28/25"
                '%Y-%m-%d',    # "2025-06-28"
                '%b %d',       # "Jun 28" (will add current year)
            ]
            
            for fmt in formats_to_try:
                try:
                    if fmt == '%b %d':
                        # Add current year for incomplete dates
                        test_string = f"{date_string} {datetime.now().year}"
                        parsed_date = datetime.strptime(test_string, '%b %d %Y')
                    else:
                        parsed_date = datetime.strptime(date_string, fmt)
                    
                    return parsed_date.isoformat()
                except ValueError:
                    continue
            
            # If no format worked, silently return None (dates are optional)
            return None
            
        except Exception as e:
            # Silently handle errors - dates are optional
            return None
    
    def upload_targeted_listings(self, listings: List[Dict[str, Any]], card_id: int, search_terms: str) -> bool:
        """Upload listings with direct card_id foreign key"""
        print(f"📤 Uploading {len(listings)} listings for card_id {card_id}...")
        
        if not listings:
            print("⚠️ No listings to upload")
            return True
        
        try:
            # Prepare listings for database with card_id
            db_listings = []
            for listing in listings:
                db_listing = self._prepare_listing_for_db(listing, card_id, search_terms)
                if db_listing:
                    db_listings.append(db_listing)
            
            if not db_listings:
                print("⚠️ No valid listings to upload after preparation")
                return True
            
            # Check for duplicates and filter
            new_listings = self._filter_duplicates(db_listings)
            
            if not new_listings:
                print("✅ All listings already exist in database")
                return True
            
            print(f"📝 Uploading {len(new_listings)} new listings (filtered {len(db_listings) - len(new_listings)} duplicates)")
            
            # Upload in batches
            success = self._batch_upload_listings(new_listings)
            
            if success:
                print(f"✅ Successfully uploaded {len(new_listings)} listings for card_id {card_id}")
            else:
                print(f"❌ Failed to upload listings for card_id {card_id}")
                
            return success
            
        except Exception as e:
            print(f"❌ Upload failed for card_id {card_id}: {e}")
            return False
    
    def upload_sealed_product_listings(self, listings: List[Dict[str, Any]], sealed_product_id: int, search_terms: str) -> bool:
        """Upload listings for sealed products to the ebay_sealed_listings table"""
        print(f"📤 Uploading {len(listings)} listings for sealed_product_id {sealed_product_id}...")
        
        if not listings:
            print("⚠️ No listings to upload")
            return True
        
        try:
            # Prepare listings for database with sealed_product_id
            db_listings = []
            for listing in listings:
                db_listing = self._prepare_sealed_listing_for_db(listing, sealed_product_id, search_terms)
                if db_listing:
                    db_listings.append(db_listing)
            
            if not db_listings:
                print("⚠️ No valid listings to upload after preparation")
                return True
            
            # Check for duplicates and filter
            new_listings = self._filter_sealed_duplicates(db_listings)
            
            if not new_listings:
                print("✅ All listings already exist in database")
                return True
            
            print(f"📝 Uploading {len(new_listings)} new listings (filtered {len(db_listings) - len(new_listings)} duplicates)")
            
            # Upload in batches to sealed listings table
            success = self._batch_upload_sealed_listings(new_listings)
            
            if success:
                print(f"✅ Successfully uploaded {len(new_listings)} listings for sealed_product_id {sealed_product_id}")
            else:
                print(f"❌ Failed to upload listings for sealed_product_id {sealed_product_id}")
                
            return success
            
        except Exception as e:
            print(f"❌ Upload failed for sealed_product_id {sealed_product_id}: {e}")
            return False
    
    def _prepare_listing_for_db(self, listing: Dict[str, Any], card_id: int, search_terms: str) -> Optional[Dict[str, Any]]:
        """Prepare a listing for database insertion with Phase 6 enhanced fields"""
        try:
            # Required fields check
            if not listing.get('title') or not listing.get('listing_url'):
                return None
            
            # Determine condition category and search strategy
            is_graded = listing.get('is_graded', False)
            condition_category = 'graded' if is_graded else 'raw'
            
            # Map search terms to strategy
            search_strategy = 'raw_nm'  # default
            search_lower = search_terms.lower()
            if 'psa 10' in search_lower:
                search_strategy = 'psa_10'
            elif 'psa 9' in search_lower:
                search_strategy = 'psa_9'
            
            # Extract numeric grade for sorting
            grade_numeric = None
            grade_str = listing.get('grade', '')
            if grade_str and grade_str.isdigit():
                grade_numeric = int(grade_str)
            
            db_listing = {
                'card_id': card_id,
                'title': listing.get('title', '').strip(),
                'price': float(listing.get('price', 0)),
                'listing_url': listing.get('listing_url', '').strip(),
                'search_terms': search_terms,
                'created_at': datetime.now().isoformat(),
                
                # Phase 6 enhanced fields
                'condition_category': condition_category,
                'search_strategy': search_strategy,
                'grade_numeric': grade_numeric,
                
                # Optional fields
                'condition': listing.get('condition', ''),
                'is_graded': is_graded,
                'grading_company': listing.get('grading_company', ''),
                'grade': grade_str,
                'image_url': listing.get('image_url', ''),
                'is_auction': listing.get('is_auction', False),
                'bids': int(listing.get('bids', 0)),
                'shipping': listing.get('shipping', ''),
            }
            
            # Parse sold_date if available
            sold_date = listing.get('sold_date')
            if sold_date:
                if isinstance(sold_date, str):
                    db_listing['sold_date'] = self.parse_ebay_date(sold_date)
                elif hasattr(sold_date, 'isoformat'):
                    db_listing['sold_date'] = sold_date.isoformat()
            
            return db_listing
            
        except Exception as e:
            print(f"⚠️ Error preparing listing: {e}")
            return None
    
    def _prepare_sealed_listing_for_db(self, listing: Dict[str, Any], sealed_product_id: int, search_terms: str) -> Optional[Dict[str, Any]]:
        """Prepare a sealed product listing for database insertion"""
        try:
            # Required fields check
            if not listing.get('title') or not listing.get('listing_url'):
                return None
            
            # For sealed products, condition category is always 'sealed'
            condition_category = 'sealed'
            
            # Map search terms to strategy for sealed products
            search_strategy = 'sealed_box'  # default
            search_lower = search_terms.lower()
            if 'elite trainer box' in search_lower:
                search_strategy = 'sealed_etb'
            elif 'collection box' in search_lower:
                search_strategy = 'sealed_collection'
            
            db_listing = {
                'sealed_product_id': sealed_product_id,
                'title': listing.get('title', '').strip(),
                'price': float(listing.get('price', 0)),
                'listing_url': listing.get('listing_url', '').strip(),
                'search_terms': search_terms,
                'created_at': datetime.now().isoformat(),
                
                # Enhanced fields
                'condition_category': condition_category,
                'search_strategy': search_strategy,
                'grade_numeric': None,  # Not applicable for sealed products
                
                # Optional fields
                'condition': listing.get('condition', ''),
                'is_graded': False,  # Sealed products are not graded
                'grading_company': '',
                'grade': '',
                'image_url': listing.get('image_url', ''),
                'is_auction': listing.get('is_auction', False),
                'bids': int(listing.get('bids', 0)),
                'shipping': listing.get('shipping', ''),
            }
            
            # Parse sold_date if available
            sold_date = listing.get('sold_date')
            if sold_date:
                if isinstance(sold_date, str):
                    db_listing['sold_date'] = self.parse_ebay_date(sold_date)
                elif hasattr(sold_date, 'isoformat'):
                    db_listing['sold_date'] = sold_date.isoformat()
            
            return db_listing
            
        except Exception as e:
            print(f"⚠️ Error preparing sealed listing: {e}")
            return None
    
    def _filter_duplicates(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out listings that already exist in database AND remove internal duplicates"""
        if not listings:
            return []
        
        try:
            # STEP 1: Remove internal duplicates within this batch
            seen_urls = set()
            deduplicated_listings = []
            internal_duplicates = 0
            
            for listing in listings:
                url = listing.get('listing_url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    deduplicated_listings.append(listing)
                elif url:
                    internal_duplicates += 1
            
            if internal_duplicates > 0:
                print(f"🔍 Removed {internal_duplicates} internal duplicates from batch")
            
            # STEP 2: Check against database for existing listings
            # Process in smaller chunks to avoid 414 Request-URI Too Large error
            chunk_size = 10
            new_listings = []
            
            for i in range(0, len(deduplicated_listings), chunk_size):
                chunk = deduplicated_listings[i:i + chunk_size]
                chunk_urls = [listing['listing_url'] for listing in chunk if listing.get('listing_url')]
                
                if chunk_urls:
                    result = self.supabase.table("ebay_sold_listings").select("listing_url").in_("listing_url", chunk_urls).execute()
                    existing_urls = set(row['listing_url'] for row in result.data) if result.data else set()
                    
                    for listing in chunk:
                        if listing.get('listing_url') not in existing_urls:
                            new_listings.append(listing)
                else:
                    new_listings.extend(chunk)
            
            database_duplicates = len(deduplicated_listings) - len(new_listings)
            if database_duplicates > 0:
                print(f"🔍 Found {database_duplicates} existing listings in database")
            
            total_filtered = len(listings) - len(new_listings)
            if total_filtered > 0:
                print(f"📊 Total filtered: {total_filtered} duplicates ({internal_duplicates} internal + {database_duplicates} database)")
            
            return new_listings
            
        except Exception as e:
            print(f"⚠️ Error checking duplicates: {e}")
            # If duplicate check fails, return all listings (better than losing data)
            return listings
    
    def _filter_sealed_duplicates(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out sealed product listings that already exist in database AND remove internal duplicates"""
        if not listings:
            return []
        
        try:
            # STEP 1: Remove internal duplicates within this batch
            seen_urls = set()
            deduplicated_listings = []
            internal_duplicates = 0
            
            for listing in listings:
                url = listing.get('listing_url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    deduplicated_listings.append(listing)
                elif url:
                    internal_duplicates += 1
            
            if internal_duplicates > 0:
                print(f"🔍 Removed {internal_duplicates} internal duplicates from batch")
            
            # STEP 2: Check against sealed listings database for existing listings
            chunk_size = 10
            new_listings = []
            
            for i in range(0, len(deduplicated_listings), chunk_size):
                chunk = deduplicated_listings[i:i + chunk_size]
                chunk_urls = [listing['listing_url'] for listing in chunk if listing.get('listing_url')]
                
                if chunk_urls:
                    result = self.supabase.table("ebay_sealed_listings").select("listing_url").in_("listing_url", chunk_urls).execute()
                    existing_urls = set(row['listing_url'] for row in result.data) if result.data else set()
                    
                    for listing in chunk:
                        if listing.get('listing_url') not in existing_urls:
                            new_listings.append(listing)
                else:
                    new_listings.extend(chunk)
            
            database_duplicates = len(deduplicated_listings) - len(new_listings)
            if database_duplicates > 0:
                print(f"🔍 Found {database_duplicates} existing listings in database")
            
            total_filtered = len(listings) - len(new_listings)
            if total_filtered > 0:
                print(f"📊 Total filtered: {total_filtered} duplicates ({internal_duplicates} internal + {database_duplicates} database)")
            
            return new_listings
            
        except Exception as e:
            print(f"⚠️ Error checking sealed duplicates: {e}")
            # If duplicate check fails, return all listings (better than losing data)
            return listings
    
    def _batch_upload_listings(self, listings: List[Dict[str, Any]]) -> bool:
        """Upload listings in batches with error handling"""
        if not listings:
            return True
        
        total_batches = (len(listings) + self.batch_size - 1) // self.batch_size
        successful_uploads = 0
        
        for i in range(0, len(listings), self.batch_size):
            batch = listings[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            print(f"📦 Uploading batch {batch_num}/{total_batches} ({len(batch)} listings)...")
            
            try:
                result = self.supabase.table("ebay_sold_listings").insert(batch).execute()
                
                if result.data:
                    successful_uploads += len(batch)
                    print(f"✅ Batch {batch_num} uploaded successfully")
                else:
                    print(f"❌ Batch {batch_num} failed - no data returned")
                    
            except Exception as e:
                print(f"❌ Batch {batch_num} failed: {e}")
                # Continue with remaining batches
                continue
        
        success_rate = (successful_uploads / len(listings)) * 100
        print(f"📊 Upload complete: {successful_uploads}/{len(listings)} listings ({success_rate:.1f}% success rate)")
        
        return successful_uploads > 0
    
    def _batch_upload_sealed_listings(self, listings: List[Dict[str, Any]]) -> bool:
        """Upload sealed product listings in batches with error handling"""
        if not listings:
            return True
        
        total_batches = (len(listings) + self.batch_size - 1) // self.batch_size
        successful_uploads = 0
        
        for i in range(0, len(listings), self.batch_size):
            batch = listings[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            print(f"📦 Uploading batch {batch_num}/{total_batches} ({len(batch)} listings)...")
            
            try:
                result = self.supabase.table("ebay_sealed_listings").insert(batch).execute()
                
                if result.data:
                    successful_uploads += len(batch)
                    print(f"✅ Batch {batch_num} uploaded successfully")
                else:
                    print(f"❌ Batch {batch_num} failed - no data returned")
                    
            except Exception as e:
                print(f"❌ Batch {batch_num} failed: {e}")
                # Continue with remaining batches
                continue
        
        success_rate = (successful_uploads / len(listings)) * 100
        print(f"📊 Upload complete: {successful_uploads}/{len(listings)} listings ({success_rate:.1f}% success rate)")
        
        return successful_uploads > 0
    
    def get_card_listing_count(self, card_id: int) -> int:
        """Get count of existing listings for a specific card"""
        try:
            result = self.supabase.table("ebay_sold_listings").select("*", count="exact").eq("card_id", card_id).execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"⚠️ Could not get listing count for card {card_id}: {e}")
            return 0
    
    def get_sealed_product_listing_count(self, sealed_product_id: int) -> int:
        """Get count of existing listings for a specific sealed product"""
        try:
            result = self.supabase.table("ebay_sealed_listings").select("*", count="exact").eq("sealed_product_id", sealed_product_id).execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"⚠️ Could not get listing count for sealed product {sealed_product_id}: {e}")
            return 0
    
    def get_recent_listings_for_card(self, card_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent listings for a specific card"""
        try:
            result = self.supabase.table("ebay_sold_listings").select("*").eq("card_id", card_id).order("created_at", desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"⚠️ Could not get recent listings for card {card_id}: {e}")
            return []
    
    def create_market_summary_for_card(self, card_id: int) -> bool:
        """Create/update market summary for a specific card"""
        print(f"📊 Creating market summary for card_id {card_id}...")
        
        try:
            # Get all listings for this card
            result = self.supabase.table("ebay_sold_listings").select("price, sold_date, is_graded, grading_company, grade").eq("card_id", card_id).execute()
            
            if not result.data:
                print(f"⚠️ No listings found for card {card_id}")
                return False
            
            listings = result.data
            prices = [float(listing['price']) for listing in listings if listing.get('price', 0) > 0]
            
            if not prices:
                print(f"⚠️ No valid prices found for card {card_id}")
                return False
            
            # Calculate summary stats
            summary = {
                'card_id': card_id,
                'avg_price': sum(prices) / len(prices),
                'lowest_price': min(prices),
                'highest_price': max(prices),
                'total_sales': len(listings),
                'last_updated': datetime.now().isoformat()
            }
            
            # Separate stats for graded vs raw
            graded_prices = [float(l['price']) for l in listings if l.get('is_graded') and l.get('price', 0) > 0]
            raw_prices = [float(l['price']) for l in listings if not l.get('is_graded') and l.get('price', 0) > 0]
            
            if graded_prices:
                summary['avg_graded_price'] = sum(graded_prices) / len(graded_prices)
                summary['graded_sales_count'] = len(graded_prices)
            
            if raw_prices:
                summary['avg_raw_price'] = sum(raw_prices) / len(raw_prices)
                summary['raw_sales_count'] = len(raw_prices)
            
            # Upsert summary (insert or update)
            result = self.supabase.table("ebay_market_summary").upsert(summary).execute()
            
            if result.data:
                print(f"✅ Market summary updated for card {card_id}")
                return True
            else:
                print(f"❌ Failed to update market summary for card {card_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating market summary for card {card_id}: {e}")
            return False
    
    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get overall upload statistics"""
        try:
            # Total listings
            total_result = self.supabase.table("ebay_sold_listings").select("*", count="exact").execute()
            total_listings = len(total_result.data) if total_result.data else 0
            
            # Unique cards tracked
            cards_result = self.supabase.table("ebay_sold_listings").select("card_id").execute()
            unique_cards = len(set(row['card_id'] for row in cards_result.data)) if cards_result.data else 0
            
            # Recent uploads (last 24 hours)
            yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            recent_result = self.supabase.table("ebay_sold_listings").select("*", count="exact").gte("created_at", yesterday).execute()
            recent_uploads = len(recent_result.data) if recent_result.data else 0
            
            stats = {
                'total_listings': total_listings,
                'unique_cards_tracked': unique_cards,
                'recent_uploads_24h': recent_uploads,
                'avg_listings_per_card': total_listings / unique_cards if unique_cards > 0 else 0
            }
            
            return stats
            
        except Exception as e:
            print(f"⚠️ Error getting upload statistics: {e}")
            return {}
    
    def get_card_last_update(self, card_id: int) -> Optional[datetime]:
        """Get the last update timestamp for a specific card"""
        try:
            result = self.supabase.table("ebay_sold_listings").select("created_at").eq("card_id", card_id).order("created_at", desc=True).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                last_update_str = result.data[0]['created_at']
                return datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error getting last update for card {card_id}: {e}")
            return None
    
    def get_cards_needing_updates(self, days_threshold: int = 7, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get cards that need updates based on last scraping timestamp
        
        Args:
            days_threshold: Cards not updated in X days need updates
            limit: Maximum cards to return
        """
        try:
            # Get all cards with their last update times
            cutoff_date = datetime.now() - timedelta(days=days_threshold)
            
            # Query cards that either have no listings or haven't been updated recently
            query = self.supabase.table("pokemon_cards").select("id, card_name, set_name, number")
            
            if limit:
                query = query.limit(limit)
            
            all_cards_result = query.execute()
            
            if not all_cards_result.data:
                return []
            
            cards_needing_updates = []
            
            for card in all_cards_result.data:
                card_id = card['id']
                last_update = self.get_card_last_update(card_id)
                
                # Card needs update if:
                # 1. Never been scraped (last_update is None)
                # 2. Last update is older than threshold
                needs_update = (
                    last_update is None or 
                    last_update < cutoff_date
                )
                
                if needs_update:
                    card['last_update'] = last_update.isoformat() if last_update else None
                    card['days_since_update'] = (datetime.now() - last_update).days if last_update else None
                    cards_needing_updates.append(card)
            
            print(f"📅 Found {len(cards_needing_updates)} cards needing updates (>{days_threshold} days old)")
            return cards_needing_updates
            
        except Exception as e:
            print(f"❌ Error getting cards needing updates: {e}")
            return []
    
    def update_card_scrape_timestamp(self, card_id: int) -> bool:
        """Update the last scrape timestamp for a card (for tracking purposes)"""
        try:
            # This could be a separate tracking table, but for now we'll use the listing timestamps
            # The most recent listing created_at serves as the last scrape timestamp
            return True
            
        except Exception as e:
            print(f"⚠️ Error updating scrape timestamp for card {card_id}: {e}")
            return False
    
    def get_comprehensive_scraping_progress(self) -> Dict[str, Any]:
        """Get progress statistics for comprehensive scraping"""
        try:
            # Total cards in database
            total_cards_result = self.supabase.table("pokemon_cards").select("*", count="exact").execute()
            total_cards = len(total_cards_result.data) if total_cards_result.data else 0
            
            # Cards with at least one listing
            scraped_cards_result = self.supabase.table("ebay_sold_listings").select("card_id").execute()
            scraped_card_ids = set(row['card_id'] for row in scraped_cards_result.data) if scraped_cards_result.data else set()
            scraped_cards_count = len(scraped_card_ids)
            
            # Cards never scraped
            unscraped_cards_count = total_cards - scraped_cards_count
            
            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            recent_result = self.supabase.table("ebay_sold_listings").select("card_id").gte("created_at", week_ago).execute()
            recently_updated_cards = set(row['card_id'] for row in recent_result.data) if recent_result.data else set()
            
            progress = {
                'total_cards_in_db': total_cards,
                'cards_with_listings': scraped_cards_count,
                'cards_never_scraped': unscraped_cards_count,
                'completion_percentage': (scraped_cards_count / total_cards * 100) if total_cards > 0 else 0,
                'cards_updated_last_7_days': len(recently_updated_cards),
                'estimated_cards_remaining': unscraped_cards_count
            }
            
            return progress
            
        except Exception as e:
            print(f"❌ Error getting scraping progress: {e}")
            return {}
    
    def get_data_collection_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of data collection for reporting"""
        try:
            # Basic stats
            upload_stats = self.get_upload_statistics()
            progress_stats = self.get_comprehensive_scraping_progress()
            
            # Condition breakdown
            condition_result = self.supabase.table("ebay_sold_listings").select("condition_category").execute()
            conditions = [row['condition_category'] for row in condition_result.data] if condition_result.data else []
            
            condition_counts = {}
            for condition in conditions:
                condition_counts[condition] = condition_counts.get(condition, 0) + 1
            
            # Search strategy breakdown
            strategy_result = self.supabase.table("ebay_sold_listings").select("search_strategy").execute()
            strategies = [row['search_strategy'] for row in strategy_result.data] if strategy_result.data else []
            
            strategy_counts = {}
            for strategy in strategies:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            summary = {
                'collection_timestamp': datetime.now().isoformat(),
                'basic_stats': upload_stats,
                'progress_stats': progress_stats,
                'condition_breakdown': condition_counts,
                'search_strategy_breakdown': strategy_counts,
                'data_quality': {
                    'listings_with_prices': len([row for row in condition_result.data if row.get('price', 0) > 0]) if condition_result.data else 0,
                    'graded_listings': condition_counts.get('graded', 0),
                    'raw_listings': condition_counts.get('raw', 0)
                }
            }
            
            return summary
            
        except Exception as e:
            print(f"❌ Error getting data collection summary: {e}")
            return {} 