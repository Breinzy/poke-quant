#!/usr/bin/env python3
"""
Fixed PriceCharting Scraper
Addresses issues with $1.00 contamination and subscription fee parsing
"""

import requests
import time
import re
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

class PriceChartingScraperFixed:
    """Fixed PriceCharting scraper with improved price extraction"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Rate limiting
        self.delay_between_requests = 2.0
        self.last_request_time = 0
    
    def _extract_current_prices_fixed(self, soup: BeautifulSoup) -> Dict[str, float]:
        """Fixed price extraction that properly filters out non-price elements"""
        prices = {}
        
        try:
            # 1. Extract chart summary prices (most reliable)
            self._extract_chart_summary_prices(soup, prices)
            
            # 2. Extract prices from designated price display areas only
            self._extract_designated_price_displays(soup, prices)
            
            # 3. Extract table prices with strict filtering
            self._extract_table_prices_strict(soup, prices)
            
        except Exception as e:
            print(f"    ⚠️ Error extracting current prices: {e}")
        
        return prices
    
    def _extract_chart_summary_prices(self, soup: BeautifulSoup, prices: Dict[str, float]):
        """Extract prices from the main price summary area (most reliable)"""
        try:
            # Look for the main price display table (ungraded/graded prices)
            price_summary_selectors = [
                'table.price-summary',
                'table[class*="price"]',
                '.price-chart-container table',
                'table:has(.price)'
            ]
            
            for selector in price_summary_selectors:
                tables = soup.select(selector)
                for table in tables:
                    # Look for condition-based pricing
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            label_text = cells[0].get_text().strip().lower()
                            
                            for i, cell in enumerate(cells[1:], 1):
                                price_text = cell.get_text().strip()
                                price_match = re.search(r'\$(\d+\.?\d*)', price_text)
                                
                                if price_match:
                                    price = float(price_match.group(1))
                                    
                                    # Only accept reasonable prices
                                    if self._is_valid_product_price(price):
                                        condition = self._determine_condition_from_context(label_text, i)
                                        if condition and condition not in prices:
                                            prices[condition] = price
        except Exception as e:
            print(f"    ⚠️ Error extracting chart summary prices: {e}")
    
    def _extract_designated_price_displays(self, soup: BeautifulSoup, prices: Dict[str, float]):
        """Extract prices only from designated price display elements"""
        try:
            # Specific selectors for actual price display areas
            price_display_selectors = [
                '.price-display .price',
                '.current-price',
                '.price-value',
                '.chart-price',
                '.product-price'
            ]
            
            for selector in price_display_selectors:
                elements = soup.select(selector)
                for element in elements:
                    # Skip if inside subscription/tour area
                    if self._is_in_subscription_area(element):
                        continue
                    
                    text = element.get_text().strip()
                    price_match = re.search(r'\$(\d+\.?\d*)', text)
                    
                    if price_match:
                        price = float(price_match.group(1))
                        if self._is_valid_product_price(price):
                            context = self._get_price_context(element)
                            key = f"display_{context}" if context else "display_current"
                            prices[key] = price
        except Exception as e:
            print(f"    ⚠️ Error extracting designated price displays: {e}")
    
    def _extract_table_prices_strict(self, soup: BeautifulSoup, prices: Dict[str, float]):
        """Extract table prices with strict filtering to avoid contamination"""
        try:
            # Only look at tables that are likely to contain sales data
            sales_tables = self._find_sales_tables(soup)
            
            for table in sales_tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    # Skip header rows
                    if row.find('th'):
                        continue
                    
                    cells = row.find_all('td')
                    if len(cells) < 3:  # Need at least date, description, price
                        continue
                    
                    # Extract date and price from this row
                    date_found = None
                    price_found = None
                    description = ""
                    
                    for cell in cells:
                        cell_text = cell.get_text().strip()
                        
                        # Check for date
                        if re.match(r'20\d{2}-\d{1,2}-\d{1,2}', cell_text):
                            date_found = cell_text
                        
                        # Check for price, but be very strict
                        if self._is_price_cell(cell, cell_text):
                            price_match = re.search(r'\$(\d+\.?\d*)', cell_text)
                            if price_match:
                                price = float(price_match.group(1))
                                if self._is_valid_product_price(price):
                                    price_found = price
                        
                        # Build description
                        if len(cell_text) > 10 and not re.match(r'20\d{2}-\d{1,2}-\d{1,2}', cell_text):
                            description += " " + cell_text
                    
                    # Only add if we have both date and price, and description looks like a product
                    if date_found and price_found and self._is_valid_product_description(description):
                        key = f"table_price_{len(prices)}"
                        prices[key] = price_found
                        
        except Exception as e:
            print(f"    ⚠️ Error extracting table prices: {e}")
    
    def _find_sales_tables(self, soup: BeautifulSoup) -> List:
        """Find tables that likely contain sales data"""
        sales_tables = []
        
        tables = soup.find_all('table')
        for table in tables:
            # Look for tables with date columns
            headers = table.find_all(['th'])
            header_text = " ".join([h.get_text().lower() for h in headers])
            
            # Check if this looks like a sales table
            if any(keyword in header_text for keyword in ['date', 'sale', 'price', 'title']):
                # Make sure it's not a subscription or navigation table
                table_text = table.get_text().lower()
                if not any(keyword in table_text for keyword in ['subscribe', 'navigation', 'menu']):
                    sales_tables.append(table)
        
        return sales_tables
    
    def _is_price_cell(self, cell, cell_text: str) -> bool:
        """Determine if a cell likely contains a product price"""
        
        # Must contain a price pattern
        if not re.search(r'\$\d+\.?\d*', cell_text):
            return False
        
        # Skip if contains subscription-related text
        if any(keyword in cell_text.lower() for keyword in [
            'subscribe', 'month', '/month', 'subscription'
        ]):
            return False
        
        # Skip if in a tour/help area
        if self._is_in_subscription_area(cell):
            return False
        
        # Skip if cell has classes that suggest it's not a price
        cell_classes = cell.get('class', [])
        if any(cls in str(cell_classes).lower() for cls in [
            'tour', 'help', 'subscription', 'nav', 'menu', 'button'
        ]):
            return False
        
        # Must be in a numeric column (has class 'numeric' or similar)
        if 'numeric' in str(cell_classes).lower():
            return True
        
        # Check if the cell content is primarily a price (not mixed with lots of other text)
        price_chars = len(re.findall(r'[\d\.\$]', cell_text))
        total_chars = len(cell_text.strip())
        
        if total_chars > 0 and (price_chars / total_chars) > 0.3:  # At least 30% price-related chars
            return True
        
        return False
    
    def _is_valid_product_price(self, price: float) -> bool:
        """Determine if a price is valid for a Pokemon product"""
        
        # Filter out known problematic prices
        if price == 6.0:  # Subscription fee
            return False
        
        # Filter out unrealistic prices
        if price < 1.0:  # Too low to be a real product
            return False
        
        if price > 100000:  # Too high to be realistic
            return False
        
        # Filter out common non-product prices
        suspicious_prices = [1.0, 1.99, 2.0, 2.99, 3.0, 4.99, 5.0, 6.0, 9.99]
        if price in suspicious_prices:
            return False
        
        return True
    
    def _is_valid_product_description(self, description: str) -> bool:
        """Check if description looks like a real product listing"""
        description = description.strip().lower()
        
        # Must have some content
        if len(description) < 10:
            return False
        
        # Should contain Pokemon-related terms
        pokemon_terms = ['pokemon', 'charizard', 'pikachu', 'card', 'booster', 'tcg']
        if not any(term in description for term in pokemon_terms):
            return False
        
        # Should not contain subscription terms
        if any(term in description for term in ['subscribe', 'month', 'subscription']):
            return False
        
        return True
    
    def _is_in_subscription_area(self, element) -> bool:
        """Check if element is inside a subscription/tour area"""
        parent = element.parent
        
        # Walk up the DOM tree looking for subscription-related containers
        for _ in range(5):  # Check up to 5 levels up
            if not parent:
                break
            
            # Check classes
            classes = parent.get('class', [])
            if any(cls in str(classes).lower() for cls in [
                'tour', 'subscription', 'subscribe', 'help', 'modal'
            ]):
                return True
            
            # Check if text content suggests subscription area
            parent_text = parent.get_text().lower()
            if any(keyword in parent_text for keyword in [
                'subscribe', '$6/month', 'time warp'
            ]):
                return True
            
            parent = parent.parent
        
        return False
    
    def _determine_condition_from_context(self, label_text: str, column_index: int) -> Optional[str]:
        """Determine price condition from table context"""
        label_lower = label_text.lower()
        
        if 'ungraded' in label_lower or 'loose' in label_lower:
            return 'ungraded'
        elif 'graded' in label_lower:
            return f'graded_{column_index}'
        elif 'psa 10' in label_lower or 'gem mint' in label_lower:
            return 'psa_10'
        elif 'psa 9' in label_lower:
            return 'psa_9'
        elif 'new' in label_lower or 'sealed' in label_lower:
            return 'new'
        else:
            return f'condition_{column_index}'
    
    def _get_price_context(self, element) -> str:
        """Get context for a price element"""
        # Look at nearby text for condition indicators
        context_text = ""
        
        # Check element itself
        if element.get('class'):
            context_text += " ".join(element.get('class'))
        
        # Check parent
        if element.parent:
            context_text += " " + element.parent.get_text()
        
        context_lower = context_text.lower()
        
        if 'loose' in context_lower or 'ungraded' in context_lower:
            return 'loose'
        elif 'graded' in context_lower:
            return 'graded'
        elif 'new' in context_lower or 'sealed' in context_lower:
            return 'new'
        else:
            return 'current'
    
    def scrape_price_history_fixed(self, pricecharting_url: str) -> Dict[str, Any]:
        """Fixed version of price history scraping"""
        
        print(f"  🔍 Scraping: {pricecharting_url}")
        
        try:
            self._rate_limit()
            response = self.session.get(pricecharting_url)
            
            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            html_content = response.text
            
            # Extract data using fixed methods
            result = {
                'url': pricecharting_url,
                'current_prices': self._extract_current_prices_fixed(soup),
                'chart_data': self._extract_chart_data_advanced(html_content),
                'product_info': self._extract_product_info(soup),
                'scrape_timestamp': datetime.now().isoformat()
            }
            
            # Summary stats
            chart_count = len(result['chart_data'])
            price_count = len(result['current_prices'])
            
            print(f"  ✅ Success: {chart_count} chart points, {price_count} current prices")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error scraping price history: {e}")
            return {}
    
    def _extract_chart_data_advanced(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract historical chart data (reusing existing working logic)"""
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
                        date = datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                        
                        # Convert price from cents to dollars
                        price_dollars = price_cents / 100.0
                        
                        # Skip zero prices
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
                
        except Exception as e:
            print(f"    ⚠️ Error extracting chart data: {e}")
        
        return chart_data
    
    def _extract_product_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract product information"""
        info = {}
        
        try:
            # Product title
            title_element = soup.find('h1')
            if title_element:
                info['title'] = title_element.get_text().strip()
                
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
        
        # Set base URL if not defined
        if not hasattr(self, 'base_url'):
            self.base_url = "https://www.pricecharting.com"
        
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
        
        # Set base URL if not defined
        if not hasattr(self, 'base_url'):
            self.base_url = "https://www.pricecharting.com"
        
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

    def save_historical_data(self, results: Dict[str, Any]):
        """Save the scraped historical data to files and potentially Supabase"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to JSON file
        filename = f"data/pricecharting_historical_fixed_{timestamp}.json"
        os.makedirs("data", exist_ok=True)
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Historical data saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save historical data: {e}")

