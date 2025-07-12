#!/usr/bin/env python3
"""
LLM-Enhanced Filtering System for PokeQuant
Inspired by PriceCharting's approach to data quality
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import google.generativeai as genai
import statistics

@dataclass
class FilterDecision:
    """Result of LLM filtering decision"""
    action: str  # 'keep', 'remove', 'flag'
    confidence: float  # 0.0 to 1.0
    reason: str
    detected_language: str
    detected_product_type: str
    detected_condition: str
    is_authentic: bool
    price_reasonableness: float  # 0.0 to 1.0

class LLMEnhancedFilter:
    """LLM-powered filtering system for Pokemon product listings"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Price ranges for reasonableness check (in USD)
        self.expected_price_ranges = {
            'booster_box': {'min': 50, 'max': 800, 'typical': (90, 200)},
            'elite_trainer_box': {'min': 20, 'max': 150, 'typical': (35, 60)},
            'booster_pack': {'min': 2, 'max': 50, 'typical': (3, 8)},
            'theme_deck': {'min': 5, 'max': 40, 'typical': (10, 20)},
            'tin': {'min': 8, 'max': 80, 'typical': (15, 35)},
            'collection_box': {'min': 15, 'max': 300, 'typical': (25, 100)},
            'single_card': {'min': 0.25, 'max': 10000, 'typical': (1, 50)},
            'bundle': {'min': 10, 'max': 200, 'typical': (20, 80)},
            'starter_deck': {'min': 8, 'max': 50, 'typical': (12, 25)}
        }
    
    def analyze_listing(self, title: str, description: str, price: float, 
                       expected_product_type: str) -> FilterDecision:
        """
        Analyze a single listing using LLM to determine if it should be kept
        
        Args:
            title: Listing title
            description: Listing description (optional)
            price: Listed price in USD
            expected_product_type: What we think this should be (e.g., 'booster_box')
        """
        
        prompt = self._build_analysis_prompt(title, description, price, expected_product_type)
        
        try:
            # Combine system prompt and user prompt for Gemini
            full_prompt = f"{self._get_system_prompt()}\n\n{prompt}\n\nRespond ONLY with valid JSON."
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent analysis
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text)
            return self._parse_llm_response(result, price, expected_product_type)
            
        except Exception as e:
            # Fallback to basic filtering if LLM fails
            return FilterDecision(
                action='flag',
                confidence=0.5,
                reason=f'LLM analysis failed: {str(e)}',
                detected_language='unknown',
                detected_product_type='unknown',
                detected_condition='unknown',
                is_authentic=True,
                price_reasonableness=0.5
            )
    
    def batch_filter_listings(self, listings: List[Dict], expected_product_type: str,
                             max_concurrent: int = 5) -> Dict[str, Any]:
        """
        Filter a batch of listings with LLM analysis
        
        Args:
            listings: List of listing dicts with 'title', 'description', 'price'
            expected_product_type: Expected product type
            max_concurrent: Max concurrent LLM calls (cost control)
        """
        
        results = {
            'kept': [],
            'removed': [],
            'flagged': [],
            'analysis_summary': {}
        }
        
        # Process in batches to control API costs
        for i in range(0, len(listings), max_concurrent):
            batch = listings[i:i + max_concurrent]
            
            for listing in batch:
                decision = self.analyze_listing(
                    title=listing.get('title', ''),
                    description=listing.get('description', ''),
                    price=listing.get('price', 0),
                    expected_product_type=expected_product_type
                )
                
                # Categorize based on decision
                listing['filter_decision'] = decision
                
                if decision.action == 'keep':
                    results['kept'].append(listing)
                elif decision.action == 'remove':
                    results['removed'].append(listing)
                else:  # flag
                    results['flagged'].append(listing)
        
        # Generate summary
        results['analysis_summary'] = self._generate_analysis_summary(results)
        
        return results
    
    def _get_system_prompt(self) -> str:
        """System prompt for LLM analysis"""
        return """You are an expert Pokemon TCG product classifier helping filter eBay listings for price analysis.

Your job is to analyze listing titles and descriptions to determine:
1. Whether the listing matches the expected product type
2. Language/region of the product
3. Condition and authenticity
4. Whether the price seems reasonable

Key Pokemon product types:
- Booster Box: 36 packs, factory sealed (English: $50-800)
- Elite Trainer Box (ETB): Usually 8-11 packs + accessories ($20-150)
- Booster Pack: Single pack ($2-50)
- Bundle/Multi-pack: Multiple packs, not a full box ($10-200)
- Theme/Battle Deck: Pre-constructed deck ($5-40)
- Tin: Metal container with packs ($8-80)
- Collection Box: Special box with packs + promos ($15-300)

Red flags to watch for:
- Japanese/Foreign language mixed with English searches
- "Empty box", "box only", "damaged", "opened", "resealed"
- Individual packs listed as "booster box"
- Bundles/multipacks mislabeled as booster boxes
- Extreme prices (too high or too low)
- Reproduction/proxy/fake indicators

Respond ONLY with valid JSON in this format:
{
  "action": "keep|remove|flag",
  "confidence": 0.85,
  "language": "english|japanese|korean|mixed|unknown",
  "product_type": "booster_box|elite_trainer_box|booster_pack|bundle|etc",
  "condition": "new|used|damaged|opened|unknown",
  "is_authentic": true,
  "price_reasonable": true,
  "reasoning": "Brief explanation of decision"
}"""

    def _build_analysis_prompt(self, title: str, description: str, price: float, 
                              expected_product_type: str) -> str:
        """Build the analysis prompt for a specific listing"""
        
        expected_range = self.expected_price_ranges.get(expected_product_type, {})
        typical_min, typical_max = expected_range.get('typical', (0, 999999))
        
        return f"""Analyze this Pokemon TCG listing:

EXPECTED PRODUCT TYPE: {expected_product_type}
TITLE: {title}
DESCRIPTION: {description[:500] if description else "No description"}
PRICE: ${price}

TYPICAL PRICE RANGE for {expected_product_type}: ${typical_min} - ${typical_max}

Does this listing match the expected product type? Is it authentic English product? Is the price reasonable?

Focus on semantic meaning - "4 Booster Packs" is NOT a "Booster Box" even if the title says "box".
Japanese/Korean products should be flagged unless specifically looking for those.
"""

    def _parse_llm_response(self, llm_result: Dict, price: float, 
                           expected_product_type: str) -> FilterDecision:
        """Parse LLM response into FilterDecision"""
        
        # Calculate price reasonableness score
        price_reasonable = self._calculate_price_reasonableness(
            price, llm_result.get('product_type', expected_product_type)
        )
        
        return FilterDecision(
            action=llm_result.get('action', 'flag'),
            confidence=llm_result.get('confidence', 0.5),
            reason=llm_result.get('reasoning', 'No reason provided'),
            detected_language=llm_result.get('language', 'unknown'),
            detected_product_type=llm_result.get('product_type', 'unknown'),
            detected_condition=llm_result.get('condition', 'unknown'),
            is_authentic=llm_result.get('is_authentic', True),
            price_reasonableness=price_reasonable
        )
    
    def _calculate_price_reasonableness(self, price: float, product_type: str) -> float:
        """Calculate how reasonable the price is (0.0 to 1.0)"""
        
        if product_type not in self.expected_price_ranges:
            return 0.5  # Unknown product type
        
        ranges = self.expected_price_ranges[product_type]
        min_price, max_price = ranges['min'], ranges['max']
        typical_min, typical_max = ranges['typical']
        
        if price < min_price or price > max_price:
            return 0.1  # Outside reasonable bounds
        elif typical_min <= price <= typical_max:
            return 1.0  # Perfect range
        elif price < typical_min:
            # Below typical but above minimum
            return 0.3 + 0.4 * (price - min_price) / (typical_min - min_price)
        else:
            # Above typical but below maximum  
            return 0.3 + 0.4 * (max_price - price) / (max_price - typical_max)
    
    def _generate_analysis_summary(self, results: Dict) -> Dict:
        """Generate summary statistics from batch analysis"""
        
        total = len(results['kept']) + len(results['removed']) + len(results['flagged'])
        if total == 0:
            return {}
        
        return {
            'total_analyzed': total,
            'kept_count': len(results['kept']),
            'removed_count': len(results['removed']),
            'flagged_count': len(results['flagged']),
            'keep_rate': len(results['kept']) / total,
            'removal_rate': len(results['removed']) / total,
            'flag_rate': len(results['flagged']) / total,
            'languages_detected': self._count_languages(results),
            'product_types_detected': self._count_product_types(results),
            'avg_confidence': self._calculate_avg_confidence(results)
        }
    
    def _count_languages(self, results: Dict) -> Dict:
        """Count detected languages across all results"""
        languages = {}
        for category in ['kept', 'removed', 'flagged']:
            for item in results[category]:
                lang = item['filter_decision'].detected_language
                languages[lang] = languages.get(lang, 0) + 1
        return languages
    
    def _count_product_types(self, results: Dict) -> Dict:
        """Count detected product types across all results"""
        types = {}
        for category in ['kept', 'removed', 'flagged']:
            for item in results[category]:
                ptype = item['filter_decision'].detected_product_type
                types[ptype] = types.get(ptype, 0) + 1
        return types
    
    def _calculate_avg_confidence(self, results: Dict) -> float:
        """Calculate average confidence across all decisions"""
        confidences = []
        for category in ['kept', 'removed', 'flagged']:
            for item in results[category]:
                confidences.append(item['filter_decision'].confidence)
        return statistics.mean(confidences) if confidences else 0.0

