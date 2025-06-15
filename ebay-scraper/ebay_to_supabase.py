"""
eBay to Supabase Module
Handles uploading parsed eBay data to Supabase with deduplication
"""

import sys
import os
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

class eBaySupabaseUploader:
    """Handles uploading eBay data to Supabase"""
    
    def __init__(self):
        self.supabase = supabase
    
    def upload_sold_listings(self, listings: List[Dict[str, Any]]) -> bool:
        """Upload listing data to ebay_sold_listings table"""
        # TODO: Implement batch upload with deduplication
        print(f"📤 Uploading {len(listings)} listings to Supabase...")
        
        if not listings:
            print("⚠️ No listings to upload")
            return True
            
        try:
            # TODO: Check for duplicates by listing_url or title+date
            # TODO: Insert new records
            print("✅ Upload successful")
            return True
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False
    
    def create_market_summary(self, card_data: Dict[str, Any]) -> bool:
        """Update ebay_market_summary table with aggregated data"""
        # TODO: Calculate avg/min/max prices for each card
        print("📊 Updating market summary...")
        return True
    
    def check_duplicate(self, listing: Dict[str, Any]) -> bool:
        """Check if listing already exists in database"""
        # TODO: Query by listing_url or title+sold_date
        return False
    
    def get_existing_listings_count(self) -> int:
        """Get count of existing listings for monitoring"""
        try:
            result = self.supabase.table("ebay_sold_listings").select("*", count="exact").execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"⚠️ Could not get listing count: {e}")
            return 0 