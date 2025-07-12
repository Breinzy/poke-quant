"""
eBay Search Module
Handles eBay search URLs + pagination for sold listings
"""

import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
import sys
import os

# Add current directory to path for local imports  
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from utils import rate_limit_delay, retry_with_backoff

class eBaySearcher:
    """Handles eBay search URL construction and fetching"""
    
    BASE_URL = "https://www.ebay.com/sch/i.html"
    
    def __init__(self):
        self.session = requests.Session()
        # Set user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def build_search_url(self, keywords: str, page: int = 1, **filters) -> str:
        """Build eBay search URL for sold listings"""
        params = {
            '_nkw': keywords,
            '_sop': filters.get('sort', '12'),  # Sort order (default: newest)
            'LH_Sold': '1',  # Sold listings only
            'LH_Complete': '1',  # Completed listings
            '_pgn': page,
            '_ipg': '60'  # Items per page
        }
        
        # Add optional filters
        if filters.get('min_price'):
            params['_udlo'] = filters['min_price']
        if filters.get('max_price'):
            params['_udhi'] = filters['max_price']
        if filters.get('condition'):
            # Map condition to eBay codes if needed
            pass
            
        url = f"{self.BASE_URL}?{urlencode(params)}"
        return url
    
    def fetch_listings_page(self, search_url: str) -> Optional[str]:
        """Fetch HTML content from eBay search page"""
        def _fetch():
            print(f"📡 Fetching: {search_url}")
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            if "blocked" in response.text.lower() or response.status_code == 429:
                raise Exception("Rate limited by eBay")
                
            return response.text
        
        try:
            # Use retry with backoff for resilience
            html = retry_with_backoff(_fetch, max_retries=3)
            print(f"✅ Successfully fetched {len(html)} characters")
            return html
        except Exception as e:
            print(f"❌ Failed to fetch page: {e}")
            return None
    
    def search_sold_listings(self, keywords: str, max_pages: int = 5, max_results: int = None, **filters) -> List[str]:
        """
        Search for sold listings and return HTML pages
        
        Args:
            keywords: Search terms
            max_pages: Maximum pages to fetch (default 5, set to 50+ for comprehensive)
            max_results: Maximum total results (None = no limit)
            **filters: Additional search filters
        """
        print(f"🔍 COMPREHENSIVE SEARCH: '{keywords}'")
        print(f"📊 Max pages: {max_pages}, Max results: {max_results if max_results else 'UNLIMITED'}")
        
        html_pages = []
        total_results_found = 0
        
        for page in range(1, max_pages + 1):
            print(f"📄 Fetching page {page}/{max_pages}")
            
            # Build URL for this page
            search_url = self.build_search_url(keywords, page, **filters)
            
            # Fetch the page
            html = self.fetch_listings_page(search_url)
            
            if html:
                html_pages.append(html)
                
                # Estimate results on this page (60 per page typically)
                page_results = 60  # eBay default items per page
                total_results_found += page_results
                
                print(f"    ✅ Page {page}: ~{page_results} listings (Total: ~{total_results_found})")
                
                # Check if we've hit max_results limit
                if max_results and total_results_found >= max_results:
                    print(f"🎯 Reached max results limit ({max_results})")
                    break
                
                # Check if this is the last page (multiple indicators)
                end_indicators = [
                    "Next page" not in html,
                    len(html) < 10000,  # Very small page
                    "No exact matches found" in html,
                    "0 results" in html.lower()
                ]
                
                if any(end_indicators):
                    print(f"🏁 Reached end of results at page {page}")
                    break
            else:
                print(f"⚠️ Failed to fetch page {page}, stopping")
                break
            
            # Rate limit between requests (longer for comprehensive scraping)
            if page < max_pages:
                rate_limit_delay(delay=2.0)  # 2 second delay between pages
        
        print(f"📦 COMPREHENSIVE COLLECTION COMPLETE:")
        print(f"    Pages collected: {len(html_pages)}")
        print(f"    Estimated listings: ~{total_results_found}")
        print(f"    Data size: {sum(len(page) for page in html_pages):,} characters")
        
        return html_pages
    
    def search_specific_card(self, card_name: str, set_name: str = "", **filters) -> List[str]:
        """Search for a specific card with set name"""
        # Build targeted search query
        query_parts = [card_name, "pokemon card"]
        if set_name:
            query_parts.append(set_name)
            
        keywords = " ".join(query_parts)
        return self.search_sold_listings(keywords, **filters) 