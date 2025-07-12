"""
Search Generator Module
Generates targeted eBay search terms for specific Pokémon cards
"""

import re
from typing import List, Dict, Any, Optional

class SearchGenerator:
    """Generates precise eBay search terms for specific cards"""
    
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
    
    def generate_search_terms(self, card: Dict[str, Any]) -> List[str]:
        """Generate targeted search terms for a specific card or sealed product"""
        card_name = card.get('card_name', card.get('product_name', 'Unknown'))
        set_name = card.get('set_name', '')
        card_number = card.get('card_number', '')
        
        # Check if this is a sealed product
        is_sealed_product = 'product_type' in card
        
        if is_sealed_product:
            return self._generate_sealed_product_terms(card)
        else:
            return self._generate_card_terms(card)
    
    def _generate_card_terms(self, card: Dict[str, Any]) -> List[str]:
        """Generate search terms for individual cards"""
        card_name = card.get('card_name', 'Unknown')
        set_name = card.get('set_name', '')
        card_number = card.get('card_number', '')
        
        terms = []
        
        # Base search - exact card name
        base_term = f"{card_name} pokemon card"
        terms.append(base_term)
        
        # Add set information if available
        if set_name:
            set_term = f"{card_name} {set_name} pokemon"
            terms.append(set_term)
            
            # Add card number if available
            if card_number:
                numbered_term = f"{card_name} {set_name} {card_number} pokemon"
                terms.append(numbered_term)
        
        # Add condition-specific terms for high-value cards
        high_value_conditions = ["PSA 10", "BGS 10", "mint"]
        
        for condition in high_value_conditions:
            condition_term = f"{card_name} pokemon {condition}"
            terms.append(condition_term)
        
            if set_name:
                condition_set_term = f"{card_name} {set_name} {condition}"
                terms.append(condition_set_term)
        
        return terms
    
    def _generate_sealed_product_terms(self, product: Dict[str, Any]) -> List[str]:
        """Generate search terms for sealed products"""
        product_name = product.get('product_name', 'Unknown')
        set_name = product.get('set_name', '')
        product_type = product.get('product_type', '')
        
        terms = []
        
        # Direct product name search
        base_term = f"{product_name} pokemon"
        terms.append(base_term)
        
        # Variations with "sealed"
        sealed_term = f"{product_name} sealed"
        terms.append(sealed_term)
        
        # Set + product type combinations
        if set_name and product_type:
            type_term = f"{set_name} {product_type} pokemon"
            terms.append(type_term)
            
            sealed_type_term = f"{set_name} {product_type} sealed"
            terms.append(sealed_type_term)
        
        # For booster boxes specifically
        if "booster box" in product_name.lower():
            box_terms = [
                f"{set_name} booster box",
                f"{set_name} sealed booster box", 
                f"{set_name} booster case"
            ]
            terms.extend(box_terms)
        
        # For special collections
        if any(word in product_name.lower() for word in ["collection", "premium", "elite"]):
            collection_terms = [
                f"{set_name} collection box",
                f"{set_name} premium collection",
                f"{set_name} elite trainer box"
            ]
            terms.extend(collection_terms)
        
        return terms
    
    def generate_graded_search_terms(self, card: Dict[str, Any], grading_companies: List[str] = None) -> List[str]:
        """Generate search terms specifically for graded cards"""
        if grading_companies is None:
            grading_companies = ['PSA', 'BGS', 'CGC']
        
        base_terms = self.generate_search_terms(card, include_variants=False)
        graded_terms = []
        
        for term in base_terms:
            for company in grading_companies:
                # Add grading company to search
                graded_terms.append(f"{term} {company}")
                
                # Add specific grades for high-value searches
                for grade in ['10', '9.5', '9']:
                    graded_terms.append(f"{term} {company} {grade}")
        
        return graded_terms
    
    def generate_condition_search_terms(self, card: Dict[str, Any], conditions: List[str] = None) -> List[str]:
        """Generate search terms for specific conditions"""
        if conditions is None:
            conditions = ['mint', 'near mint', 'nm', 'lp', 'light played']
        
        base_terms = self.generate_search_terms(card, include_variants=False)
        condition_terms = []
        
        for term in base_terms:
            for condition in conditions:
                condition_terms.append(f"{term} {condition}")
        
        return condition_terms
    
    def _get_set_variations(self, set_name: str) -> List[str]:
        """Get different ways to search for a set name"""
        set_name_lower = set_name.lower().strip()
        
        # Check if we have predefined abbreviations
        if set_name_lower in self.set_abbreviations:
            return self.set_abbreviations[set_name_lower]
        
        # Generate variations for unknown sets
        variations = [set_name]
        
        # Add acronym if set has multiple words
        words = set_name.split()
        if len(words) > 1:
            acronym = ''.join(word[0].upper() for word in words)
            variations.append(acronym)
        
        # Add shortened version (first word only)
        if len(words) > 1:
            variations.append(words[0])
        
        return variations
    
    def _generate_variants(self, card: Dict[str, Any]) -> List[str]:
        """Generate variant search terms"""
        variants = []
        card_name = card.get('card_name', '').strip()
        
        # Try without "pokemon card" suffix
        variants.append(card_name)
        
        # Add TCG variant
        variants.append(f"{card_name} TCG")
        
        # Check for card type suffixes and create variants
        for suffix in self.card_suffixes:
            if suffix.lower() in card_name.lower():
                # Try search without the suffix
                name_without_suffix = re.sub(rf'\s*{re.escape(suffix)}\s*$', '', card_name, flags=re.IGNORECASE)
                if name_without_suffix != card_name:
                    variants.append(f"{name_without_suffix} pokemon card")
        
        return variants
    
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
    
    def prioritize_search_terms(self, search_terms: List[str], card: Dict[str, Any]) -> List[str]:
        """Order search terms by priority (most specific first)"""
        if not search_terms:
            return []
        
        prioritized = []
        
        # Priority 1: Terms with set name AND card number
        for term in search_terms:
            if self._has_set_and_number(term, card):
                prioritized.append(term)
        
        # Priority 2: Terms with set name OR card number
        for term in search_terms:
            if term not in prioritized and (self._has_set_name(term, card) or self._has_card_number(term, card)):
                prioritized.append(term)
        
        # Priority 3: Basic terms
        for term in search_terms:
            if term not in prioritized:
                prioritized.append(term)
        
        return prioritized
    
    def _has_set_and_number(self, term: str, card: Dict[str, Any]) -> bool:
        """Check if term contains both set name and card number"""
        set_name = card.get('set_name', '').lower()
        card_number = card.get('card_number', '')
        
        term_lower = term.lower()
        has_set = set_name and set_name in term_lower
        has_number = card_number and card_number in term
        
        return has_set and has_number
    
    def _has_set_name(self, term: str, card: Dict[str, Any]) -> bool:
        """Check if term contains set name"""
        set_name = card.get('set_name', '').lower()
        return set_name and set_name in term.lower()
    
    def _has_card_number(self, term: str, card: Dict[str, Any]) -> bool:
        """Check if term contains card number"""
        card_number = card.get('card_number', '')
        return card_number and card_number in term
    
    def generate_batch_search_plan(self, items: List[Dict[str, Any]], max_terms_per_item: int = 3) -> Dict[str, Any]:
        """Generate a search plan for multiple items (cards and sealed products)"""
        plan = {
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
            
            search_terms = self.generate_search_terms(item)
            prioritized_terms = self.prioritize_search_terms(search_terms, item)
            
            # Limit terms per item
            selected_terms = prioritized_terms[:max_terms_per_item]
            
            item_plan = {
                "item_id": item_id,
                "item_name": item_name,
                "item_type": "sealed_product" if is_sealed_product else "card",
                "set_name": item.get('set_name', ''),
                "search_terms": selected_terms,
                "term_count": len(selected_terms)
            }
            
            if not is_sealed_product:
                item_plan["card_number"] = item.get('card_number', '')
            else:
                item_plan["product_type"] = item.get('product_type', '')
            
            plan["search_plans"].append(item_plan)
            plan["total_searches"] += len(selected_terms)
        
        return plan 