# Pushes parsed sets/cards into Supabase
import sys
import os
import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any

# Add parent directory to path to import supabase_client
sys.path.append(str(Path(__file__).parent.parent))
from supabase_client import supabase

def load_cached_sets() -> List[Dict]:
    """Load cached sets data"""
    sets_cache_file = Path(__file__).parent / "data" / "sets_cache.json"
    if not sets_cache_file.exists():
        print("No sets cache found. Run api_sets.py --sets first.")
        return []
    
    with open(sets_cache_file, 'r') as f:
        return json.load(f)

def load_cached_cards(set_id: str) -> List[Dict]:
    """Load cached cards for a specific set"""
    cards_cache_file = Path(__file__).parent / "data" / f"cards_{set_id}.json"
    if not cards_cache_file.exists():
        return []
    
    with open(cards_cache_file, 'r') as f:
        return json.load(f)

def build_rarity_breakdown(cards: List[Dict]) -> Dict[str, int]:
    """Build rarity breakdown from cards list"""
    if not cards:
        return {}
    
    rarity_counts = Counter(card.get('rarity', 'Unknown') for card in cards)
    return dict(rarity_counts)

def calculate_secret_rare_count(cards: List[Dict], total_cards: int) -> int:
    """Calculate number of secret rare cards (cards with numbers beyond base set)"""
    if not cards or not total_cards:
        return 0
    
    secret_count = 0
    for card in cards:
        card_number = card.get('number', '')
        # Try to parse number - secret rares typically have numbers > total
        try:
            if card_number.isdigit() and int(card_number) > total_cards:
                secret_count += 1
        except:
            continue
    
    return secret_count

def prepare_set_data(set_info: Dict, cards: List[Dict]) -> Dict:
    """Prepare set data for Supabase insertion"""
    total_cards = set_info.get('total', 0)
    printed_total = set_info.get('printedTotal', 0)
    
    return {
        'set_name': set_info.get('name'),
        'release_date': set_info.get('releaseDate'),
        'series': set_info.get('series'),
        'total_cards': total_cards,
        'base_cards': printed_total,
        'secret_rare_count': calculate_secret_rare_count(cards, printed_total),
        'structure': {
            'total': total_cards,
            'printed': printed_total,
            'api_id': set_info.get('id')
        },
        'products': {},  # Can be enriched later
        'known_pull_rates': {},  # Can be enriched later  
        'rarity_breakdown': build_rarity_breakdown(cards)
    }

def prepare_cards_data(cards: List[Dict]) -> List[Dict]:
    """Prepare cards data for Supabase insertion"""
    prepared_cards = []
    
    for card in cards:
        prepared_card = {
            'card_name': card.get('name'),
            'card_number': card.get('number'),
            'set_name': card.get('set_name'),
            'rarity': card.get('rarity') or 'Unknown'  # Handle null rarity values
        }
        prepared_cards.append(prepared_card)
    
    return prepared_cards

def batch_data(data: List[Any], batch_size: int = 100) -> List[List[Any]]:
    """Split data into batches for processing"""
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

def sync_sets_to_supabase():
    """Sync Pokemon sets data to Supabase"""
    print("Syncing sets to Supabase...")
    
    # Load cached sets
    sets = load_cached_sets()
    if not sets:
        return
    
    processed_sets = []
    
    for set_info in sets:
        set_id = set_info.get('id')
        print(f"Processing set: {set_info.get('name')} ({set_id})")
        
        # Load cards for this set
        cards = load_cached_cards(set_id)
        
        # Prepare set data
        set_data = prepare_set_data(set_info, cards)
        processed_sets.append(set_data)
    
    print(f"Prepared {len(processed_sets)} sets for insertion")
    
    # Insert in batches
    success_count = 0
    for batch in batch_data(processed_sets, batch_size=50):
        try:
            result = supabase.table("pokemon_sets").upsert(batch).execute()
            success_count += len(batch)
            print(f"  -> Inserted batch of {len(batch)} sets")
        except Exception as e:
            print(f"  -> Error inserting sets batch: {e}")
    
    print(f"Successfully synced {success_count} sets to Supabase")

def sync_cards_to_supabase():
    """Sync Pokemon cards data to Supabase"""
    print("Syncing cards to Supabase...")
    
    # Load cached sets to get list of sets with cards
    sets = load_cached_sets()
    if not sets:
        return
    
    total_cards = 0
    
    for set_info in sets:
        set_id = set_info.get('id')
        set_name = set_info.get('name')
        
        # Load cards for this set
        cards = load_cached_cards(set_id)
        if not cards:
            print(f"  -> No cards cached for {set_name} ({set_id})")
            continue
        
        print(f"Processing cards for: {set_name} ({len(cards)} cards)")
        
        # Prepare cards data
        prepared_cards = prepare_cards_data(cards)
        
        # Insert in batches
        for batch in batch_data(prepared_cards, batch_size=100):
            try:
                result = supabase.table("pokemon_cards").upsert(batch).execute()
                total_cards += len(batch)
                print(f"  -> Inserted batch of {len(batch)} cards")
            except Exception as e:
                print(f"  -> Error inserting cards batch: {e}")
    
    print(f"Successfully synced {total_cards} cards to Supabase")

def sync_all():
    """Sync both sets and cards to Supabase"""
    print("Starting full sync to Supabase...")
    sync_sets_to_supabase()
    print()
    sync_cards_to_supabase()
    print("Sync complete!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--sets":
            sync_sets_to_supabase()
        elif sys.argv[1] == "--cards":
            sync_cards_to_supabase()
        elif sys.argv[1] == "--all":
            sync_all()
        else:
            print("Usage: python sync_to_supabase.py [--sets|--cards|--all]")
    else:
        # Default: sync both
        sync_all() 