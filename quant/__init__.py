"""
PokeQuant - Quantitative Analysis for Pokemon Cards and Sealed Products

A comprehensive tool for analyzing Pokemon card and sealed product investments
using eBay and PriceCharting data.
"""

__version__ = "1.0.0"
__author__ = "PokeQuant Team"

# Core modules
from .freshness_checker import DataFreshnessChecker
# from .product_finder import ProductFinder  # TODO: Implement in Phase 1.3
# from .scraper_service import ScraperService  # TODO: Implement in Phase 2.1

__all__ = [
    'DataFreshnessChecker',
    # 'ProductFinder',
    # 'ScraperService',
] 