def test_fixed_scraper():
    """Test the fixed scraper on problematic URLs"""
    
    print("🔧 Testing Fixed PriceCharting Scraper")
    print("="*50)
    
    # Test URLs from our debug
    test_urls = [
        ("Charizard V", "https://www.pricecharting.com/game/3188378"),
        ("Evolving Skies Booster Box", "https://www.pricecharting.com/game/3217472"),
        ("Base Set Booster Box", "https://www.pricecharting.com/game/2368436")
    ]
    
    scraper = PriceChartingScraperFixed()
    
    for name, url in test_urls:
        print(f"\n🎯 Testing: {name}")
        print("-" * 30)
        
        result = scraper.scrape_price_history_fixed(url)
        
        if result:
            current_prices = result.get('current_prices', {})
            chart_data = result.get('chart_data', [])
            
            print(f"  📊 Current prices found: {len(current_prices)}")
            print(f"  📈 Chart data points: {len(chart_data)}")
            
            # Show sample current prices
            if current_prices:
                print("  💰 Sample current prices:")
                for key, price in list(current_prices.items())[:5]:
                    print(f"    {key}: ${price}")
                
                # Check for suspicious prices
                suspicious = [price for price in current_prices.values() 
                             if price in [1.0, 6.0] or price < 1.0]
                if suspicious:
                    print(f"  ⚠️ Suspicious prices found: {suspicious}")
                else:
                    print(f"  ✅ No suspicious prices detected")
            
            # Show chart data range
            if chart_data:
                prices = [d['price'] for d in chart_data]
                print(f"  📈 Chart price range: ${min(prices):.2f} - ${max(prices):.2f}")
        else:
            print(f"  ❌ Failed to scrape data")

if __name__ == "__main__":
    test_fixed_scraper() 