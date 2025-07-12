"""
Utility functions for eBay scraper
Date handling, batching, retries, etc.
"""

import time
import random
from datetime import datetime, timedelta
from typing import List, Any, Callable
import logging

def setup_logging():
    """Setup logging for the scraper"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ebay_scraper.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def rate_limit_delay(min_delay: float = 3.0, max_delay: float = 5.0):
    """Add random delay to avoid rate limiting"""
    delay = random.uniform(min_delay, max_delay)
    print(f"⏱️ Rate limiting... waiting {delay:.1f}s")
    time.sleep(delay)

def batch_list(items: List[Any], batch_size: int = 50) -> List[List[Any]]:
    """Split list into batches for processing"""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def retry_with_backoff(func: Callable, max_retries: int = 3, base_delay: float = 1.0):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = base_delay * (2 ** attempt)
            print(f"🔄 Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
            time.sleep(delay)

def parse_ebay_date(date_str: str) -> datetime:
    """Parse eBay date string to datetime object"""
    # TODO: Handle various eBay date formats
    # Common formats: "Dec 15, 2023", "12/15/23", etc.
    return datetime.now()  # Placeholder

def is_recent_listing(sold_date: datetime, days_back: int = 30) -> bool:
    """Check if listing is within specified days"""
    cutoff_date = datetime.now() - timedelta(days=days_back)
    return sold_date >= cutoff_date 