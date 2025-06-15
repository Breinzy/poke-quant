# Shared formatting or ID logic
"""
Utility functions for Pokemon TCG data processing
"""

import re
from typing import List, Dict, Any

def slugify_set_name(set_name: str) -> str:
    """Convert set name to URL-friendly slug"""
    return re.sub(r'[^a-zA-Z0-9]+', '-', set_name.lower()).strip('-')

def normalize_rarity(rarity: str) -> str:
    """Normalize rarity string to standard format"""
    from constants import RARITY_MAPPINGS
    return RARITY_MAPPINGS.get(rarity, rarity.lower())

def batch_data(data: List[Any], batch_size: int = 100) -> List[List[Any]]:
    """Split data into batches for processing"""
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

def deduplicate_cards(cards: List[Dict]) -> List[Dict]:
    """Remove duplicate cards based on card_number + set_name"""
    seen = set()
    unique_cards = []
    
    for card in cards:
        key = f"{card.get('number', '')}-{card.get('set', {}).get('name', '')}"
        if key not in seen:
            seen.add(key)
            unique_cards.append(card)
    
    return unique_cards 