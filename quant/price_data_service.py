#!/usr/bin/env python3
"""
Price Data Aggregation Service
Handles storage and retrieval of price data from multiple sources in PokeQuant format
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from statistics import median, mean

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

class PriceDataService:
    """Service for aggregating and storing price data from multiple sources"""
    
    def __init__(self):
        self.supabase = supabase
        
        # Initialize filtering capabilities
        try:
            from quant.enhanced_outlier_filter import apply_enhanced_filtering
            from quant.llm_enhanced_filter import apply_llm_enhanced_filtering
            self.enhanced_filtering_available = True
            self.llm_filtering_available = True
        except ImportError:
            from quant.enhanced_outlier_filter import apply_enhanced_filtering
            self.enhanced_filtering_available = True
            self.llm_filtering_available = False
        
    def ensure_product_exists(self, product_type: str, product_id: str, product_name: str, set_name: str = None) -> str:
        """Ensure product exists in pokequant_products table and return its UUID"""
        
        try:
            # Check if product already exists
            existing_result = self.supabase.table('pokequant_products').select('id').eq('product_type', product_type).eq('product_id', product_id).execute()
            
            if existing_result.data:
                return existing_result.data[0]['id']
            
            # Create new product entry
            new_product = {
                'product_type': product_type,
                'product_id': product_id,
                'product_name': product_name,
                'set_name': set_name,
                'last_data_update': datetime.now().isoformat(),
                'data_quality_score': 0.5  # Initial score, will be updated
            }
            
            result = self.supabase.table('pokequant_products').insert(new_product).execute()
            
            if result.data:
                print(f"   ✅ Created PokeQuant product entry: {product_name}")
                return result.data[0]['id']
            else:
                raise Exception("Failed to create product entry")
                
        except Exception as e:
            print(f"   ❌ Error ensuring product exists: {e}")
            return None
    
    def aggregate_ebay_data(self, product_type: str, product_id: str, product_name: str, set_name: str = None) -> Dict[str, Any]:
        """Aggregate eBay data into pokequant_price_series"""
        
        print(f"   📈 Aggregating eBay data for {product_name}...")
        
        try:
            # Ensure product exists in pokequant_products
            pokequant_product_id = self.ensure_product_exists(product_type, product_id, product_name, set_name)
            if not pokequant_product_id:
                return {'success': False, 'error': 'Failed to create product entry'}
            
            # Load raw eBay data
            table_name = 'ebay_sold_listings' if product_type == 'card' else 'ebay_sealed_listings'
            id_column = 'card_id' if product_type == 'card' else 'sealed_product_id'
            
            ebay_result = self.supabase.table(table_name).select('*').eq(id_column, product_id).execute()
            
            if not ebay_result.data:
                return {'success': False, 'error': 'No eBay data found'}
            
            # Apply data quality filtering before aggregation
            product_info = {
                'name': product_name,
                'type': product_type,
                'set_name': set_name
            }
            
            # Fix: Apply filtering to raw listings before aggregation
            filtered_listings = self._apply_data_quality_filtering(ebay_result.data, product_info)
            
            # Group by date and aggregate prices
            aggregated_data = self._aggregate_prices_by_date(filtered_listings, 'ebay')
            
            # Store in pokequant_price_series
            stored_count = self._store_price_series(pokequant_product_id, aggregated_data, 'ebay')
            
            # Update product timestamp
            self._update_product_timestamp(pokequant_product_id)
            
            return {
                'success': True,
                'raw_listings': len(ebay_result.data),
                'filtered_listings': len(filtered_listings),
                'removed_listings': len(ebay_result.data) - len(filtered_listings),
                'aggregated_points': len(aggregated_data),
                'stored_points': stored_count,
                'pokequant_product_id': pokequant_product_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def aggregate_pricecharting_data(self, product_type: str, product_id: str, product_name: str, 
                                   pricecharting_data: Dict[str, Any], set_name: str = None) -> Dict[str, Any]:
        """Aggregate PriceCharting data into pokequant_price_series"""
        
        print(f"   💰 Aggregating PriceCharting data for {product_name}...")
        
        try:
            # Ensure product exists in pokequant_products
            pokequant_product_id = self.ensure_product_exists(product_type, product_id, product_name, set_name)
            if not pokequant_product_id:
                return {'success': False, 'error': 'Failed to create product entry'}
            
            # Extract historical data from PriceCharting response
            aggregated_data = self._process_pricecharting_data(pricecharting_data)
            
            if not aggregated_data:
                return {'success': False, 'error': 'No valid PriceCharting data found'}
            
            # Store in pokequant_price_series
            stored_count = self._store_price_series(pokequant_product_id, aggregated_data, 'pricecharting')
            
            # Update product timestamp
            self._update_product_timestamp(pokequant_product_id)
            
            return {
                'success': True,
                'aggregated_points': len(aggregated_data),
                'stored_points': stored_count,
                'pokequant_product_id': pokequant_product_id
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _aggregate_prices_by_date(self, listings: List[Dict], source: str) -> List[Dict]:
        """Aggregate multiple listings into daily price points"""
        
        # Group listings by date
        date_groups = {}
        
        for listing in listings:
            # Get the date (prefer sold_date, fallback to created_at)
            date_str = listing.get('sold_date') or listing.get('created_at')
            if not date_str:
                continue
                
            # Extract date part (YYYY-MM-DD)
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_key = date_obj.date().isoformat()
            except:
                continue
            
            # Get price
            try:
                price = float(listing.get('price', 0))
                if price <= 0:
                    continue
            except:
                continue
            
            # Determine condition category
            condition_category = self._determine_condition_category(listing)
            
            # Group key includes condition for separate aggregation
            group_key = f"{date_key}_{condition_category}"
            
            if group_key not in date_groups:
                date_groups[group_key] = {
                    'date': date_key,
                    'condition_category': condition_category,
                    'prices': [],
                    'listings': []
                }
            
            date_groups[group_key]['prices'].append(price)
            date_groups[group_key]['listings'].append(listing)
        
        # Aggregate each date group
        aggregated = []
        for group_data in date_groups.values():
            prices = group_data['prices']
            listings = group_data['listings']
            
            if not prices:
                continue
            
            # Calculate aggregated price (median to reduce outlier impact)
            aggregated_price = median(prices)
            data_confidence = min(1.0, len(prices) / 10)  # Higher confidence with more data points
            
            # Include sample titles for filtering (take a few representative titles)
            sample_titles = [listing.get('title', '') for listing in listings[:3] if listing.get('title')]
            
            aggregated.append({
                'price_date': group_data['date'],
                'price': round(aggregated_price, 2),
                'condition_category': group_data['condition_category'],
                'data_confidence': round(data_confidence, 2),
                'listing_count': len(prices),
                'sample_titles': sample_titles  # Add titles for filtering
            })
        
        return aggregated
    
    def _determine_condition_category(self, listing: Dict) -> str:
        """Determine condition category from listing data"""
        
        if listing.get('is_graded'):
            return 'graded'
        elif listing.get('condition_category') == 'sealed':
            return 'sealed'
        else:
            return 'raw'
    
    def _process_pricecharting_data(self, pc_data: Dict[str, Any]) -> List[Dict]:
        """Process PriceCharting data into our format"""
        
        aggregated = []
        
        # Extract historical data from PriceCharting response
        historical_data = pc_data.get('historical_chart_data', [])
        
        for data_point in historical_data:
            try:
                price_date = data_point.get('date')
                price = float(data_point.get('price', 0))
                
                if price_date and price > 0:
                    aggregated.append({
                        'price_date': price_date,
                        'price': round(price, 2),
                        'condition_category': 'market',  # PriceCharting market price
                        'data_confidence': 0.8,  # PriceCharting is generally reliable
                        'listing_count': 1
                    })
            except:
                continue
        
        # Also add current prices if available
        current_prices = pc_data.get('current_prices', {})
        today = datetime.now().date().isoformat()
        
        for condition, price in current_prices.items():
            try:
                price_val = float(price)
                if price_val > 0:
                    aggregated.append({
                        'price_date': today,
                        'price': round(price_val, 2),
                        'condition_category': condition,  # 'loose', 'graded', 'new', etc.
                        'data_confidence': 0.9,
                        'listing_count': 1
                    })
            except:
                continue
        
        return aggregated
    
    def _store_price_series(self, pokequant_product_id: str, price_data: List[Dict], source: str) -> int:
        """Store aggregated price data in pokequant_price_series table"""
        
        if not price_data:
            return 0
        
        stored_count = 0
        
        for data_point in price_data:
            try:
                price_entry = {
                    'pokequant_product_id': pokequant_product_id,
                    'price_date': data_point['price_date'],
                    'price': data_point['price'],
                    'source': source,
                    'condition_category': data_point['condition_category'],
                    'data_confidence': data_point['data_confidence'],
                    'listing_count': data_point['listing_count']
                }
                
                # Use upsert to handle duplicates
                result = self.supabase.table('pokequant_price_series').upsert(price_entry).execute()
                
                if result.data:
                    stored_count += 1
                    
            except Exception as e:
                print(f"   ⚠️ Failed to store price point: {e}")
                continue
        
        print(f"   ✅ Stored {stored_count}/{len(price_data)} price points in pokequant_price_series")
        return stored_count
    
    def _apply_data_quality_filtering(self, listings: List[Dict], product_info: Dict) -> List[Dict]:
        """Apply data quality filtering before storing data"""
        
        if not listings:
            return listings
        
        print(f"   🧹 Applying data quality filtering to {len(listings)} listings...")
        
        # Convert database format to filtering format
        price_data = []
        for listing in listings:
            # Map database fields to filtering format
            price_point = {
                'price': float(listing.get('price', 0)),
                'source': 'ebay',  # Since this is eBay data aggregation
                'title': listing.get('title', ''),
                'condition_category': listing.get('condition_category', 'unknown'),
                'original_data': listing  # Keep original for later reconstruction
            }
            price_data.append(price_point)
        
        # Apply enhanced filtering
        try:
            from quant.enhanced_outlier_filter import apply_enhanced_filtering
            clean_data = apply_enhanced_filtering(
                price_data, 
                product_info, 
                verbose=False
            )
            
            # Convert back to original format
            clean_listings = []
            for clean_point in clean_data:
                if 'original_data' in clean_point:
                    clean_listings.append(clean_point['original_data'])
                else:
                    # Fallback: reconstruct from filtered data
                    clean_listings.append({
                        'price': clean_point['price'],
                        'title': clean_point.get('title', ''),
                        'condition_category': clean_point.get('condition_category', 'unknown'),
                        'sold_date': clean_point.get('sold_date', ''),
                        'created_at': clean_point.get('created_at', '')
                    })
            
            removed_count = len(listings) - len(clean_listings)
            
            if removed_count > 0:
                print(f"   🚫 Enhanced filtering removed {removed_count} suspicious listings")
            
            # Optionally apply LLM filtering if enabled
            use_llm = (self.llm_filtering_available and 
                      os.getenv('GEMINI_API_KEY') and 
                      os.getenv('POKEQUANT_USE_LLM', 'false').lower() == 'true')
            
            if use_llm:
                try:
                    from quant.llm_enhanced_filter import apply_llm_enhanced_filtering
                    print(f"   🤖 Applying LLM filtering to {len(clean_listings)} listings...")
                    
                    # Convert to LLM format (needs sample_titles)
                    llm_data = []
                    for listing in clean_listings:
                        llm_point = listing.copy()
                        llm_point['sample_titles'] = [listing.get('title', 'Unknown')]
                        llm_data.append(llm_point)
                    
                    llm_result = apply_llm_enhanced_filtering(
                        llm_data,
                        product_info,
                        verbose=False
                    )
                    
                    final_listings = llm_result['filtered_data']
                    llm_removed = len(clean_listings) - len(final_listings)
                    
                    if llm_removed > 0:
                        print(f"   🧠 LLM filtering removed {llm_removed} additional problematic listings")
                    
                    clean_listings = final_listings
                    
                except Exception as e:
                    print(f"   ⚠️ LLM filtering failed, using enhanced filtering only: {e}")
            
            total_removed = len(listings) - len(clean_listings)
            if total_removed > 0:
                print(f"   ✅ Data quality filtering: {len(clean_listings)} kept, {total_removed} removed ({total_removed/len(listings)*100:.1f}%)")
            
            return clean_listings
            
        except Exception as e:
            print(f"   ⚠️ Filtering failed, using unfiltered data: {e}")
            return listings
    
    def _update_product_timestamp(self, pokequant_product_id: str):
        """Update the last_data_update timestamp for a product"""
        
        try:
            self.supabase.table('pokequant_products').update({
                'last_data_update': datetime.now().isoformat()
            }).eq('id', pokequant_product_id).execute()
        except Exception as e:
            print(f"   ⚠️ Failed to update product timestamp: {e}")
    
    def get_price_series(self, pokequant_product_id: str, days_back: int = None) -> Dict[str, Any]:
        """Retrieve price series data for analysis"""
        
        try:
            query = self.supabase.table('pokequant_price_series').select('*').eq('pokequant_product_id', pokequant_product_id).order('price_date')
            
            if days_back:
                cutoff_date = (datetime.now() - timedelta(days=days_back)).date().isoformat()
                query = query.gte('price_date', cutoff_date)
            
            result = query.execute()
            
            if not result.data:
                return {'success': False, 'error': 'No price data found'}
            
            # Organize data by source and condition
            organized_data = {
                'ebay': {'raw': [], 'graded': [], 'sealed': []},
                'pricecharting': {'market': [], 'loose': [], 'graded': [], 'new': []}
            }
            
            all_prices = []
            all_dates = []
            
            for price_point in result.data:
                source = price_point['source']
                condition = price_point['condition_category']
                
                price_data = {
                    'date': price_point['price_date'],
                    'price': price_point['price'],
                    'confidence': price_point['data_confidence'],
                    'listing_count': price_point['listing_count']
                }
                
                if source in organized_data and condition in organized_data[source]:
                    organized_data[source][condition].append(price_data)
                
                all_prices.append(price_point['price'])
                all_dates.append(price_point['price_date'])
            
            # Calculate summary statistics
            summary = {
                'total_data_points': len(result.data),
                'date_range': {'start': min(all_dates), 'end': max(all_dates)} if all_dates else None,
                'price_range': {'min': min(all_prices), 'max': max(all_prices)} if all_prices else None,
                'average_price': mean(all_prices) if all_prices else 0,
                'sources': list(set(point['source'] for point in result.data))
            }
            
            return {
                'success': True,
                'organized_data': organized_data,
                'raw_data': result.data,
                'summary': summary
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_data_quality_score(self, pokequant_product_id: str) -> float:
        """Calculate data quality score for a product"""
        
        try:
            price_data = self.get_price_series(pokequant_product_id)
            
            if not price_data['success']:
                return 0.0
            
            total_points = price_data['summary']['total_data_points']
            sources = price_data['summary']['sources']
            date_range_days = self._calculate_date_range_days(price_data['summary']['date_range'])
            
            # Quality scoring factors
            score = 0.0
            
            # Data volume (0-40 points)
            if total_points >= 100:
                score += 40
            elif total_points >= 50:
                score += 30
            elif total_points >= 20:
                score += 20
            elif total_points >= 10:
                score += 10
            
            # Multiple sources (0-30 points)
            if len(sources) >= 2:
                score += 30
            elif len(sources) == 1:
                score += 15
            
            # Time coverage (0-30 points)
            if date_range_days >= 365:
                score += 30
            elif date_range_days >= 180:
                score += 20
            elif date_range_days >= 90:
                score += 15
            elif date_range_days >= 30:
                score += 10
            
            return min(1.0, score / 100)
            
        except Exception as e:
            print(f"   ⚠️ Error calculating data quality: {e}")
            return 0.0
    
    def _calculate_date_range_days(self, date_range: Dict) -> int:
        """Calculate days between start and end dates"""
        
        if not date_range or not date_range['start'] or not date_range['end']:
            return 0
        
        try:
            start_date = datetime.fromisoformat(date_range['start']).date()
            end_date = datetime.fromisoformat(date_range['end']).date()
            return (end_date - start_date).days
        except:
            return 0 