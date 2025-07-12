# Main API client + fetch logic for Pokemon TCG API
import requests
import json
import os
import time
from pathlib import Path

class PokemonTCGClient:
    """Client for fetching data from Pokemon TCG API"""
    
    def __init__(self):
        self.base_url = "https://api.pokemontcg.io/v2"
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.sets_cache_file = self.data_dir / "sets_cache.json"
    
    def fetch_sets(self):
        """Fetch all Pokemon TCG sets from API"""
        print("Fetching Pokemon TCG sets...")
        
        try:
            # Make API request
            response = requests.get(f"{self.base_url}/sets")
            response.raise_for_status()
            
            sets_data = response.json()
            
            # Extract relevant fields for each set
            processed_sets = []
            for set_item in sets_data.get('data', []):
                processed_set = {
                    'id': set_item.get('id'),
                    'name': set_item.get('name'),
                    'releaseDate': set_item.get('releaseDate'),
                    'total': set_item.get('total'),
                    'printedTotal': set_item.get('printedTotal'),
                    'series': set_item.get('series')
                }
                processed_sets.append(processed_set)
            
            # Cache to file
            with open(self.sets_cache_file, 'w') as f:
                json.dump(processed_sets, f, indent=2)
            
            print(f"Successfully fetched and cached {len(processed_sets)} sets")
            return processed_sets
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
        except Exception as e:
            print(f"Error processing sets: {e}")
            return None
    
    def fetch_cards_for_set(self, set_id: str):
        """Fetch all cards for a specific set"""
        print(f"Fetching cards for set: {set_id}")
        
        try:
            # Make API request for cards in this set
            response = requests.get(f"{self.base_url}/cards", params={'q': f'set.id:{set_id}'})
            response.raise_for_status()
            
            cards_data = response.json()
            
            # Extract relevant fields for each card
            processed_cards = []
            for card_item in cards_data.get('data', []):
                processed_card = {
                    'name': card_item.get('name'),
                    'number': card_item.get('number'),
                    'rarity': card_item.get('rarity'),
                    'set_name': card_item.get('set', {}).get('name'),
                    'set_series': card_item.get('set', {}).get('series')
                }
                processed_cards.append(processed_card)
            
            # Cache to file
            cards_cache_file = self.data_dir / f"cards_{set_id}.json"
            with open(cards_cache_file, 'w') as f:
                json.dump(processed_cards, f, indent=2)
            
            print(f"  -> Cached {len(processed_cards)} cards for {set_id}")
            return processed_cards
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed for set {set_id}: {e}")
            return None
        except Exception as e:
            print(f"Error processing cards for set {set_id}: {e}")
            return None
    
    def fetch_all_cards(self, max_sets=None):
        """Fetch cards for all sets from cache"""
        # Load cached sets
        if not self.sets_cache_file.exists():
            print("No sets cache found. Run fetch_sets() first.")
            return
        
        with open(self.sets_cache_file, 'r') as f:
            sets = json.load(f)
        
        print(f"Fetching cards for {len(sets)} sets...")
        if max_sets:
            sets = sets[:max_sets]
            print(f"Limited to first {max_sets} sets for testing")
        
        total_cards = 0
        for i, set_data in enumerate(sets, 1):
            set_id = set_data['id']
            
            # Check if already cached
            cards_cache_file = self.data_dir / f"cards_{set_id}.json"
            if cards_cache_file.exists():
                print(f"[{i}/{len(sets)}] Skipping {set_id} (already cached)")
                continue
            
            cards = self.fetch_cards_for_set(set_id)
            if cards:
                total_cards += len(cards)
            
            # Small delay to be respectful to API
            time.sleep(0.1)
        
        print(f"Card fetching complete! Total cards cached: {total_cards}")

if __name__ == "__main__":
    client = PokemonTCGClient()
    print("Pokemon TCG API client initialized")
    
    # Example usage - can be modified for different tasks
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--sets":
            # Fetch sets
            sets = client.fetch_sets()
            if sets:
                print(f"Fetched {len(sets)} sets. Example: {sets[0]['name']}")
        elif sys.argv[1] == "--cards":
            # Fetch cards for all sets (or limited number)
            max_sets = int(sys.argv[2]) if len(sys.argv) > 2 else None
            client.fetch_all_cards(max_sets=max_sets)
        elif sys.argv[1] == "--single":
            # Fetch cards for a single set
            if len(sys.argv) > 2:
                set_id = sys.argv[2]
                cards = client.fetch_cards_for_set(set_id)
                if cards:
                    print(f"Fetched {len(cards)} cards for set {set_id}")
            else:
                print("Please provide set_id: python api_sets.py --single base1")
    else:
        # Default: test with first few sets
        print("Testing with first 3 sets...")
        client.fetch_all_cards(max_sets=3) 