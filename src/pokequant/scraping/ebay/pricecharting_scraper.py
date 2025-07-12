#!/usr/bin/env python3
"""
PriceCharting Scraper
Scrapes historical pricing data from PriceCharting for Pokemon cards and sealed products
"""

import sys
import os
import time
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

class PriceChartingScraper:
    """Scraper for PriceCharting historical data"""
    
    def __init__(self):
        self.base_url = "https://www.pricecharting.com"
        self.session = requests.Session()
        
        # Headers to mimic browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Rate limiting
        self.delay_between_requests = 2.0
        self.last_request_time = 0
        
    def _get_card_search_term(self, card: Dict[str, Any]) -> str:
        """Generate proper search term for a card: card name + card number"""
        card_name = card.get('card_name', '').strip()
        card_number = card.get('card_number', '').strip()
        
        if card_name and card_number:
            # For PriceCharting: "Charizard V 154" not "Charizard V #154"
            return f"{card_name} {card_number}"
        elif card_name:
            return card_name
        else:
            return "Unknown Card"
    
    def search_card_on_pricecharting(self, card_name: str, set_name: str = None, card_data: Dict[str, Any] = None) -> Optional[str]:
        """Search for a card on PriceCharting and return the URL to the product page with price chart"""
        
        # If we have full card data, use it to build proper search term
        if card_data:
            query = self._get_card_search_term(card_data)
        else:
            # Fallback to just card name
            query = card_name.strip()
            
        search_url = f"{self.base_url}/search-products?q={query}&console=&genre=TCG+Card"
        
        print(f"🔍 Searching PriceCharting for: {query}")
        
        try:
            self._rate_limit()
            response = self.session.get(search_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for table links (marketplace offers) and extract product IDs
                table_links = soup.select('table a')
                
                if table_links:
                    print(f"  🔍 Found {len(table_links)} marketplace offers")
                    
                    for link in table_links:
                        href = link.get('href', '')
                        
                        # Extract product ID from offers URL: /offers?product=3188378
                        if '/offers?product=' in href:
                            product_id = href.split('product=')[1].split('&')[0]
                            
                            # Construct the actual product page URL
                            # PriceCharting product pages are typically: /game/pokemon-tcg/product-name
                            # But we can also try: /console/product-id or /product/product-id
                            possible_urls = [
                                f"{self.base_url}/console/{product_id}",
                                f"{self.base_url}/product/{product_id}",
                                f"{self.base_url}/game/{product_id}"
                            ]
                            
                            # Try each possible URL format
                            for test_url in possible_urls:
                                try:
                                    self._rate_limit()
                                    test_response = self.session.get(test_url)
                                    
                                    if test_response.status_code == 200:
                                        # Check if this page has price chart data
                                        test_soup = BeautifulSoup(test_response.content, 'html.parser')
                                        
                                        # Look for indicators of a price chart page
                                        chart_indicators = [
                                            'chart',
                                            'price-history',
                                            'chartData',
                                            'historical',
                                            'graph'
                                        ]
                                        
                                        page_text = test_response.text.lower()
                                        has_chart = any(indicator in page_text for indicator in chart_indicators)
                                        
                                        if has_chart:
                                            print(f"  ✅ Found product page with chart: {test_url}")
                                            return test_url
                                            
                                except Exception as e:
                                    continue
                
                # If no direct product pages found, look for any other game/product links
                all_links = soup.find_all('a')
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text().lower()
                    
                    # Look for product page patterns
                    if (href and 
                        ('/game/' in href or '/games/' in href or '/console/' in href) and
                        not '/offers' in href):
                        
                        # Check if this looks like our search term
                        search_words = query.lower().split()
                        matches = sum(1 for word in search_words if word in text)
                        
                        if matches >= len(search_words) - 1:
                            full_url = self.base_url + href if href.startswith('/') else href
                            print(f"  ✅ Found product page: {full_url}")
                            return full_url
                
                print(f"  ⚠️ No product page found for {query}")
                return None
                
        except Exception as e:
            print(f"  ❌ Error searching for {query}: {e}")
            return None
    
    def search_sealed_product_on_pricecharting(self, product_name: str) -> Optional[str]:
        """Search for a sealed product on PriceCharting and return the URL to the product page"""
        
        # Extract set name and product type for better search
        search_query = product_name.replace("Pokemon", "").replace("pokemon", "").strip()
        search_url = f"{self.base_url}/search-products?q={search_query}&console=&genre=TCG+Card"
        
        print(f"📦 Searching PriceCharting for sealed product: {search_query}")
        
        try:
            self._rate_limit()
            response = self.session.get(search_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for table links (marketplace offers) and extract product IDs
                table_links = soup.select('table a')
                
                if table_links:
                    print(f"  📦 Found {len(table_links)} marketplace offers")
                    
                    for link in table_links:
                        href = link.get('href', '')
                        
                        # Extract product ID from offers URL
                        if '/offers?product=' in href:
                            product_id = href.split('product=')[1].split('&')[0]
                            
                            # Try different product page URL formats
                            possible_urls = [
                                f"{self.base_url}/console/{product_id}",
                                f"{self.base_url}/product/{product_id}",
                                f"{self.base_url}/game/{product_id}"
                            ]
                            
                            for test_url in possible_urls:
                                try:
                                    self._rate_limit()
                                    test_response = self.session.get(test_url)
                                    
                                    if test_response.status_code == 200:
                                        # Check if this page has price chart data
                                        page_text = test_response.text.lower()
                                        has_chart = any(indicator in page_text for indicator in ['chart', 'price-history', 'chartdata'])
                                        
                                        if has_chart:
                                            print(f"  ✅ Found sealed product page: {test_url}")
                                            return test_url
                                            
                                except Exception as e:
                                    continue
                
                print(f"  ⚠️ No product page found for {search_query}")
                return None
                
        except Exception as e:
            print(f"  ❌ Error searching for {product_name}: {e}")
            return None
    
    def scrape_price_history(self, pricecharting_url: str) -> Dict[str, Any]:
        """Scrape price history chart data from a PriceCharting product page"""
        
        print(f"📈 Scraping price chart from: {pricecharting_url}")
        
        try:
            self._rate_limit()
            response = self.session.get(pricecharting_url)
            
            if response.status_code != 200:
                print(f"  ❌ Failed to load page: {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            html_content = response.text
            
            # Extract product info
            product_info = self._extract_product_info(soup)
            
            # Extract current prices from the page
            current_prices = self._extract_current_prices_from_chart_page(soup)
            
            # Extract historical chart data from JavaScript
            chart_data = self._extract_chart_data_advanced(html_content)
            
            # Extract any price tables or grids
            price_tables = self._extract_price_tables(soup)
            
            result = {
                'url': pricecharting_url,
                'product_info': product_info,
                'current_prices': current_prices,
                'historical_chart_data': chart_data,
                'price_tables': price_tables,
                'scraped_at': datetime.now().isoformat()
            }
            
            print(f"  ✅ Successfully scraped chart data")
            print(f"    Current prices: {len(current_prices)} found")
            print(f"    Chart data points: {len(chart_data)}")
            print(f"    Price tables: {len(price_tables)}")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error scraping price history: {e}")
            return {}
    
    def _extract_current_prices_from_chart_page(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Extract current prices from product chart page"""
        prices = {}
        
        try:
            # Look for price display elements on chart pages
            price_selectors = [
                '.price-display',
                '.current-price',
                '.price-value',
                'span[class*="price"]',
                'div[class*="price"]',
                '.loose-price',
                '.cib-price',
                '.new-price'
            ]
            
            for selector in price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    price_match = re.search(r'\$(\d+\.?\d*)', text)
                    
                    if price_match:
                        price = float(price_match.group(1))
                        
                        # Filter out subscription fees and unrealistic prices
                        if price == 6.0 or price < 1.0 or price > 100000:
                            continue
                        
                        # Determine condition from context
                        context = element.get('class', []) + [element.parent.get_text().lower() if element.parent else ""]
                        context_text = " ".join(str(c) for c in context).lower()
                        
                        if 'loose' in context_text or 'ungraded' in context_text:
                            prices['loose'] = price
                        elif 'cib' in context_text or 'complete' in context_text:
                            prices['complete'] = price
                        elif 'new' in context_text or 'sealed' in context_text:
                            prices['new'] = price
                        elif 'graded' in context_text:
                            prices['graded'] = price
                        else:
                            prices['current'] = price
            
            # Also look for any visible price numbers in tables, but filter out subscription fees
            tables = soup.find_all('table')
            for table in tables:
                cells = table.find_all(['td', 'th'])
                for cell in cells:
                    text = cell.get_text().strip()
                    
                    # Skip cells that contain subscription-related text
                    if 'subscribe' in text.lower() or 'month' in text.lower():
                        continue
                        
                    price_match = re.search(r'\$(\d+\.?\d*)', text)
                    if price_match:
                        price = float(price_match.group(1))
                        
                        # Filter out subscription fees and unrealistic prices
                        if price == 6.0 or price < 1.0 or price > 100000:
                            continue
                            
                        prices[f'table_price_{len(prices)}'] = price
                        
        except Exception as e:
            print(f"    ⚠️ Error extracting current prices: {e}")
        
        return prices
    
    def _extract_chart_data_advanced(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract historical chart data from JavaScript with proper date-price parsing"""
        chart_data = []
        
        try:
            # Look for timestamp-price pairs in the format [timestamp, price]
            timestamp_pattern = r'\[(\d{13}),(\d+)\]'
            matches = re.findall(timestamp_pattern, html_content)
            
            if matches:
                print(f"    📊 Found {len(matches)} timestamp-price pairs")
                
                for timestamp_str, price_str in matches:
                    try:
                        timestamp = int(timestamp_str)
                        price_cents = int(price_str)
                        
                        # Convert timestamp to date
                        from datetime import datetime
                        date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                        
                        # Convert price from cents to dollars
                        price_dollars = price_cents / 100.0
                        
                        # Skip zero prices (often invalid data points)
                        if price_dollars > 0:
                            chart_entry = {
                                'timestamp': timestamp,
                                'date': date,
                                'price': price_dollars,
                                'raw_price_cents': price_cents
                            }
                            chart_data.append(chart_entry)
                    except (ValueError, TypeError):
                        continue
                
                print(f"    📈 Extracted {len(chart_data)} valid price points")
                return chart_data
            
            # Fallback: Look for other JavaScript variable patterns (original logic)
            js_patterns = [
                r'chartData\s*=\s*(\[.*?\]);',
                r'priceData\s*=\s*(\[.*?\]);',
                r'historyData\s*=\s*(\[.*?\]);',
                r'data:\s*(\[.*?\])',
                r'series:\s*\[\s*{\s*data:\s*(\[.*?\])',
                r'"data":\s*(\[.*?\])',
                r'price_history\s*=\s*(\[.*?\]);'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        import json
                        data = json.loads(match)
                        
                        if isinstance(data, list) and len(data) > 0:
                            # Check if this looks like chart data
                            first_item = data[0]
                            if isinstance(first_item, (list, dict)):
                                # Parse the data to extract proper date-price pairs
                                parsed_data = self._parse_historical_data_array(data)
                                chart_data.extend(parsed_data)
                                print(f"    📊 Found chart data pattern: {len(parsed_data)} valid data points")
                                break
                                
                    except json.JSONDecodeError:
                        continue
            
            # Look for embedded data in script tags
            script_pattern = r'<script[^>]*>(.*?)</script>'
            scripts = re.findall(script_pattern, html_content, re.DOTALL)
            
            for script in scripts:
                if 'chart' in script.lower() or 'price' in script.lower():
                    # Look for timestamp-price patterns in this specific script
                    script_matches = re.findall(timestamp_pattern, script)
                    if script_matches and not chart_data:  # Only if we haven't found data yet
                        for timestamp_str, price_str in script_matches:
                            try:
                                timestamp = int(timestamp_str)
                                price_cents = int(price_str)
                                
                                from datetime import datetime
                                date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                                price_dollars = price_cents / 100.0
                                
                                if price_dollars > 0:
                                    chart_data.append({
                                        'timestamp': timestamp,
                                        'date': date,
                                        'price': price_dollars,
                                        'raw_price_cents': price_cents
                                    })
                            except (ValueError, TypeError):
                                continue
                        
                        if chart_data:
                            print(f"    📊 Found {len(chart_data)} chart points in script")
                            break
                        
        except Exception as e:
            print(f"    ⚠️ Error extracting chart data: {e}")
        
        return chart_data
    
    def _parse_historical_data_array(self, data_array: List[Any]) -> List[Dict[str, Any]]:
        """Parse historical data array to extract clean date-price pairs"""
        parsed_data = []
        
        try:
            for item in data_array:
                if isinstance(item, list):
                    parsed_entry = self._parse_single_data_entry(item)
                    if parsed_entry:
                        parsed_data.append(parsed_entry)
                elif isinstance(item, dict):
                    # Handle dictionary format
                    if 'date' in item and 'price' in item:
                        try:
                            price = float(re.search(r'(\d+\.?\d*)', str(item['price'])).group(1))
                            if price != 6.0 and price >= 1.0 and price <= 100000:
                                parsed_data.append({
                                    'date': item['date'],
                                    'price': price,
                                    'raw_data': item
                                })
                        except:
                            continue
        except Exception as e:
            print(f"    ⚠️ Error parsing historical data array: {e}")
        
        return parsed_data
    
    def _parse_single_data_entry(self, entry_array: List[Any]) -> Dict[str, Any]:
        """Parse a single data entry to extract date and price"""
        
        try:
            if len(entry_array) < 4:
                return None
            
            # Expected format: [date, subscription_msg, description, price, report_button]
            date_str = str(entry_array[0]).strip()
            price_str = str(entry_array[3]).strip()
            description = str(entry_array[2]).strip()
            
            # Validate date format (YYYY-MM-DD or similar)
            if not re.match(r'20\d{2}-\d{1,2}-\d{1,2}', date_str):
                return None
            
            # Extract price
            price_match = re.search(r'\$?(\d+\.?\d*)', price_str)
            if not price_match:
                return None
            
            price = float(price_match.group(1))
            
            # Filter out subscription fees and unrealistic prices
            if price == 6.0 or price < 1.0 or price > 100000:
                return None
            
            # Check if description contains subscription-related text
            if 'subscribe' in description.lower() or '$6/month' in description.lower():
                return None
            
            return {
                'date': date_str,
                'price': price,
                'description': description,
                'raw_data': entry_array
            }
            
        except Exception as e:
            return None
    
    def _extract_price_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract any price tables or grids from the page with proper filtering"""
        tables_data = []
        
        try:
            tables = soup.find_all('table')
            
            for i, table in enumerate(tables):
                table_data = {
                    'table_index': i,
                    'headers': [],
                    'rows': [],
                    'clean_price_data': []
                }
                
                # Extract headers
                headers = table.find_all(['th', 'thead'])
                for header in headers:
                    text = header.get_text().strip()
                    if text and 'subscribe' not in text.lower():
                        table_data['headers'].append(text)
                
                # Extract rows
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = []
                    clean_row_data = {}
                    
                    for cell in cells:
                        text = cell.get_text().strip()
                        row_data.append(text)
                    
                    if row_data and any(text for text in row_data):
                        # Try to extract date-price pairs from this row
                        date_found = None
                        price_found = None
                        
                        for cell_text in row_data:
                            # Look for date
                            if re.match(r'20\d{2}-\d{1,2}-\d{1,2}', cell_text):
                                date_found = cell_text
                            
                            # Look for price (but not $6)
                            price_match = re.search(r'\$(\d+\.?\d*)', cell_text)
                            if price_match:
                                price = float(price_match.group(1))
                                if price != 6.0 and price >= 1.0 and price <= 100000:
                                    price_found = price
                        
                        table_data['rows'].append(row_data)
                        
                        if date_found and price_found:
                            clean_row_data = {
                                'date': date_found,
                                'price': price_found
                            }
                            table_data['clean_price_data'].append(clean_row_data)
                
                if table_data['rows']:
                    tables_data.append(table_data)
                    
        except Exception as e:
            print(f"    ⚠️ Error extracting price tables: {e}")
        
        return tables_data
    
    def _extract_product_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product information"""
        info = {}
        
        try:
            # Product title
            title_element = soup.find('h1')
            if title_element:
                info['title'] = title_element.get_text().strip()
            
            # Product details
            details = soup.find_all('div', class_='product-detail')
            for detail in details:
                text = detail.get_text().strip()
                if ':' in text:
                    key, value = text.split(':', 1)
                    info[key.strip().lower()] = value.strip()
                    
        except Exception as e:
            print(f"    ⚠️ Error extracting product info: {e}")
        
        return info
    
    def _rate_limit(self):
        """Ensure we don't make requests too quickly"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay_between_requests:
            sleep_time = self.delay_between_requests - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def scrape_curated_items_historical_data(self, cards: List[Dict[str, Any]], 
                                           sealed_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Scrape historical data for all curated items"""
        
        print("📊 Starting PriceCharting historical data scraping...")
        
        results = {
            'cards': [],
            'sealed_products': [],
            'total_items_processed': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'errors': []
        }
        
        # Process cards
        print(f"\n🎯 Processing {len(cards)} cards...")
        for card in cards:
            card_name = card.get('card_name', 'Unknown')
            set_name = card.get('set_name', '')
            
            try:
                # Search for the card - pass full card data for better search terms
                pc_url = self.search_card_on_pricecharting(card_name, set_name, card_data=card)
                
                if pc_url:
                    # Scrape price history
                    price_data = self.scrape_price_history(pc_url)
                    
                    if price_data:
                        card_result = {
                            'card_id': card.get('id'),
                            'card_name': card_name,
                            'set_name': set_name,
                            'pricecharting_data': price_data
                        }
                        results['cards'].append(card_result)
                        results['successful_scrapes'] += 1
                    else:
                        results['failed_scrapes'] += 1
                else:
                    results['failed_scrapes'] += 1
                
                results['total_items_processed'] += 1
                
            except Exception as e:
                error_msg = f"Error processing card {card_name}: {e}"
                print(f"  ❌ {error_msg}")
                results['errors'].append(error_msg)
                results['failed_scrapes'] += 1
        
        # Process sealed products
        print(f"\n📦 Processing {len(sealed_products)} sealed products...")
        for product in sealed_products:
            product_name = product.get('product_name', 'Unknown')
            
            try:
                # Search for the product
                pc_url = self.search_sealed_product_on_pricecharting(product_name)
                
                if pc_url:
                    # Scrape price history
                    price_data = self.scrape_price_history(pc_url)
                    
                    if price_data:
                        product_result = {
                            'product_id': product.get('id'),
                            'product_name': product_name,
                            'product_type': product.get('product_type', ''),
                            'pricecharting_data': price_data
                        }
                        results['sealed_products'].append(product_result)
                        results['successful_scrapes'] += 1
                    else:
                        results['failed_scrapes'] += 1
                else:
                    results['failed_scrapes'] += 1
                
                results['total_items_processed'] += 1
                
            except Exception as e:
                error_msg = f"Error processing product {product_name}: {e}"
                print(f"  ❌ {error_msg}")
                results['errors'].append(error_msg)
                results['failed_scrapes'] += 1
        
        return results
    
    def save_historical_data(self, results: Dict[str, Any]):
        """Save the scraped historical data to files and potentially Supabase"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to JSON file
        filename = f"data/pricecharting_historical_{timestamp}.json"
        os.makedirs("data", exist_ok=True)
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Historical data saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save historical data: {e}")

def main():
    """Run PriceCharting scraper for curated items"""
    
    from card_selector import CardSelector
    
    # Initialize components
    card_selector = CardSelector()
    scraper = PriceChartingScraper()
    
    print("🚀 Starting PriceCharting Historical Data Collection")
    print("=" * 60)
    
    # Get curated items
    cards = card_selector.get_curated_investment_targets()
    sealed_products = card_selector.get_sealed_products_list()
    
    print(f"📊 Will process {len(cards)} cards and {len(sealed_products)} sealed products")
    
    # Scrape historical data
    results = scraper.scrape_curated_items_historical_data(cards, sealed_products)
    
    # Save results
    scraper.save_historical_data(results)
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 PRICECHARTING SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total items processed: {results['total_items_processed']}")
    print(f"Successful scrapes: {results['successful_scrapes']}")
    print(f"Failed scrapes: {results['failed_scrapes']}")
    print(f"Cards with data: {len(results['cards'])}")
    print(f"Sealed products with data: {len(results['sealed_products'])}")
    
    if results['errors']:
        print(f"\n⚠️ Errors encountered: {len(results['errors'])}")
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")

if __name__ == "__main__":
    main() 