#!/usr/bin/env python3
"""
Data Freshness Checker
Determines if we have up-to-date pricing data for Pokemon cards and sealed products
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

class DataFreshnessChecker:
    """Checks data freshness and determines if new data collection is needed"""
    
    def __init__(self, max_age_days: int = 7):
        """
        Initialize the freshness checker
        
        Args:
            max_age_days: Maximum age in days before data is considered stale
        """
        self.max_age_days = max_age_days
        self.supabase = supabase
        
    def check_product_freshness(self, product_name: str, product_type: str = None) -> Dict[str, Any]:
        """
        Check if we have fresh data for a product
        
        Args:
            product_name: Name of the product to check
            product_type: 'card' or 'sealed' (optional, will search both if not specified)
            
        Returns:
            Dict with freshness information and recommended actions
        """
        
        print(f"🔍 Checking data freshness for: {product_name}")
        
        # First, find the product in our tracking table
        product_info = self._find_product(product_name, product_type)
        
        if not product_info:
            return {
                'product_found': False,
                'is_fresh': False,
                'last_update': None,
                'days_old': float('inf'),
                'ebay_listing_count': 0,
                'pricecharting_available': False,
                'recommended_action': 'full_setup'  # Need to find and add product first
            }
        
        # Check freshness of existing data
        freshness_info = self._check_existing_data(product_info)
        
        print(f"   📊 Found product: {product_info['product_name']} ({product_info['product_type']})")
        print(f"   📅 Last update: {freshness_info['last_update']}")
        print(f"   🕐 Days old: {freshness_info['days_old']}")
        print(f"   📈 eBay listings: {freshness_info['ebay_listing_count']}")
        print(f"   💰 PriceCharting: {'Yes' if freshness_info['pricecharting_available'] else 'No'}")
        print(f"   🎯 Recommended action: {freshness_info['recommended_action']}")
        
        return freshness_info
    
    def _find_product(self, product_name: str, product_type: str = None) -> Optional[Dict]:
        """Find product in pokequant_products table"""
        
        try:
            query = self.supabase.table('pokequant_products').select('*')
            
            # Search by name (case insensitive)
            query = query.ilike('product_name', f'%{product_name}%')
            
            # Filter by type if specified
            if product_type:
                query = query.eq('product_type', product_type)
            
            result = query.execute()
            
            if result.data:
                # Return the first match (or could return all matches for user to choose)
                return result.data[0]
            else:
                # Product not found in tracking table, let's search the source tables
                return self._search_source_tables(product_name, product_type)
                
        except Exception as e:
            print(f"   ❌ Error searching for product: {e}")
            return None
    
    def _search_source_tables(self, product_name: str, product_type: str = None) -> Optional[Dict]:
        """Search for product in pokemon_cards or sealed_products tables"""
        
        found_products = []
        
        # Search cards table if not specifically looking for sealed products
        if product_type != 'sealed':
            try:
                card_result = self.supabase.table('pokemon_cards').select('*').ilike('card_name', f'%{product_name}%').limit(5).execute()
                
                for card in card_result.data:
                    found_products.append({
                        'product_type': 'card',
                        'product_id': str(card['id']),
                        'product_name': card['card_name'],
                        'set_name': card.get('set_name', ''),
                        'source_table': 'pokemon_cards'
                    })
            except Exception as e:
                print(f"   ⚠️ Error searching cards: {e}")
        
        # Search sealed products table if not specifically looking for cards
        if product_type != 'card':
            try:
                sealed_result = self.supabase.table('sealed_products').select('*').ilike('product_name', f'%{product_name}%').limit(5).execute()
                
                for product in sealed_result.data:
                    found_products.append({
                        'product_type': 'sealed',
                        'product_id': str(product['id']),
                        'product_name': product['product_name'],
                        'set_name': product.get('set_name', ''),
                        'source_table': 'sealed_products'
                    })
            except Exception as e:
                print(f"   ⚠️ Error searching sealed products: {e}")
        
        if found_products:
            # For now, return the first match
            # In a real implementation, you might want to show all options to the user
            product = found_products[0]
            print(f"   🔍 Found in {product['source_table']}: {product['product_name']}")
            return product
        
        return None
    
    def _check_existing_data(self, product_info: Dict) -> Dict[str, Any]:
        """Check the freshness of existing data for a product"""
        
        result = {
            'product_found': True,
            'product_info': product_info,
            'is_fresh': False,
            'last_update': None,
            'days_old': float('inf'),
            'ebay_listing_count': 0,
            'pricecharting_available': False,
            'recommended_action': 'scrape_both'
        }
        
        product_type = product_info['product_type']
        product_id = product_info['product_id']
        
        # Check eBay data freshness
        ebay_info = self._check_ebay_data(product_type, product_id)
        result.update(ebay_info)
        
        # Check PriceCharting data availability
        pc_info = self._check_pricecharting_data(product_type, product_id)
        result['pricecharting_available'] = pc_info['available']
        
        # Determine if data is fresh
        if result['days_old'] <= self.max_age_days:
            result['is_fresh'] = True
            result['recommended_action'] = 'use_cache'
        elif result['ebay_listing_count'] > 0 and result['days_old'] <= self.max_age_days * 2:
            result['recommended_action'] = 'scrape_pricecharting_only'
        else:
            result['recommended_action'] = 'scrape_both'
        
        return result
    
    def _check_ebay_data(self, product_type: str, product_id: str) -> Dict[str, Any]:
        """Check eBay data freshness for a product"""
        
        table_name = 'ebay_sold_listings' if product_type == 'card' else 'ebay_sealed_listings'
        id_column = 'card_id' if product_type == 'card' else 'sealed_product_id'
        
        try:
            # Count total listings
            count_result = self.supabase.table(table_name).select('id', count='exact').eq(id_column, product_id).execute()
            listing_count = count_result.count or 0
            
            # Get most recent listing
            recent_result = self.supabase.table(table_name).select('created_at').eq(id_column, product_id).order('created_at', desc=True).limit(1).execute()
            
            last_update = None
            days_old = float('inf')
            
            if recent_result.data:
                last_update_str = recent_result.data[0]['created_at']
                last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                days_old = (datetime.now(last_update.tzinfo) - last_update).days
            
            return {
                'last_update': last_update,
                'days_old': days_old,
                'ebay_listing_count': listing_count
            }
            
        except Exception as e:
            print(f"   ⚠️ Error checking eBay data: {e}")
            return {
                'last_update': None,
                'days_old': float('inf'),
                'ebay_listing_count': 0
            }
    
    def _check_pricecharting_data(self, product_type: str, product_id: str) -> Dict[str, Any]:
        """Check if PriceCharting data is available"""
        
        # For now, this is a placeholder
        # In the future, we could check if we have PriceCharting data stored
        # or check the product's attributes to see if it's a good PriceCharting candidate
        
        return {
            'available': False,  # Placeholder - will be implemented when PriceCharting integration is added
            'last_update': None
        }
    
    def get_stale_products(self, limit: int = 20) -> List[Dict]:
        """Get list of products with stale data that need updating"""
        
        print(f"🔍 Finding products with data older than {self.max_age_days} days...")
        
        try:
            # Find products that haven't been updated recently
            cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
            
            result = self.supabase.table('pokequant_products').select('*').filter('last_data_update', 'lt', cutoff_date.isoformat()).limit(limit).execute()
            
            print(f"   📊 Found {len(result.data)} products needing updates")
            
            return result.data
            
        except Exception as e:
            print(f"   ❌ Error finding stale products: {e}")
            return []
    
    def update_product_timestamp(self, product_type: str, product_id: str) -> bool:
        """Update the last_data_update timestamp for a product"""
        
        try:
            result = self.supabase.table('pokequant_products').update({
                'last_data_update': datetime.now().isoformat()
            }).eq('product_type', product_type).eq('product_id', product_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Error updating timestamp: {e}")
            return False

def main():
    """CLI interface for testing the freshness checker"""
    
    parser = argparse.ArgumentParser(description="Check data freshness for Pokemon products")
    parser.add_argument('product_name', nargs='?', help='Product name to check')
    parser.add_argument('--type', choices=['card', 'sealed'], help='Product type')
    parser.add_argument('--max-age', type=int, default=7, help='Maximum age in days before data is stale')
    parser.add_argument('--test', action='store_true', help='Run test mode with sample products')
    parser.add_argument('--stale', action='store_true', help='Show products with stale data')
    
    args = parser.parse_args()
    
    checker = DataFreshnessChecker(max_age_days=args.max_age)
    
    if args.test:
        print("🧪 Running freshness checker test mode...")
        
        test_products = [
            ("Charizard V", "card"),
            ("Evolving Skies Booster Box", "sealed"),
            ("Nonexistent Product", None)
        ]
        
        for product_name, product_type in test_products:
            print(f"\n{'='*50}")
            result = checker.check_product_freshness(product_name, product_type)
            print(f"Result: {result}")
        
    elif args.stale:
        print("📋 Finding products with stale data...")
        stale_products = checker.get_stale_products()
        
        if stale_products:
            print(f"\nFound {len(stale_products)} products needing updates:")
            for product in stale_products:
                print(f"   📦 {product['product_name']} ({product['product_type']}) - Last update: {product.get('last_data_update', 'Never')}")
        else:
            print("✅ No stale products found!")
    
    elif args.product_name:
        result = checker.check_product_freshness(args.product_name, args.type)
        print(f"\n📊 Freshness Check Result:")
        print(f"   Product Found: {result['product_found']}")
        print(f"   Data Fresh: {result['is_fresh']}")
        print(f"   Recommended Action: {result['recommended_action']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 