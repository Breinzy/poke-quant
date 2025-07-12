#!/usr/bin/env python3
"""
Enhanced Outlier Filter for PokeQuant Price Data
Provides product-specific filtering and outlier removal
"""

import re
import statistics
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

class EnhancedOutlierFilter:
    """Enhanced outlier filtering with product-specific logic"""
    
    def __init__(self):
        # Product-specific price thresholds
        self.price_thresholds = {
            'booster_box': {'min': 50, 'max': 1000},
            'booster_box_inclusive': {'min': 25, 'max': 1000},  # Include ETBs (25-200) + Booster Boxes (50-1000)
            'elite_trainer_box': {'min': 25, 'max': 200},
            'theme_deck': {'min': 8, 'max': 50},
            'single_pack': {'min': 2, 'max': 25},
            'tin': {'min': 10, 'max': 100},
            'collection_box': {'min': 15, 'max': 300},
            'card': {'min': 0.25, 'max': 10000}
        }
        
        # Suspicious title patterns for different product types
        self.suspicious_patterns = {
            'booster_box': [
                r'\bpack\b(?!\s*(?:box|s?\s*(?:36|24)\b))',  # Single pack mentions (but not "pack box" or "36 packs")
                r'\bblister\b',         # Blister packs
                r'\b(?:1|2|3|4|5|6|7|8|9|10|11|12)\s*pack[s]?\b',  # Small pack counts (1-12 packs)
                r'\bsingle\b',          # Single items
                r'\bempty\b',           # Empty boxes
                r'\bbox\s+only\b',      # Box only
                r'\bno\s+cards?\b',     # No cards
                r'\bno\s+packs?\b',     # No packs
                r'\bjust\s+box\b',      # Just the box
                r'\bdamaged\b',         # Damaged
                r'\btorn\b',            # Torn
                r'\bopened\b',          # Opened
                r'\bresealed\b',        # Resealed
                r'\bmissing\b',         # Missing items
            ],
            'booster_box_inclusive': [
                # More lenient - only filter obvious junk, allow ETBs and booster boxes
                r'\bblister\b',         # Blister packs
                r'\b(?:1|2|3|4|5|6)\s*pack[s]?\b',  # Very small pack counts only (1-6 packs)
                r'\bsingle\b',          # Single items
                r'\bempty\b',           # Empty boxes
                r'\bbox\s+only\b',      # Box only
                r'\bno\s+cards?\b',     # No cards
                r'\bno\s+packs?\b',     # No packs
                r'\bjust\s+box\b',      # Just the box
                r'\bdamaged\b',         # Damaged
                r'\btorn\b',            # Torn
                r'\bopened\b',          # Opened
                r'\bresealed\b',        # Resealed
                r'\bmissing\b',         # Missing items
            ],
            'card': [
                r'\bempty\b',
                r'\bdamaged\b',
                r'\btorn\b',
                r'\bproxy\b',
                r'\bfake\b',
                r'\bcustom\b'
            ]
        }
        
        # Title keywords that should be present for specific products
        self.required_keywords = {
            'booster_box': ['box', 'booster'],  # Must contain both
            'booster_box_inclusive': [],  # No strict requirements - be more inclusive
            'elite_trainer_box': ['elite', 'trainer', 'box'],
            'theme_deck': ['theme', 'deck']
        }
    
    def filter_price_data(self, price_data: List[Dict], product_info: Dict) -> Dict[str, Any]:
        """Filter price data removing outliers and suspicious entries"""
        
        product_type = self._determine_product_type(product_info)
        
        print(f"🔍 Filtering price data for {product_type}")
        print(f"   Original data points: {len(price_data)}")
        
        # Step 1: Apply product-specific filters
        filtered_data = []
        removed_suspicious = []
        
        for point in price_data:
            price = point.get('price', 0)
            source = point.get('source', '')
            
            # Apply price thresholds
            thresholds = self.price_thresholds.get(product_type, self.price_thresholds['card'])
            if price < thresholds['min'] or price > thresholds['max']:
                removed_suspicious.append({
                    'point': point,
                    'reason': f"Price ${price} outside valid range ${thresholds['min']}-${thresholds['max']}"
                })
                continue
            
            # For eBay data, we can check additional factors
            if source == 'ebay' and 'title' in point:
                if self._is_suspicious_title(point['title'], product_type):
                    removed_suspicious.append({
                        'point': point,
                        'reason': "Suspicious title pattern detected"
                    })
                    continue
            
            filtered_data.append(point)
        
        # Step 2: Apply statistical outlier removal
        if len(filtered_data) >= 5:  # Need minimum data for statistical analysis
            statistically_filtered, removed_statistical = self._remove_statistical_outliers(filtered_data)
        else:
            statistically_filtered = filtered_data
            removed_statistical = []
        
        print(f"   After filtering: {len(statistically_filtered)} data points")
        print(f"   Removed suspicious: {len(removed_suspicious)}")
        print(f"   Removed statistical outliers: {len(removed_statistical)}")
        
        return {
            'filtered_data': statistically_filtered,
            'original_count': len(price_data),
            'final_count': len(statistically_filtered),
            'removed_suspicious': removed_suspicious,
            'removed_statistical': removed_statistical,
            'filter_summary': self._generate_filter_summary(removed_suspicious, removed_statistical)
        }
    
    def _determine_product_type(self, product_info: Dict) -> str:
        """Determine the specific product type for filtering"""
        
        product_name = product_info.get('name', '').lower()
        
        if 'booster box' in product_name:
            return 'booster_box_inclusive'  # Use inclusive mode for booster box searches
        elif 'elite trainer box' in product_name or 'etb' in product_name:
            return 'elite_trainer_box'
        elif 'theme deck' in product_name:
            return 'theme_deck'
        elif 'tin' in product_name:
            return 'tin'
        elif 'collection' in product_name:
            return 'collection_box'
        elif product_info.get('type') == 'card':
            return 'card'
        else:
            return 'booster_box_inclusive'  # Default to inclusive for sealed products
    
    def _is_suspicious_title(self, title: str, product_type: str) -> bool:
        """Check if a title contains suspicious patterns for the product type"""
        
        title_lower = title.lower()
        
        # Check for suspicious patterns
        suspicious_patterns = self.suspicious_patterns.get(product_type, [])
        for pattern in suspicious_patterns:
            if re.search(pattern, title_lower):
                return True
        
        # Check for required keywords (for sealed products)
        required_keywords = self.required_keywords.get(product_type, [])
        if required_keywords:
            # For booster boxes, we need 'booster box' OR ('box' AND 'booster') OR ('36' AND 'pack') 
            if product_type == 'booster_box':
                has_booster_box = 'booster box' in title_lower
                has_box_and_booster = ('box' in title_lower and 'booster' in title_lower)
                has_standard_count = ('36' in title_lower and 'pack' in title_lower) or ('24' in title_lower and 'pack' in title_lower)
                
                if not (has_booster_box or has_box_and_booster or has_standard_count):
                    return True
            elif product_type == 'booster_box_inclusive':
                # For inclusive mode, no strict keyword requirements
                # Just rely on suspicious pattern filtering
                pass
            else:
                # For other products, need all keywords
                if not all(keyword in title_lower for keyword in required_keywords):
                    return True
        
        return False
    
    def _remove_statistical_outliers(self, data: List[Dict], iqr_multiplier: float = 1.5) -> Tuple[List[Dict], List[Dict]]:
        """Remove statistical outliers using IQR method"""
        
        if len(data) < 5:
            return data, []
        
        # Group by source and condition for separate outlier detection
        groups = {}
        for point in data:
            source = point.get('source', 'unknown')
            condition = point.get('condition_category', 'unknown')
            key = f"{source}_{condition}"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(point)
        
        filtered_data = []
        removed_outliers = []
        
        for group_key, group_data in groups.items():
            if len(group_data) < 3:  # Not enough data for outlier detection
                filtered_data.extend(group_data)
                continue
            
            prices = [p['price'] for p in group_data]
            
            # Calculate IQR
            q1 = statistics.quantiles(prices, n=4)[0]
            q3 = statistics.quantiles(prices, n=4)[2]
            iqr = q3 - q1
            
            lower_bound = q1 - iqr_multiplier * iqr
            upper_bound = q3 + iqr_multiplier * iqr
            
            # Filter outliers
            for point in group_data:
                price = point['price']
                if lower_bound <= price <= upper_bound:
                    filtered_data.append(point)
                else:
                    outlier_type = 'extreme_low' if price < lower_bound else 'extreme_high'
                    removed_outliers.append({
                        'point': point,
                        'reason': f"Statistical outlier ({outlier_type}): ${price} outside ${lower_bound:.2f}-${upper_bound:.2f}",
                        'group': group_key
                    })
        
        return filtered_data, removed_outliers
    
    def _generate_filter_summary(self, removed_suspicious: List[Dict], removed_statistical: List[Dict]) -> Dict[str, Any]:
        """Generate a summary of filtering results"""
        
        summary = {
            'total_removed': len(removed_suspicious) + len(removed_statistical),
            'suspicious_removal_reasons': {},
            'statistical_outlier_groups': {},
            'price_ranges_removed': {'suspicious': [], 'statistical': []}
        }
        
        # Analyze suspicious removals
        for item in removed_suspicious:
            reason = item['reason']
            if 'outside valid range' in reason:
                summary['suspicious_removal_reasons']['price_threshold'] = summary['suspicious_removal_reasons'].get('price_threshold', 0) + 1
            elif 'Suspicious title' in reason:
                summary['suspicious_removal_reasons']['title_pattern'] = summary['suspicious_removal_reasons'].get('title_pattern', 0) + 1
            
            price = item['point'].get('price', 0)
            summary['price_ranges_removed']['suspicious'].append(price)
        
        # Analyze statistical removals
        for item in removed_statistical:
            group = item.get('group', 'unknown')
            summary['statistical_outlier_groups'][group] = summary['statistical_outlier_groups'].get(group, 0) + 1
            
            price = item['point'].get('price', 0)
            summary['price_ranges_removed']['statistical'].append(price)
        
        return summary
    
    def print_filter_report(self, filter_result: Dict[str, Any], product_info: Dict):
        """Print a detailed filter report"""
        
        print(f"\n📋 FILTER REPORT")
        print("=" * 50)
        
        product_name = product_info.get('name', 'Unknown')
        product_type = self._determine_product_type(product_info)
        
        print(f"Product: {product_name}")
        print(f"Type: {product_type}")
        print(f"Original data points: {filter_result['original_count']}")
        print(f"Filtered data points: {filter_result['final_count']}")
        print(f"Removal rate: {((filter_result['original_count'] - filter_result['final_count']) / filter_result['original_count'] * 100):.1f}%")
        
        # Suspicious removals
        if filter_result['removed_suspicious']:
            print(f"\n🚨 SUSPICIOUS REMOVALS ({len(filter_result['removed_suspicious'])}):")
            for i, item in enumerate(filter_result['removed_suspicious'][:5], 1):
                point = item['point']
                print(f"  {i}. ${point.get('price', 0)} - {item['reason']}")
                if 'title' in point:
                    print(f"     Title: {point['title'][:80]}...")
        
        # Statistical outliers
        if filter_result['removed_statistical']:
            print(f"\n📊 STATISTICAL OUTLIERS ({len(filter_result['removed_statistical'])}):")
            for i, item in enumerate(filter_result['removed_statistical'][:5], 1):
                point = item['point']
                print(f"  {i}. ${point.get('price', 0)} - {item['reason']}")
        
        # Summary
        summary = filter_result['filter_summary']
        print(f"\n📈 FILTER EFFECTIVENESS:")
        print(f"  Total removed: {summary['total_removed']}")
        
        if summary['suspicious_removal_reasons']:
            print(f"  Suspicious reasons: {summary['suspicious_removal_reasons']}")
        
        if summary['statistical_outlier_groups']:
            print(f"  Outlier groups: {summary['statistical_outlier_groups']}")

# Integration function for PokeQuant
def apply_enhanced_filtering(price_data: List[Dict], product_info: Dict, verbose: bool = True) -> List[Dict]:
    """Apply enhanced filtering to PokeQuant price data"""
    
    filter_system = EnhancedOutlierFilter()
    filter_result = filter_system.filter_price_data(price_data, product_info)
    
    if verbose:
        filter_system.print_filter_report(filter_result, product_info)
    
    return filter_result['filtered_data'] 