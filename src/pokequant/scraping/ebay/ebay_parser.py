"""
eBay Parser Module
Parses raw HTML to extract listing data (title, price, date, etc.)
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import re
from datetime import datetime
from listing_quality_filter_fixed import ListingQualityFilterFixed

class eBayParser:
    """Parses eBay listing HTML to extract structured data"""
    
    def __init__(self, enable_quality_filter: bool = True):
        # Initialize quality filter
        self.quality_filter = ListingQualityFilterFixed() if enable_quality_filter else None
        
        # Patterns for extracting card info from titles
        self.grading_pattern = re.compile(r'\b(PSA|BGS|CGC|CBCS)\s*(\d+(?:\.\d+)?)\b', re.IGNORECASE)
        self.card_number_pattern = re.compile(r'\b(\d+)/(\d+)\b')
        self.set_patterns = {
            'base set': r'\b(base\s*set|1st\s*edition)\b',
            'evolving skies': r'\b(evolving\s*skies|ES)\b',
            'brilliant stars': r'\b(brilliant\s*stars|BS)\b',
            'darkness ablaze': r'\b(darkness\s*ablaze|DAB)\b',
            'sword shield': r'\b(sword\s*&?\s*shield|SWSH)\b',
            'celebrations': r'\b(celebrations|CELEB)\b',
            'fusion strike': r'\b(fusion\s*strike|FST)\b'
        }
    
    def parse_listing_html(self, html: str, expected_card_name: str = None, is_sealed_product: bool = False) -> List[Dict[str, Any]]:
        """Parse HTML page and extract all listings"""
        soup = BeautifulSoup(html, 'html.parser')
        print("🔍 Parsing eBay HTML...")
        
        # Find the main results container first - NEW eBay structure
        main_container = soup.find('ul', {'class': re.compile(r'srp-results')})
        if not main_container:
            main_container = soup.find('div', {'id': 'srp-river-results'})
        
        if main_container:
            # Look for listing items within the main container (NEW structure)
            listings = main_container.find_all('li', {'class': re.compile(r's-card')})
            if not listings:
                # Fallback: look for old li.s-item elements
                listings = main_container.find_all('li', {'class': re.compile(r's-item')})
            if not listings:
                # Fallback: look for div.s-item elements (old structure)
                listings = main_container.find_all('div', {'class': re.compile(r's-item')})
            print(f"📊 Found {len(listings)} listing containers in main results")
        else:
            # Fallback to global search
            listings = soup.find_all('li', {'class': re.compile(r's-card')})
            if not listings:
                listings = soup.find_all('li', {'class': re.compile(r's-item')})
            if not listings:
                listings = soup.find_all('div', {'class': re.compile(r's-item')})
            print(f"📊 Found {len(listings)} listing containers (fallback method)")
        
        parsed_listings = []
        
        for i, listing in enumerate(listings):
            try:
                listing_data = self.extract_listing_data(listing)
                if listing_data and listing_data.get('title'):  # Only include if we got valid data
                    # Parse title for card metadata
                    card_info = self.parse_title_for_card_info(listing_data['title'])
                    listing_data.update(card_info)
                    parsed_listings.append(listing_data)
                    
            except Exception as e:
                print(f"⚠️ Error parsing listing {i}: {e}")
                continue
        
        # Apply quality filter if enabled
        if self.quality_filter:
            original_count = len(parsed_listings)
            parsed_listings, rejection_stats = self.quality_filter.filter_listings_batch(parsed_listings, expected_card_name, is_sealed_product)
            if expected_card_name:
                item_type = "sealed product" if is_sealed_product else "card"
                print(f"🎯 Filtering for {item_type}: {expected_card_name}")
            self.quality_filter.print_filter_summary(original_count, len(parsed_listings), rejection_stats)
        else:
            print(f"✅ Parsed {len(parsed_listings)} listings from {len(listings)} containers (no quality filter)")
        
        return parsed_listings
    
    def extract_listing_data(self, listing_element) -> Dict[str, Any]:
        """Extract data from individual listing element"""
        data = {
            'title': '',
            'price': 0.0,
            'sold_date': None,
            'listing_url': '',
            'image_url': '',
            'is_auction': False,
            'bids': 0,
            'condition': '',
            'shipping': ''
        }
        
        try:
            # Check if this is the new s-card structure or old s-item structure
            is_new_structure = 's-card' in listing_element.get('class', [])
            
            if is_new_structure:
                # NEW eBay structure (s-card)
                
                # Extract title
                title_elem = listing_element.find('div', class_='s-card__title')
                if title_elem:
                    title_span = title_elem.find('span', class_='su-styled-text')
                    if title_span:
                        data['title'] = title_span.get_text(strip=True)
                
                # Extract price
                price_elem = listing_element.find('span', class_='s-card__price')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    data['price'] = self.clean_price(price_text)
                
                # Extract listing URL
                link_elem = listing_element.find('a', class_='su-link')
                if link_elem:
                    data['listing_url'] = link_elem.get('href', '')
                
                # Extract condition from subtitle
                subtitle_elem = listing_element.find('div', class_='s-card__subtitle')
                if subtitle_elem:
                    condition_span = subtitle_elem.find('span', class_='su-styled-text')
                    if condition_span:
                        data['condition'] = condition_span.get_text(strip=True)
                
                # Check for auction indicators in attribute rows
                attribute_rows = listing_element.find_all('div', class_='s-card__attribute-row')
                for row in attribute_rows:
                    text = row.get_text(strip=True).lower()
                    if 'bid' in text or 'auction' in text:
                        data['is_auction'] = True
                        # Extract number of bids
                        bids_match = re.search(r'(\d+)\s+bid', text)
                        if bids_match:
                            data['bids'] = int(bids_match.group(1))
                    elif 'delivery' in text or 'shipping' in text:
                        data['shipping'] = row.get_text(strip=True)
                
            else:
                # OLD eBay structure (s-item) - fallback
                
                # Extract title
                title_elem = listing_element.find('div', class_='s-item__title')
                if title_elem:
                    title_span = title_elem.find('span')
                    if title_span:
                        data['title'] = title_span.get_text(strip=True)
                
                # Extract price
                price_elem = listing_element.find('span', class_='s-item__price')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    data['price'] = self.clean_price(price_text)
                
                # Extract listing URL
                link_elem = listing_element.find('a', class_='s-item__link')
                if link_elem:
                    data['listing_url'] = link_elem.get('href', '')
                
                # Extract condition from subtitle
                subtitle_elem = listing_element.find('div', class_='s-item__subtitle')
                if subtitle_elem:
                    condition_span = subtitle_elem.find('span', class_='SECONDARY_INFO')
                    if condition_span:
                        data['condition'] = condition_span.get_text(strip=True)
                
                # Check if auction vs Buy It Now
                purchase_options = listing_element.find('span', class_='s-item__purchase-options')
                if purchase_options:
                    options_text = purchase_options.get_text(strip=True).lower()
                    data['is_auction'] = 'bid' in options_text or 'auction' in options_text
                
                # Extract bids (for auctions)
                bids_elem = listing_element.find('span', class_='s-item__bids')
                if bids_elem:
                    bids_text = bids_elem.get_text(strip=True)
                    bids_match = re.search(r'(\d+)', bids_text)
                    if bids_match:
                        data['bids'] = int(bids_match.group(1))
                
                # Extract shipping info
                shipping_elem = listing_element.find('span', class_='s-item__shipping')
                if shipping_elem:
                    data['shipping'] = shipping_elem.get_text(strip=True)
            
            # Extract image URL (common for both structures)
            img_elem = listing_element.find('img')
            if img_elem:
                # Try to get the full-size image URL
                img_url = img_elem.get('data-defer-load') or img_elem.get('src', '')
                data['image_url'] = img_url
            
            # Extract sold date (for sold listings) - common for both structures
            data['sold_date'] = self.get_sold_date_from_listing(listing_element)
            
        except Exception as e:
            print(f"⚠️ Error extracting listing data: {e}")
        
        return data
    
    def parse_title_for_card_info(self, title: str) -> Dict[str, Any]:
        """Extract card metadata from eBay title"""
        card_info = {
            'card_name': '',
            'card_number': '',
            'set_name': '',
            'is_graded': False,
            'grading_company': '',
            'grade': ''
        }
        
        if not title:
            return card_info
        
        title_lower = title.lower()
        
        # Extract grading information
        grading_match = self.grading_pattern.search(title)
        if grading_match:
            card_info['is_graded'] = True
            card_info['grading_company'] = grading_match.group(1).upper()
            card_info['grade'] = grading_match.group(2)
        
        # Extract card number (e.g., "25/102", "195/203")
        number_match = self.card_number_pattern.search(title)
        if number_match:
            card_info['card_number'] = f"{number_match.group(1)}/{number_match.group(2)}"
        
        # Extract set name
        for set_name, pattern in self.set_patterns.items():
            if re.search(pattern, title_lower):
                card_info['set_name'] = set_name
                break
        
        # Extract Pokémon name (basic approach)
        pokemon_names = [
            'charizard', 'pikachu', 'rayquaza', 'lugia', 'mewtwo',
            'blastoise', 'venusaur', 'gyarados', 'dragonite', 'mew',
            'eevee', 'umbreon', 'espeon', 'vaporeon', 'flareon',
            'jolteon', 'leafeon', 'glaceon', 'sylveon'
        ]
        
        for pokemon in pokemon_names:
            if pokemon in title_lower:
                card_info['card_name'] = pokemon.title()
                break
        
        # If no specific Pokémon found, try to extract from title
        if not card_info['card_name']:
            # Look for common card name patterns
            name_patterns = [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:V|EX|GX|VMAX|VSTAR)\b',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+Pokemon\b',
                r'Pokemon\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, title)
                if match:
                    card_info['card_name'] = match.group(1).strip()
                    break
        
        return card_info
    
    def clean_price(self, price_text: str) -> float:
        """Clean and convert price string to float"""
        if not price_text:
            return 0.0
        
        # Handle price ranges (take the first/lower price)
        if 'to' in price_text.lower():
            price_text = price_text.split('to')[0]
        
        # Remove everything except digits, dots, and commas
        clean_price = re.sub(r'[^\d.,]', '', price_text)
        
        # Handle comma as thousands separator
        if ',' in clean_price and '.' in clean_price:
            # Format like "1,234.56"
            clean_price = clean_price.replace(',', '')
        elif ',' in clean_price:
            # Could be "1,234" (thousands) or "12,34" (European decimal)
            if len(clean_price.split(',')[1]) == 2:
                # Likely European decimal format
                clean_price = clean_price.replace(',', '.')
            else:
                # Likely thousands separator
                clean_price = clean_price.replace(',', '')
        
        try:
            return float(clean_price)
        except ValueError:
            print(f"⚠️ Could not parse price: {price_text}")
            return 0.0
    
    def get_sold_date_from_listing(self, listing_element) -> Optional[str]:
        """Extract sold date from listing if available"""
        try:
            # Check if this is the new s-card structure
            is_new_structure = 's-card' in listing_element.get('class', [])
            
            if is_new_structure:
                # NEW eBay structure (s-card) - look in caption area
                caption_elem = listing_element.find('div', class_='s-card__caption')
                if caption_elem:
                    sold_span = caption_elem.find('span', class_='su-styled-text')
                    if sold_span:
                        date_text = sold_span.get_text(strip=True)
                        if 'sold' in date_text.lower():
                            return date_text
            else:
                # OLD eBay structure (s-item) - use existing selectors
                date_selectors = [
                    'span.s-item__ended-date',
                    'span.s-item__time-left',
                    'div.s-item__detail--primary',
                    'span.s-item__time-end',
                    'span[class*="sold"]',
                    'span[class*="date"]'
                ]
                
                for selector in date_selectors:
                    date_elem = listing_element.select_one(selector)
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        
                        # Look for patterns like "Sold Dec 15" or "Ended Dec 15, 2023"
                        if any(word in date_text.lower() for word in ['sold', 'ended']):
                            return date_text
            
            # Alternative: look in the entire listing text for sold date patterns
            listing_text = listing_element.get_text()
            sold_patterns = [
                r'Sold\s+([A-Za-z]{3}\s+\d{1,2}(?:,\s*\d{4})?)',
                r'Ended\s+([A-Za-z]{3}\s+\d{1,2}(?:,\s*\d{4})?)',
                r'(\d{1,2}/\d{1,2}/\d{2,4})\s*sold',
                r'sold\s*(\d{1,2}/\d{1,2}/\d{2,4})'
            ]
            
            for pattern in sold_patterns:
                match = re.search(pattern, listing_text, re.IGNORECASE)
                if match:
                    return match.group(1) if match.lastindex else match.group(0)
            
        except Exception as e:
            print(f"⚠️ Error extracting sold date: {e}")
        
        return None 