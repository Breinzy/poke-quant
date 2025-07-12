"""
Fixed Listing Quality Filter Module
Improved version that handles both cards and sealed products
"""

import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

@dataclass
class FilterResult:
    """Result of quality filtering"""
    is_valid: bool
    reason: str
    confidence: float  # 0.0 to 1.0

class ListingQualityFilterFixed:
    """Improved filter for eBay listings supporting cards and sealed products"""
    
    def __init__(self):
        # Patterns that indicate INVALID listings (lots, damaged, etc.)
        self.invalid_patterns = {
            # Lots and bulk sales (same as before)
            'lots': [
                r'\b\d+\s*(card|pokemon)\s*lot\b',
                r'\blot\s*of\s*\d+',
                r'\bbulk\s*(lot|sale|cards)',
                r'\bmixed\s*lot',
                r'\bcollection\s*lot',
                r'\bwholesale',
                r'\b\d+x\s*cards?',
                r'\bmultiple\s*cards?',
                r'\bvarious\s*cards?',
                r'\bassorted\s*cards?',
                r'\bbundle\s*of\s*\d+',  # Updated: specify number to avoid false positives
                r'\b\d+\s*piece\s*lot',
            ],
            
            # Damaged/poor condition (same as before)
            'damaged': [
                r'\bdamaged\b',
                r'\bheavily\s*played\b',
                r'\bpoor\s*condition\b',
                r'\bwater\s*damage',
                r'\bcreased?\b',
                r'\bbent\b',
                r'\btorn\b',
                r'\bworn\b',
                r'\bscratched\b',
                r'\bfaded\b',
                r'\bstained\b',
                r'\bfor\s*parts\b',
                r'\bas\s*is\b',
            ],
            
            # Non-cards or accessories (updated to be less aggressive)
            'non_cards': [
                r'\bcard\s*sleeves?\b',  # More specific
                r'\bbinder\b',
                r'\bplaymat\b',
                r'\bdice\b',
                r'\bcounters?\b',
                r'\bcoins?\b',
                r'\bfigurines?\b',
                r'\bplushies?\b',
                r'\btoys?\b',
                r'\bstickers?\b',
                r'\bposters?\b',
                r'\bbooks?\b',
                r'\bguides?\b',
                r'\benergy\s*cards?\s*only\b',  # More specific
                r'\bbasic\s*energy\s*only\b',  # More specific
            ],
            
            # Fake/proxy cards (same as before)
            'fake': [
                r'\bfake\b',
                r'\bproxy\b',
                r'\bcustom\b',
                r'\bhomemade\b',
                r'\bfan\s*made',
                r'\bunofficial\b',
                r'\breplica\b',
                r'\brepro\b',
                r'\breproduction\b',
                r'\bbootleg\b',
            ],
            
            # Unclear/vague listings (same as before)
            'vague': [
                r'\bmystery\s*box',
                r'\brandom\s*card',
                r'\bsurprise\s*pack',
                r'\bmixed\s*condition',
                r'\bunknown\s*condition',
                r'\bmisc\b',
                r'\bmiscellaneous\b',
                r'\betc\b',
                r'\band\s*more\b',
                r'\bplus\s*extras?',
            ],
            
            # Wrong games/franchises (same as before)
            'wrong_game': [
                r'\byu-?gi-?oh\b',
                r'\bmagic\s*the\s*gathering\b',
                r'\bmtg\b',
                r'\bdigimon\b',
                r'\bdragon\s*ball\b',
                r'\bnaruto\b',
                r'\bone\s*piece\b',
                r'\bweiss\s*schwarz\b',
                r'\bcardfight\b',
                r'\bvanguard\b',
            ]
        }
        
        # Patterns that indicate VALID listings
        self.valid_patterns = [
            r'\bpsa\s*\d+\b',  # PSA graded
            r'\bbgs\s*\d+\b',  # BGS graded
            r'\bcgc\s*\d+\b',  # CGC graded
            r'\bsgc\s*\d+\b',  # SGC graded
            r'\bmint\b',       # Mint condition
            r'\bnear\s*mint\b', # Near mint
            r'\bnm\b',         # NM abbreviation
            r'\b\d+/\d+\b',    # Card number (e.g., 25/102)
            r'\bholo\b',       # Holographic
            r'\bfirst\s*edition\b', # 1st edition
            r'\bshadowless\b', # Shadowless
            r'\bpromo\b',      # Promo cards
            r'\balt\s*art\b',  # Alternate art
            r'\bfull\s*art\b', # Full art
            r'\bsecret\s*rare\b', # Secret rare
            r'\bultra\s*rare\b',  # Ultra rare
            r'\brainbow\s*rare\b', # Rainbow rare
            r'\bsealed\b',     # Sealed products
            r'\bnew\s*in\s*box\b', # NIB
            r'\bnib\b',        # NIB abbreviation
        ]
        
        # Pokemon indicators (expanded)
        self.pokemon_indicators = [
            # Direct mentions
            r'\bpokemon\b',
            r'\bpokémon\b',
            r'\btcg\b',
            r'\btrading\s*card\s*game\b',
            r'\bpokemon\s*card\b',
            r'\bpokemon\s*tcg\b',
            
            # Card numbers (strong indicator)
            r'\b\d+/\d+\b',
            
            # Card types
            r'\bv\b', r'\bvmax\b', r'\bvstar\b', r'\bex\b', r'\bgx\b',
            
            # Set names (partial list)
            r'\bbase\s*set\b',
            r'\bbrilliant\s*stars\b',
            r'\bevolving\s*skies\b',
            r'\bvivid\s*voltage\b',
            r'\bsilver\s*tempest\b',
            r'\blost\s*origin\b',
            r'\bsword\s*shield\b',
            r'\bswsh\b',
            
            # Sealed product terms
            r'\bbooster\s*box\b',
            r'\belite\s*trainer\s*box\b',
            r'\betb\b',
            r'\bcollection\s*box\b',
        ]
        
        # Pokemon names (key ones)
        self.pokemon_names = [
            'charizard', 'pikachu', 'blastoise', 'venusaur', 'mewtwo', 'mew',
            'lugia', 'rayquaza', 'umbreon', 'espeon', 'lucario', 'garchomp'
        ]
    
    def filter_listing(self, listing: Dict[str, Any], expected_item_name: str = None, 
                      is_sealed_product: bool = False) -> FilterResult:
        """
        Filter a single listing for quality and relevance
        
        Args:
            listing: Dictionary containing listing data (title, price, etc.)
            expected_item_name: The specific card/product name we're searching for
            is_sealed_product: Whether this is a sealed product (less strict filtering)
            
        Returns:
            FilterResult with is_valid, reason, and confidence
        """
        title = listing.get('title', '').lower()
        price = listing.get('price', 0)
        
        if not title:
            return FilterResult(False, "No title", 1.0)
        
        # Check for invalid patterns
        for category, patterns in self.invalid_patterns.items():
            for pattern in patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    return FilterResult(False, f"Invalid: {category} - matched '{pattern}'", 0.9)
        
        # Price validation
        if price <= 0:
            return FilterResult(False, "Invalid price", 0.8)
        
        if price < 0.50:  # Suspiciously low price
            return FilterResult(False, "Price too low (likely damaged/fake)", 0.7)
        
        # Item name matching validation (if expected item name provided)
        if expected_item_name:
            item_match_score = self._check_item_name_match(title, expected_item_name)
            if item_match_score < 0.3:  # Flexible threshold
                return FilterResult(False, f"Item name mismatch: expected '{expected_item_name}' not well matched", 0.8)
        
        # Check for Pokemon indicators (more flexible for sealed products)
        pokemon_indicators_found = []
        for indicator_pattern in self.pokemon_indicators:
            if re.search(indicator_pattern, title, re.IGNORECASE):
                pokemon_indicators_found.append(indicator_pattern)
        
        # Check for specific Pokemon names
        pokemon_names_found = []
        for pokemon in self.pokemon_names:
            if pokemon in title:
                pokemon_names_found.append(pokemon)
        
        # Calculate confidence based on multiple factors
        confidence = 0.4  # Base confidence
        
        # Boost confidence for various indicators
        if pokemon_names_found:
            confidence += 0.3
        if pokemon_indicators_found:
            confidence += min(len(pokemon_indicators_found) * 0.1, 0.3)
        if expected_item_name and self._check_item_name_match(title, expected_item_name) > 0.7:
            confidence += 0.2
        
        # Check for valid patterns
        valid_score = 0
        for pattern in self.valid_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                valid_score += 1
        
        if valid_score > 0:
            confidence += min(valid_score * 0.05, 0.2)
        
        # Different requirements for cards vs sealed products
        if is_sealed_product:
            # More lenient for sealed products - just need some Pokemon indicators
            if not (pokemon_indicators_found or pokemon_names_found):
                return FilterResult(False, "No Pokemon indicators found for sealed product", 0.7)
        else:
            # More strict for individual cards
            if not (pokemon_names_found or len(pokemon_indicators_found) >= 1):
                return FilterResult(False, "No Pokemon name or 'pokemon' found in title", 0.8)
        
        # Additional checks for edge cases
        if len(title) < 10:
            return FilterResult(False, "Title too short", 0.7)
        
        if title.count(' ') < 2:  # Very few words
            return FilterResult(False, "Title too simple", 0.6)
        
        return FilterResult(True, "Passed quality checks", min(confidence, 1.0))
    
    def _check_item_name_match(self, title: str, expected_name: str) -> float:
        """
        Check how well the title matches the expected item name
        Returns a score from 0.0 to 1.0
        """
        title_lower = title.lower()
        expected_lower = expected_name.lower()
        
        # Exact match
        if expected_lower in title_lower:
            return 1.0
        
        # Split into words and check partial matches
        expected_words = expected_lower.split()
        matched_words = 0
        
        for word in expected_words:
            if len(word) > 2 and word in title_lower:  # Skip very short words
                matched_words += 1
        
        if len(expected_words) > 0:
            word_match_score = matched_words / len(expected_words)
        else:
            word_match_score = 0.0
        
        # Handle common variations
        variations = {
            'v': ['v', ' v ', 'v '],
            'vmax': ['vmax', ' vmax', 'v max'],
            'vstar': ['vstar', ' vstar', 'v star'],
            'charizard': ['charizard', 'zard'],
            'pikachu': ['pikachu', 'pika'],
            'booster box': ['booster box', 'booster', 'box'],
            'elite trainer box': ['elite trainer box', 'etb', 'elite trainer'],
        }
        
        # Check for variations
        for key, vars in variations.items():
            if key in expected_lower:
                for var in vars:
                    if var in title_lower:
                        word_match_score += 0.2
                        break
        
        return min(word_match_score, 1.0)
    
    def filter_listings_batch(self, listings: List[Dict[str, Any]], expected_item_name: str = None,
                            is_sealed_product: bool = False) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Filter a batch of listings
        
        Args:
            listings: List of listing dictionaries
            expected_item_name: The specific item name we're searching for
            is_sealed_product: Whether these are sealed products
            
        Returns:
            Tuple of (valid_listings, rejection_stats)
        """
        valid_listings = []
        rejection_stats = {}
        
        for listing in listings:
            result = self.filter_listing(listing, expected_item_name, is_sealed_product)
            
            if result.is_valid:
                # Add quality score to listing
                listing['quality_score'] = result.confidence
                valid_listings.append(listing)
            else:
                # Track rejection reasons
                category = result.reason.split(' - ')[0] if ' - ' in result.reason else result.reason
                category = category.split(':')[0] if ':' in category else category  # Handle "Item name mismatch: ..."
                rejection_stats[category] = rejection_stats.get(category, 0) + 1
        
        return valid_listings, rejection_stats
    
    def print_filter_summary(self, original_count: int, filtered_count: int, rejection_stats: Dict[str, int]):
        """Print a summary of filtering results"""
        rejected_count = original_count - filtered_count
        
        if rejected_count == 0:
            print(f"✅ All {original_count} listings passed quality filter")
            return
        
        print(f"🔍 Quality Filter Results:")
        print(f"  Original listings: {original_count}")
        print(f"  Valid listings: {filtered_count}")
        print(f"  Rejected listings: {rejected_count} ({(rejected_count/original_count)*100:.1f}%)")
        
        if rejection_stats:
            print(f"  Rejection reasons:")
            for reason, count in sorted(rejection_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"    • {reason}: {count}")

def test_fixed_quality_filter():
    """Test the fixed quality filter"""
    filter = ListingQualityFilterFixed()
    
    print("🧪 Testing Fixed Quality Filter")
    print("="*50)
    
    # Test cases for cards
    card_test_cases = [
        # Should PASS
        ("2022 Pokemon Sword & Shield Brilliant Stars Charizard V #154 PSA 10", True, "Charizard V", False),
        ("Pokemon Charizard V 154/172 Brilliant Stars Alt Art Ultra Rare NM", True, "Charizard V", False),
        ("Charizard V 154/172 Alt Art Sword & Shield: Brilliant Stars Pokemon TCG NM", True, "Charizard V", False),
        ("Pokemon Pikachu VMAX 188/185 Vivid Voltage Secret Rare Rainbow Holo", True, "Pikachu VMAX", False),
        ("Pikachu VMAX 188/185 Vivid Voltage Rainbow Rare Pokemon Card NM/M", True, "Pikachu VMAX", False),
        
        # Borderline (should pass with flexible matching)
        ("Charizard V 154/172 Brilliant Stars Alt Art Ultra Rare NM Sword Shield", True, "Charizard V", False),
        ("Pikachu VMAX 188/185 Vivid Voltage Secret Rare Rainbow Holo Card", True, "Pikachu VMAX", False),
        
        # Should FAIL
        ("34 Pokemon Card Lot Mixed Condition Vintage", False, "Charizard V", False),
        ("Pokemon Card Collection 100+ Cards Bulk Sale", False, "Charizard V", False),
        ("Charizard V Damaged Creased Water Damage As Is", False, "Charizard V", False),
    ]
    
    # Test cases for sealed products
    sealed_test_cases = [
        # Should PASS
        ("Pokemon Brilliant Stars Booster Box Sealed New", True, "Brilliant Stars Booster Box", True),
        ("Evolving Skies Booster Box Pokemon TCG Sealed", True, "Evolving Skies Booster Box", True),
        ("Pokemon Silver Tempest Elite Trainer Box ETB Sealed", True, "Silver Tempest Elite Trainer Box", True),
        ("Base Set Booster Box Pokemon Vintage Sealed", True, "Base Set Booster Box", True),
        
        # Should FAIL
        ("Random Pokemon Card Mystery Box Lot", False, "Brilliant Stars Booster Box", True),
        ("Pokemon Card Collection 500+ Cards", False, "Evolving Skies Booster Box", True),
    ]
    
    print("\n🎯 Testing Card Listings:")
    for title, expected, item_name, is_sealed in card_test_cases:
        result = filter.filter_listing({'title': title, 'price': 25.0}, item_name, is_sealed)
        status = "✅" if result.is_valid == expected else "❌"
        print(f"{status} {title[:60]}... -> {result.is_valid} ({result.reason})")
    
    print("\n📦 Testing Sealed Product Listings:")
    for title, expected, item_name, is_sealed in sealed_test_cases:
        result = filter.filter_listing({'title': title, 'price': 150.0}, item_name, is_sealed)
        status = "✅" if result.is_valid == expected else "❌"
        print(f"{status} {title[:60]}... -> {result.is_valid} ({result.reason})")

if __name__ == "__main__":
    test_fixed_quality_filter() 