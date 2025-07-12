#!/usr/bin/env python3
"""
Investigate Outliers in PokeQuant Price Data
"""

import sys
import os
from typing import List, Dict, Any
import statistics

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase
from quant.price_data_service import PriceDataService

class OutlierInvestigator:
    """Investigate outliers in PokeQuant price data"""
    
    def __init__(self):
        self.supabase = supabase
        self.price_service = PriceDataService()
    
    def investigate_product(self, product_name: str) -> Dict[str, Any]:
        """Investigate outliers for a specific product"""
        
        print(f"🔍 Investigating outliers for: {product_name}")
        print("=" * 60)
        
        # Find the product
        product_info = self._find_product(product_name)
        if not product_info['found']:
            return {'error': f"Product '{product_name}' not found"}
        
        product = product_info['product']
        product_type = product['type']
        product_id = product['id']
        
        # Get the PokeQuant product ID
        pokequant_product_id = self.price_service.ensure_product_exists(
            product_type, product_id, product['name'], product.get('set_name')
        )
        
        # Get price series data
        price_data = self.price_service.get_price_series(pokequant_product_id)
        
        if not price_data['success']:
            return {'error': 'No price data found'}
        
        # Analyze outliers
        raw_data = price_data['raw_data']
        outlier_analysis = self._analyze_outliers(raw_data, product)
        
        # Get raw eBay listings for comparison
        ebay_analysis = self._analyze_raw_ebay_data(product_type, product_id, product['name'])
        
        return {
            'product': product,
            'pokequant_analysis': outlier_analysis,
            'ebay_analysis': ebay_analysis,
            'recommendations': self._generate_recommendations(outlier_analysis, ebay_analysis, product)
        }
    
    def _find_product(self, product_name: str) -> Dict[str, Any]:
        """Find product in database"""
        
        # Search in sealed_products first
        try:
            sealed_query = self.supabase.table('sealed_products').select('*').ilike('product_name', f'%{product_name}%').limit(5).execute()
            sealed_results = sealed_query.data
        except Exception as e:
            sealed_results = []
        
        # Search in pokemon_cards
        try:
            card_query = self.supabase.table('pokemon_cards').select('*').ilike('card_name', f'%{product_name}%').limit(5).execute()
            card_results = card_query.data
        except Exception as e:
            card_results = []
        
        all_results = []
        
        for product in sealed_results:
            all_results.append({
                'type': 'sealed',
                'id': str(product['id']),
                'name': product['product_name'],
                'set_name': product.get('set_name', ''),
                'display_name': product['product_name'],
                'raw_data': product
            })
        
        for card in card_results:
            all_results.append({
                'type': 'card',
                'id': str(card['id']),
                'name': card['card_name'],
                'set_name': card.get('set_name', ''),
                'display_name': f"{card['card_name']} - {card.get('set_name', 'Unknown Set')}",
                'raw_data': card
            })
        
        if all_results:
            return {'found': True, 'product': all_results[0]}
        else:
            return {'found': False, 'product': None}
    
    def _analyze_outliers(self, price_data: List[Dict], product: Dict) -> Dict[str, Any]:
        """Analyze outliers in PokeQuant price series data"""
        
        print(f"\n📊 Analyzing PokeQuant Price Series Data")
        print("-" * 40)
        
        # Group by source and condition
        source_groups = {}
        for point in price_data:
            source = point['source']
            condition = point['condition_category']
            price = point['price']
            
            key = f"{source}_{condition}"
            if key not in source_groups:
                source_groups[key] = []
            source_groups[key].append(point)
        
        outlier_summary = {
            'total_points': len(price_data),
            'source_breakdown': {},
            'outliers': [],
            'price_ranges': {}
        }
        
        all_prices = [p['price'] for p in price_data]
        outlier_summary['overall_stats'] = {
            'min': min(all_prices),
            'max': max(all_prices),
            'mean': round(statistics.mean(all_prices), 2),
            'median': round(statistics.median(all_prices), 2)
        }
        
        print(f"Total data points: {len(price_data)}")
        print(f"Overall price range: ${min(all_prices)} - ${max(all_prices)}")
        print(f"Mean: ${statistics.mean(all_prices):.2f}, Median: ${statistics.median(all_prices):.2f}")
        
        # Analyze each source/condition group
        for group_key, points in source_groups.items():
            if len(points) < 3:
                continue
                
            prices = [p['price'] for p in points]
            source, condition = group_key.split('_', 1)
            
            # Calculate IQR outliers
            q1 = statistics.quantiles(prices, n=4)[0]
            q3 = statistics.quantiles(prices, n=4)[2]
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            group_outliers = []
            for point in points:
                price = point['price']
                if price < lower_bound or price > upper_bound:
                    outlier_type = 'extreme' if price < q1 - 3 * iqr or price > q3 + 3 * iqr else 'moderate'
                    group_outliers.append({
                        'price': price,
                        'date': point['price_date'],
                        'type': outlier_type,
                        'expected_range': f"${lower_bound:.2f} - ${upper_bound:.2f}"
                    })
            
            outlier_summary['source_breakdown'][group_key] = {
                'count': len(points),
                'price_range': f"${min(prices):.2f} - ${max(prices):.2f}",
                'median': f"${statistics.median(prices):.2f}",
                'outliers': len(group_outliers),
                'outlier_details': group_outliers
            }
            
            print(f"\n{source.upper()} ({condition}):")
            print(f"  Count: {len(points)}")
            print(f"  Range: ${min(prices):.2f} - ${max(prices):.2f}")
            print(f"  Median: ${statistics.median(prices):.2f}")
            print(f"  Outliers: {len(group_outliers)}")
            
            for outlier in group_outliers[:3]:  # Show first 3
                print(f"    - ${outlier['price']} on {outlier['date']} ({outlier['type']})")
        
        return outlier_summary
    
    def _analyze_raw_ebay_data(self, product_type: str, product_id: str, product_name: str) -> Dict[str, Any]:
        """Analyze raw eBay data for comparison"""
        
        print(f"\n📊 Analyzing Raw eBay Data")
        print("-" * 40)
        
        try:
            if product_type == 'sealed':
                table = 'ebay_sealed_listings'
                id_field = 'sealed_product_id'
            else:
                table = 'ebay_sold_listings'
                id_field = 'card_id'
            
            result = self.supabase.table(table).select('*').eq(id_field, int(product_id)).execute()
            
            if not result.data:
                return {'error': 'No raw eBay data found'}
            
            listings = result.data
            prices = [float(listing['price']) for listing in listings if listing.get('price') and float(listing['price']) > 0]
            
            if not prices:
                return {'error': 'No valid prices found'}
            
            # Find suspicious listings
            suspicious = []
            
            for listing in listings:
                price = float(listing.get('price', 0))
                title = listing.get('title', '')
                
                # Check for suspiciously low prices for sealed products
                if product_type == 'sealed' and 'booster box' in product_name.lower():
                    if price < 50:  # Booster boxes shouldn't be under $50
                        suspicious.append({
                            'price': price,
                            'title': title,
                            'reason': 'Suspiciously low for booster box',
                            'url': listing.get('listing_url', '')
                        })
                
                # Check for empty box indicators
                empty_indicators = ['empty', 'box only', 'just box', 'no cards', 'no packs']
                if any(indicator in title.lower() for indicator in empty_indicators):
                    suspicious.append({
                        'price': price,
                        'title': title,
                        'reason': 'Likely empty box',
                        'url': listing.get('listing_url', '')
                    })
                
                # Check for damaged/opened indicators
                damage_indicators = ['damaged', 'torn', 'opened', 'resealed', 'missing']
                if any(indicator in title.lower() for indicator in damage_indicators):
                    suspicious.append({
                        'price': price,
                        'title': title,
                        'reason': 'Likely damaged/opened',
                        'url': listing.get('listing_url', '')
                    })
            
            analysis = {
                'total_listings': len(listings),
                'total_prices': len(prices),
                'price_range': f"${min(prices):.2f} - ${max(prices):.2f}",
                'median': f"${statistics.median(prices):.2f}",
                'suspicious_count': len(suspicious),
                'suspicious_listings': suspicious[:10]  # Show first 10
            }
            
            print(f"Total listings: {len(listings)}")
            print(f"Valid prices: {len(prices)}")
            print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
            print(f"Suspicious listings: {len(suspicious)}")
            
            for i, sus in enumerate(suspicious[:5], 1):
                print(f"  {i}. ${sus['price']} - {sus['reason']}")
                print(f"     Title: {sus['title'][:80]}...")
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_recommendations(self, pokequant_analysis: Dict, ebay_analysis: Dict, product: Dict) -> List[str]:
        """Generate recommendations for outlier handling"""
        
        recommendations = []
        
        # Product-specific filters
        if product['type'] == 'sealed' and 'booster box' in product['name'].lower():
            recommendations.append("Add minimum price filter: Booster boxes should be at least $50")
            recommendations.append("Filter titles containing: 'empty', 'box only', 'just box', 'no cards'")
            recommendations.append("Filter damaged indicators: 'damaged', 'torn', 'opened', 'resealed'")
        
        # General recommendations
        if ebay_analysis.get('suspicious_count', 0) > 10:
            recommendations.append("High number of suspicious listings detected - implement stricter filtering")
        
        total_outliers = sum(group.get('outliers', 0) for group in pokequant_analysis.get('source_breakdown', {}).values())
        if total_outliers > 5:
            recommendations.append("Consider more aggressive IQR-based outlier removal")
        
        # Price-specific recommendations
        overall_stats = pokequant_analysis.get('overall_stats', {})
        if overall_stats.get('min', 0) < 10:
            recommendations.append("Implement minimum price threshold based on product type")
        
        return recommendations

def main():
    """Main function"""
    
    if len(sys.argv) != 2:
        print("Usage: python investigate_outliers.py 'Product Name'")
        return
    
    product_name = sys.argv[1]
    
    investigator = OutlierInvestigator()
    result = investigator.investigate_product(product_name)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print("-" * 40)
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"{i}. {rec}")

if __name__ == "__main__":
    main() 