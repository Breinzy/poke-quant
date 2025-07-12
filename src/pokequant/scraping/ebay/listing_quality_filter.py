"""
Listing Quality Filter Module
Audits eBay listings to ensure they are relevant single-card listings
Filters out lots, damaged cards, irrelevant items, etc.
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

class ListingQualityFilter:
    """Filters eBay listings for quality and relevance"""
    
    def __init__(self):
        # Patterns that indicate INVALID listings (lots, damaged, etc.)
        self.invalid_patterns = {
            # Lots and bulk sales
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
                r'\bbundle\s*of',
                r'\bpack\s*of\s*\d+',
                r'\b\d+\s*piece\s*lot',
            ],
            
            # Damaged/poor condition
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
            
            # Non-cards or accessories
            'non_cards': [
                r'\bsleeves?\b',
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
                r'\bdecks?\b',
                r'\btheme\s*deck',
                r'\bstarter\s*deck',
                r'\benergy\s*cards?',
                r'\bbasic\s*energy',
            ],
            
            # Fake/proxy cards
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
            
            # Unclear/vague listings
            'vague': [
                r'\bmystery\s*box',
                r'\brandom\s*card',
                r'\bsurprise\s*pack',
                r'\bmixed\s*condition',
                r'\bunknown\s*condition',
                r'\bvintage\s*lot',
                r'\bold\s*cards?',
                r'\bmisc\b',
                r'\bmiscellaneous\b',
                r'\betc\b',
                r'\band\s*more\b',
                r'\bplus\s*extras?',
            ],
            
            # Wrong games/franchises
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
        
        # Patterns that indicate VALID single cards
        self.valid_patterns = [
            r'\bpsa\s*\d+\b',  # PSA graded
            r'\bbgs\s*\d+\b',  # BGS graded
            r'\bcgc\s*\d+\b',  # CGC graded
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
        ]
        
        # Pokemon name patterns (more comprehensive)
        self.pokemon_names = [
            # Gen 1
            'bulbasaur', 'ivysaur', 'venusaur', 'charmander', 'charmeleon', 'charizard',
            'squirtle', 'wartortle', 'blastoise', 'caterpie', 'metapod', 'butterfree',
            'weedle', 'kakuna', 'beedrill', 'pidgey', 'pidgeotto', 'pidgeot',
            'rattata', 'raticate', 'spearow', 'fearow', 'ekans', 'arbok',
            'pikachu', 'raichu', 'sandshrew', 'sandslash', 'nidoran', 'nidorina',
            'nidoqueen', 'nidorino', 'nidoking', 'clefairy', 'clefable', 'vulpix',
            'ninetales', 'jigglypuff', 'wigglytuff', 'zubat', 'golbat', 'oddish',
            'gloom', 'vileplume', 'paras', 'parasect', 'venonat', 'venomoth',
            'diglett', 'dugtrio', 'meowth', 'persian', 'psyduck', 'golduck',
            'mankey', 'primeape', 'growlithe', 'arcanine', 'poliwag', 'poliwhirl',
            'poliwrath', 'abra', 'kadabra', 'alakazam', 'machop', 'machoke',
            'machamp', 'bellsprout', 'weepinbell', 'victreebel', 'tentacool', 'tentacruel',
            'geodude', 'graveler', 'golem', 'ponyta', 'rapidash', 'slowpoke',
            'slowbro', 'magnemite', 'magneton', 'farfetchd', 'doduo', 'dodrio',
            'seel', 'dewgong', 'grimer', 'muk', 'shellder', 'cloyster',
            'gastly', 'haunter', 'gengar', 'onix', 'drowzee', 'hypno',
            'krabby', 'kingler', 'voltorb', 'electrode', 'exeggcute', 'exeggutor',
            'cubone', 'marowak', 'hitmonlee', 'hitmonchan', 'lickitung', 'koffing',
            'weezing', 'rhyhorn', 'rhydon', 'chansey', 'tangela', 'kangaskhan',
            'horsea', 'seadra', 'goldeen', 'seaking', 'staryu', 'starmie',
            'mr mime', 'scyther', 'jynx', 'electabuzz', 'magmar', 'pinsir',
            'tauros', 'magikarp', 'gyarados', 'lapras', 'ditto', 'eevee',
            'vaporeon', 'jolteon', 'flareon', 'porygon', 'omanyte', 'omastar',
            'kabuto', 'kabutops', 'aerodactyl', 'snorlax', 'articuno', 'zapdos',
            'moltres', 'dratini', 'dragonair', 'dragonite', 'mewtwo', 'mew',
            
            # Popular newer Pokemon
            'lugia', 'ho-oh', 'celebi', 'rayquaza', 'kyogre', 'groudon',
            'dialga', 'palkia', 'giratina', 'arceus', 'reshiram', 'zekrom',
            'kyurem', 'xerneas', 'yveltal', 'zygarde', 'solgaleo', 'lunala',
            'necrozma', 'zacian', 'zamazenta', 'eternatus', 'calyrex',
            
            # Eeveelutions
            'umbreon', 'espeon', 'leafeon', 'glaceon', 'sylveon',
            
            # Popular cards
            'lucario', 'garchomp', 'metagross', 'salamence', 'tyranitar',
            'dragonite', 'flygon', 'altaria', 'latios', 'latias'
        ]
        
        # Card type suffixes
        self.card_types = ['v', 'vmax', 'vstar', 'ex', 'gx', 'mega', 'prime', 'lv.x', 'break']
        
    def filter_listing(self, listing: Dict[str, Any], expected_card_name: str = None) -> FilterResult:
        """
        Filter a single listing for quality and relevance
        
        Args:
            listing: Dictionary containing listing data (title, price, etc.)
            expected_card_name: The specific card name we're searching for
            
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
        
        # Card name matching validation (if expected card name provided)
        if expected_card_name:
            expected_name_lower = expected_card_name.lower()
            if expected_name_lower not in title:
                return FilterResult(False, f"Card name mismatch: expected '{expected_card_name}' not found in title", 0.9)
        
        # Check for Pokemon names
        has_pokemon_name = False
        for pokemon in self.pokemon_names:
            if pokemon in title:
                has_pokemon_name = True
                break
        
        # Check for card types (V, VMAX, etc.)
        has_card_type = False
        for card_type in self.card_types:
            if f' {card_type}' in title or f'{card_type} ' in title:
                has_card_type = True
                break
        
        # Check for valid patterns
        valid_score = 0
        for pattern in self.valid_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                valid_score += 1
        
        # Calculate confidence based on multiple factors
        confidence = 0.5  # Base confidence
        
        if has_pokemon_name:
            confidence += 0.2
        if has_card_type:
            confidence += 0.1
        if valid_score > 0:
            confidence += min(valid_score * 0.1, 0.3)
        if 'pokemon' in title:
            confidence += 0.1
        if expected_card_name and expected_card_name.lower() in title:
            confidence += 0.2  # Bonus for matching expected card
        
        # Must have at least one positive indicator AND a Pokemon name or "pokemon" in title
        if not (has_pokemon_name or 'pokemon' in title):
            return FilterResult(False, "No Pokemon name or 'pokemon' found in title", 0.8)
        
        # Additional checks for edge cases
        if len(title) < 10:
            return FilterResult(False, "Title too short", 0.7)
        
        if title.count(' ') < 2:  # Very few words
            return FilterResult(False, "Title too simple", 0.6)
        
        return FilterResult(True, "Passed quality checks", confidence)
    
    def filter_listings_batch(self, listings: List[Dict[str, Any]], expected_card_name: str = None) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Filter a batch of listings
        
        Args:
            listings: List of listing dictionaries
            expected_card_name: The specific card name we're searching for
            
        Returns:
            Tuple of (valid_listings, rejection_stats)
        """
        valid_listings = []
        rejection_stats = {}
        
        for listing in listings:
            result = self.filter_listing(listing, expected_card_name)
            
            if result.is_valid:
                # Add quality score to listing
                listing['quality_score'] = result.confidence
                valid_listings.append(listing)
            else:
                # Track rejection reasons
                category = result.reason.split(' - ')[0] if ' - ' in result.reason else result.reason
                category = category.split(':')[0] if ':' in category else category  # Handle "Card name mismatch: ..."
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

def test_quality_filter():
    """Test the quality filter with sample titles"""
    filter = ListingQualityFilter()
    
    test_cases = [
        # Valid listings
        ("Pokemon Charizard V 079/073 Champions Path Secret Rare PSA 10", True, "Charizard"),
        ("Pikachu 25/102 Base Set Shadowless Near Mint", True, "Pikachu"),
        ("Rayquaza VMAX 111/203 Evolving Skies Holo Rare", True, "Rayquaza"),
        ("Umbreon Gold Star 17/17 POP Series 5 BGS 9", True, "Umbreon"),
        
        # Invalid listings - wrong card name
        ("2023 OBSIDEN FLAME SCARLET & VIOLET TYRANITAR EX 66/197 STAGE 2 NM", False, "Charizard"),
        ("Pokemon Blastoise V 009/189 Darkness Ablaze PSA 9", False, "Charizard"),
        
        # Invalid listings - other reasons
        ("34 Vintage Pokemon Card Lot Mixed Condition", False, "Charizard"),
        ("Pokemon Card Collection 100+ Cards Bulk Sale", False, "Charizard"),
        ("Charizard Damaged Creased Water Damage", False, "Charizard"),
        ("Yu-Gi-Oh Blue Eyes White Dragon", False, "Charizard"),
        ("Pokemon Card Sleeves and Binder", False, "Charizard"),
        ("Mystery Pokemon Card Pack Random", False, "Charizard"),
        ("Custom Fake Charizard Proxy Card", False, "Charizard"),
        ("PSA 7 (no specific card mentioned)", False, "Charizard"),
    ]
    
    print("🧪 Testing Quality Filter with Card Name Matching:")
    for title, expected, card_name in test_cases:
        result = filter.filter_listing({'title': title, 'price': 10.0}, card_name)
        status = "✅" if result.is_valid == expected else "❌"
        print(f"{status} [{card_name}] {title[:50]}... -> {result.is_valid} ({result.reason})")
    
    print("\n🧪 Testing without card name matching:")
    # Test a few without card name to ensure basic filtering still works
    basic_tests = [
        ("Pokemon Charizard V 079/073 Champions Path Secret Rare PSA 10", True),
        ("34 Vintage Pokemon Card Lot Mixed Condition", False),
        ("PSA 7 (no specific card mentioned)", False),
    ]
    
    for title, expected in basic_tests:
        result = filter.filter_listing({'title': title, 'price': 10.0})
        status = "✅" if result.is_valid == expected else "❌"
        print(f"{status} [No filter] {title[:50]}... -> {result.is_valid} ({result.reason})")

if __name__ == "__main__":
    test_quality_filter() 