# Integration function for existing PokeQuant system
def apply_llm_enhanced_filtering(price_data: List[Dict], product_info: Dict, 
                                verbose: bool = False) -> Dict[str, Any]:
    """
    Apply LLM-enhanced filtering to price data
    
    Args:
        price_data: List of price data points with titles/descriptions
        product_info: Product information
        verbose: Whether to print detailed output
    """
    
    # Check if LLM filtering is enabled and API key is available
    if not os.getenv('OPENAI_API_KEY'):
        if verbose:
            print("   ⚠️ OpenAI API key not found, skipping LLM filtering")
        return {
            'filtered_data': price_data,
            'removed_suspicious': [],
            'removed_statistical': [],
            'llm_analysis': None
        }
    
    # Determine expected product type
    product_name = product_info.get('name', '').lower()
    if 'booster box' in product_name:
        expected_type = 'booster_box'
    elif 'elite trainer' in product_name:
        expected_type = 'elite_trainer_box'
    elif 'collection box' in product_name:
        expected_type = 'collection_box'
    else:
        expected_type = 'unknown'
    
    if verbose:
        print(f"   🤖 Applying LLM filtering for product type: {expected_type}")
    
    # Initialize LLM filter
    llm_filter = LLMEnhancedFilter()
    
    # Convert price data to format expected by LLM filter
    listings = []
    for point in price_data:
        # Get title from sample_titles if available
        title = ""
        if 'sample_titles' in point and point['sample_titles']:
            title = point['sample_titles'][0]
        elif 'title' in point:
            title = point['title']
        
        listings.append({
            'title': title,
            'description': point.get('description', ''),
            'price': point['price'],
            'original_data': point
        })
    
    # Apply LLM filtering
    llm_results = llm_filter.batch_filter_listings(listings, expected_type, max_concurrent=3)
    
    if verbose:
        summary = llm_results['analysis_summary']
        print(f"   📊 LLM Analysis: {summary.get('kept_count', 0)} kept, "
              f"{summary.get('removed_count', 0)} removed, "
              f"{summary.get('flagged_count', 0)} flagged")
        
        if summary.get('languages_detected'):
            print(f"   🌍 Languages: {summary['languages_detected']}")
    
    # Combine LLM decisions with original data
    filtered_data = []
    removed_items = []
    
    for item in llm_results['kept']:
        filtered_data.append(item['original_data'])
    
    for item in llm_results['removed'] + llm_results['flagged']:
        removed_items.append({
            'point': item['original_data'],
            'reason': f"LLM: {item['filter_decision'].reason}"
        })
    
    return {
        'filtered_data': filtered_data,
        'removed_suspicious': removed_items,
        'removed_statistical': [],  # LLM handles this
        'llm_analysis': llm_results['analysis_summary']
    }

if __name__ == "__main__":
    # Test the LLM filter
    test_listings = [
        {
            'title': 'Pokemon Brilliant Stars Booster Box 36 Packs Factory Sealed',
            'description': 'Brand new factory sealed booster box',
            'price': 149.99
        },
        {
            'title': 'Pokemon Brilliant Stars Booster Box - 4 Packs Only',
            'description': '4 booster packs from brilliant stars',
            'price': 39.99
        },
        {
            'title': 'ポケモンカード ブリリアントスター 1BOX',
            'description': 'Japanese Pokemon cards',
            'price': 89.99
        }
    ]
    
    llm_filter = LLMEnhancedFilter()
    
    for listing in test_listings:
        decision = llm_filter.analyze_listing(
            listing['title'],
            listing['description'], 
            listing['price'],
            'booster_box'
        )
        
        print(f"\nTitle: {listing['title']}")
        print(f"Decision: {decision.action} ({decision.confidence:.2f} confidence)")
        print(f"Reason: {decision.reason}")
        print(f"Detected Type: {decision.detected_product_type}")
        print(f"Language: {decision.detected_language}") 