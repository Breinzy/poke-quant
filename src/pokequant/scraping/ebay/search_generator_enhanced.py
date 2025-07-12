"""
Enhanced Search Generator Module
Generates platform-specific search terms for Pokémon cards and sealed products
"""

import re
from typing import List, Dict, Any, Optional
from enum import Enum

class SearchPlatform(Enum):
    """Platform types for different search strategies"""
    PRICECHARTING = "pricecharting"  # Exact, minimal terms
    EBAY = "ebay"                   # Enhanced with filtering terms
    GENERIC = "generic"             # Balanced approach

class EnhancedSearchGenerator:
    """Generates platform-specific search terms for cards and sealed products"""
    
    def __init__(self):
        # Common abbreviations and variations
        self.set_abbreviations = {
            'base set': ['base set', 'base', 'bs'],
            'jungle': ['jungle', 'jun'],
            'fossil': ['fossil', 'fos'],
            'team rocket': ['team rocket', 'tr'],
            'gym heroes': ['gym heroes', 'gh'],
            'gym challenge': ['gym challenge', 'gc'],
            'neo genesis': ['neo genesis', 'ng'],
            'neo discovery': ['neo discovery', 'nd'],
            'neo destiny': ['neo destiny', 'ndes'],
            'neo revelation': ['neo revelation', 'nr'],
            'evolving skies': ['evolving skies', 'es', 'evs'],
            'brilliant stars': ['brilliant stars', 'bs', 'brs'],
            'darkness ablaze': ['darkness ablaze', 'dab', 'da'],
            'vivid voltage': ['vivid voltage', 'vv'],
            'battle styles': ['battle styles', 'bst'],
            'chilling reign': ['chilling reign', 'cr', 'chr'],
            'fusion strike': ['fusion strike', 'fst', 'fs'],
            'astral radiance': ['astral radiance', 'ar'],
            'sword shield': ['sword shield', 'swsh', 'ssh'],
            'lost origin': ['lost origin', 'lo'],
            'silver tempest': ['silver tempest', 'st']
        }
        
        # Common card type suffixes
        self.card_suffixes = [
            'V', 'VMAX', 'VSTAR', 'ex', 'EX', 'GX', 'TAG TEAM',
            'Prime', 'Legend', 'BREAK', 'Lv.X', 'Star'
        ]
    
    def generate_search_terms(self, item: Dict[str, Any], platform: SearchPlatform = SearchPlatform.EBAY, 
                            max_terms: int = 3) -> List[str]:
        """Generate platform-specific search terms"""
        
        # Check if this is a sealed product
        is_sealed_product = 'product_type' in item
        
        if is_sealed_product:
            terms = self._generate_sealed_product_terms(item, platform)
        else:
            terms = self._generate_card_terms(item, platform)
        
        # Clean and prioritize terms
        cleaned_terms = self._clean_search_terms(terms)
        prioritized_terms = self._prioritize_search_terms(cleaned_terms, item, platform)
        
        return prioritized_terms[:max_terms]
    
    def _generate_card_terms(self, card: Dict[str, Any], platform: SearchPlatform) -> List[str]:
        """Generate platform-specific search terms for individual cards"""
        card_name = card.get('card_name', 'Unknown')
        set_name = card.get('set_name', '')
        card_number = card.get('card_number', '')
        
        if platform == SearchPlatform.PRICECHARTING:
            return self._generate_pricecharting_card_terms(card_name, set_name, card_number)
        elif platform == SearchPlatform.EBAY:
            return self._generate_ebay_card_terms(card_name, set_name, card_number)
        else:
            return self._generate_generic_card_terms(card_name, set_name, card_number)
    
    def _generate_pricecharting_card_terms(self, card_name: str, set_name: str, card_number: str) -> List[str]:
        """Generate exact terms for PriceCharting searches - prioritize card numbers for direct matches"""
        terms = []
        
        # PRIORITY 1: Card name + card number (direct match - most important!)
        if card_number:
            terms.append(f"{card_name} {card_number}")
            
            # Alternative formats with card number
            if set_name:
                terms.append(f"{card_name} {set_name} {card_number}")
                terms.append(f"{card_name} ({set_name}) {card_number}")
        
        # PRIORITY 2: Card name with set (if no card number available)
        if set_name:
            terms.append(f"{card_name} ({set_name})")
            terms.append(f"{card_name} - {set_name}")
        
        # PRIORITY 3: Exact card name only (fallback - gives list instead of direct match)
        terms.append(card_name)
        
        return terms
    
    def _generate_ebay_card_terms(self, card_name: str, set_name: str, card_number: str) -> List[str]:
        """Generate very specific, exact terms for eBay searches (no generic terms!)"""
        terms = []
        
        # NEVER use generic terms on eBay - be very specific!
        base_search = f"{card_name}"
        if card_number:
            base_search += f" {card_number}"
        if set_name:
            base_search += f" {set_name}"
        
        # Specific condition searches (most targeted)
        if set_name and card_number:
            terms.append(f"{card_name} {card_number} {set_name} near mint")
            terms.append(f"{card_name} {card_number} {set_name} nm")
            terms.append(f"{card_name} {card_number} {set_name} mint")
        
        # Specific grading searches
        grading_terms = ["psa 10", "psa 9", "bgs 10", "cgc 10"]
        for grade in grading_terms:
            if set_name and card_number:
                terms.append(f"{card_name} {card_number} {set_name} {grade}")
            elif set_name:
                terms.append(f"{card_name} {set_name} {grade}")
        
        # Base exact search (no generic keywords)
        if set_name and card_number:
            terms.append(f"{card_name} {card_number} {set_name}")
        elif set_name:
            terms.append(f"{card_name} {set_name}")
        
        return terms
    
    def _generate_generic_card_terms(self, card_name: str, set_name: str, card_number: str) -> List[str]:
        """Generate balanced terms for generic searches"""
        terms = []
        
        # Card name with minimal enhancement
        terms.append(card_name)
        
        if set_name:
            terms.append(f"{card_name} {set_name}")
        
        terms.append(f"{card_name} TCG")
        
        return terms
    
    def _generate_sealed_product_terms(self, product: Dict[str, Any], platform: SearchPlatform) -> List[str]:
        """Generate platform-specific search terms for sealed products"""
        product_name = product.get('product_name', 'Unknown')
        set_name = product.get('set_name', '')
        product_type = product.get('product_type', '')
        
        if platform == SearchPlatform.PRICECHARTING:
            return self._generate_pricecharting_sealed_terms(product_name, set_name, product_type)
        elif platform == SearchPlatform.EBAY:
            return self._generate_ebay_sealed_terms(product_name, set_name, product_type)
        else:
            return self._generate_generic_sealed_terms(product_name, set_name, product_type)
    
    def _generate_pricecharting_sealed_terms(self, product_name: str, set_name: str, product_type: str) -> List[str]:
        """Generate exact terms for PriceCharting sealed product searches"""
        terms = []
        
        # Exact product name
        terms.append(product_name)
        
        # Set + product type combination
        if set_name and product_type:
            terms.append(f"{set_name} {product_type}")
        
        # Alternative exact formats
        if "booster box" in product_name.lower():
            terms.append(f"{set_name} Booster Box")
            terms.append(f"{set_name} Box")
        
        if "elite trainer" in product_name.lower():
            terms.append(f"{set_name} Elite Trainer Box")
            terms.append(f"{set_name} ETB")
        
        return terms
    
    def _generate_ebay_sealed_terms(self, product_name: str, set_name: str, product_type: str) -> List[str]:
        """Generate very specific, exact terms for eBay sealed product searches"""
        terms = []
        
        # Very specific sealed product searches (no generic terms!)
        base_search = f"{set_name} {product_type}" if set_name and product_type else product_name
        
        # Specific condition/state searches
        specific_terms = [
            f"{base_search} factory sealed",
            f"{base_search} sealed english",
            f"{base_search} new sealed",
            f"{base_search} sealed new"
        ]
        terms.extend(specific_terms)
        
        # Booster box specific exact searches
        if "booster box" in product_name.lower():
            booster_terms = [
                f"{set_name} booster box factory sealed",
                f"{set_name} booster box english sealed",
                f"{set_name} booster box new",
                f"{set_name} display box sealed"
            ]
            terms.extend(booster_terms)
        
        # Elite Trainer Box specific exact searches  
        if "elite trainer" in product_name.lower():
            etb_terms = [
                f"{set_name} elite trainer box sealed",
                f"{set_name} ETB factory sealed", 
                f"{set_name} ETB new sealed"
            ]
            terms.extend(etb_terms)
        
        # Base exact search (no generic keywords)
        terms.append(base_search)
        
        return terms
    
    def _generate_generic_sealed_terms(self, product_name: str, set_name: str, product_type: str) -> List[str]:
        """Generate balanced terms for generic sealed product searches"""
        terms = []
        
        terms.append(product_name)
        
        if set_name and product_type:
            terms.append(f"{set_name} {product_type}")
        
        terms.append(f"{product_name} sealed")
        
        return terms
    
    def _clean_search_terms(self, search_terms: List[str]) -> List[str]:
        """Clean and deduplicate search terms"""
        cleaned = []
        seen = set()
        
        for term in search_terms:
            # Clean the term
            clean_term = ' '.join(term.split())  # Remove extra whitespace
            clean_term = clean_term.strip()
            
            # Skip empty or very short terms
            if len(clean_term) < 3:
                continue
            
            # Deduplicate (case insensitive)
            term_lower = clean_term.lower()
            if term_lower not in seen:
                seen.add(term_lower)
                cleaned.append(clean_term)
        
        return cleaned
    
    def _prioritize_search_terms(self, search_terms: List[str], item: Dict[str, Any], 
                                platform: SearchPlatform) -> List[str]:
        """Order search terms by priority based on platform and specificity"""
        if not search_terms:
            return []
        
        prioritized = []
        remaining = search_terms.copy()
        
        # Platform-specific prioritization
        if platform == SearchPlatform.PRICECHARTING:
            # For PriceCharting, prefer terms with card numbers first (direct matches)
            card_number = item.get('card_number', '')
            if card_number:
                number_terms = [t for t in remaining if card_number in t]
                prioritized.extend(number_terms)
                remaining = [t for t in remaining if t not in number_terms]
            
            # Then prefer exact matches
            exact_terms = [t for t in remaining if self._is_exact_term(t, item)]
            prioritized.extend(exact_terms)
            remaining = [t for t in remaining if t not in exact_terms]
            
        elif platform == SearchPlatform.EBAY:
            # For eBay, prefer very specific condition/grading terms first
            condition_terms = [t for t in remaining if self._has_condition_or_grading(t)]
            prioritized.extend(condition_terms)
            remaining = [t for t in remaining if t not in condition_terms]
            
            # Then prefer specific sealed product state terms
            sealed_state_terms = [t for t in remaining if self._has_sealed_state_terms(t)]
            prioritized.extend(sealed_state_terms)
            remaining = [t for t in remaining if t not in sealed_state_terms]
        
        # Add remaining terms
        prioritized.extend(remaining)
        
        return prioritized
    
    def _is_exact_term(self, term: str, item: Dict[str, Any]) -> bool:
        """Check if term is exact/minimal for the item"""
        item_name = item.get('card_name', item.get('product_name', ''))
        return term.strip() == item_name.strip()
    
    def _has_condition_or_grading(self, term: str) -> bool:
        """Check if term has specific condition or grading terms"""
        condition_keywords = ['near mint', 'nm', 'mint', 'psa 10', 'psa 9', 'bgs 10', 'cgc 10', 'psa', 'bgs', 'cgc']
        term_lower = term.lower()
        return any(keyword in term_lower for keyword in condition_keywords)
    
    def _has_sealed_state_terms(self, term: str) -> bool:
        """Check if term has specific sealed product state terms"""
        sealed_keywords = ['factory sealed', 'sealed english', 'new sealed', 'sealed new']
        term_lower = term.lower()
        return any(keyword in term_lower for keyword in sealed_keywords)
    
    def generate_batch_search_plan(self, items: List[Dict[str, Any]], platform: SearchPlatform = SearchPlatform.EBAY,
                                 max_terms_per_item: int = 3) -> Dict[str, Any]:
        """Generate a platform-specific search plan for multiple items"""
        plan = {
            "platform": platform.value,
            "total_items": len(items),
            "search_plans": [],
            "total_searches": 0,
            "cards_count": 0,
            "sealed_products_count": 0
        }
        
        for item in items:
            # Determine if this is a card or sealed product
            is_sealed_product = 'product_type' in item
            
            if is_sealed_product:
                plan["sealed_products_count"] += 1
                item_name = item.get('product_name', 'Unknown Product')
                item_id = item.get('id', 'unknown')
            else:
                plan["cards_count"] += 1
                item_name = item.get('card_name', 'Unknown Card')
                item_id = item.get('id', 'unknown')
            
            search_terms = self.generate_search_terms(item, platform, max_terms_per_item)
            
            item_plan = {
                "item_id": item_id,
                "item_name": item_name,
                "item_type": "sealed_product" if is_sealed_product else "card",
                "set_name": item.get('set_name', ''),
                "search_terms": search_terms,
                "term_count": len(search_terms),
                "platform_strategy": platform.value
            }
            
            if not is_sealed_product:
                item_plan["card_number"] = item.get('card_number', '')
            else:
                item_plan["product_type"] = item.get('product_type', '')
            
            plan["search_plans"].append(item_plan)
            plan["total_searches"] += len(search_terms)
        
        return plan

# Test the enhanced generator
if __name__ == "__main__":
    generator = EnhancedSearchGenerator()
    
    # Test card
    test_card = {
        "card_name": "Charizard V",
        "set_name": "Brilliant Stars", 
        "card_number": "154"
    }
    
    # Test sealed product
    test_sealed = {
        "product_name": "Brilliant Stars Booster Box",
        "set_name": "Brilliant Stars",
        "product_type": "Booster Box"
    }
    
    print("=== CARD SEARCH TERMS ===")
    print("PriceCharting:", generator.generate_search_terms(test_card, SearchPlatform.PRICECHARTING))
    print("eBay:", generator.generate_search_terms(test_card, SearchPlatform.EBAY))
    
    print("\n=== SEALED PRODUCT SEARCH TERMS ===")
    print("PriceCharting:", generator.generate_search_terms(test_sealed, SearchPlatform.PRICECHARTING))
    print("eBay:", generator.generate_search_terms(test_sealed, SearchPlatform.EBAY)) 