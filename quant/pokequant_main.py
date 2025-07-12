#!/usr/bin/env python3
"""
PokeQuant Main Orchestrator
Complete end-to-end flow: Product Input → Freshness Check → Scraping → Analysis → Results
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase
from quant.freshness_checker import DataFreshnessChecker
from quant.price_data_service import PriceDataService
from quant.enhanced_outlier_filter import apply_enhanced_filtering

# Optional LLM-enhanced filtering
try:
    from quant.llm_enhanced_filter import apply_llm_enhanced_filtering
    LLM_FILTERING_AVAILABLE = True
except ImportError:
    LLM_FILTERING_AVAILABLE = False
    apply_llm_enhanced_filtering = None

# Import existing scrapers
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ebay-scraper'))
from ebay_search import eBaySearcher
from ebay_parser import eBayParser
from ebay_to_supabase import eBaySupabaseUploader
from pricecharting_scraper import PriceChartingScraper

class PokeQuantOrchestrator:
    """Main PokeQuant orchestrator - complete product analysis pipeline"""
    
    def __init__(self, max_age_days: int = 7, analysis_cache_hours: int = 24, use_llm: bool = False):
        self.max_age_days = max_age_days
        self.analysis_cache_hours = analysis_cache_hours
        self._use_llm_flag = use_llm
        self.supabase = supabase
        self.freshness_checker = DataFreshnessChecker(max_age_days)
        self.price_data_service = PriceDataService()
        
        # Initialize scrapers
        self.ebay_searcher = eBaySearcher()
        self.ebay_parser = eBayParser()
        self.ebay_uploader = eBaySupabaseUploader()
        self.pricecharting_scraper = PriceChartingScraper()
        
    def analyze_product(self, product_name: str, force_refresh: bool = False, force_analysis: bool = False) -> Dict[str, Any]:
        """
        Complete analysis pipeline for a product
        
        Args:
            product_name: Name of the product to analyze
            force_refresh: Force data refresh even if recent data exists
            force_analysis: Force analysis even if cached analysis exists
            
        Returns:
            Complete analysis results
        """
        
        print(f"🚀 PokeQuant Analysis: {product_name}")
        print("=" * 60)
        
        result = {
            'product_name': product_name,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'stages': {},
            'final_analysis': {},
            'used_cached_analysis': False
        }
        
        try:
            # Stage 1: Find and identify the product
            print("\n📍 Stage 1: Product Identification")
            product_info = self._find_product(product_name)
            result['stages']['product_identification'] = product_info
            
            if not product_info['found']:
                result['error'] = f"Product '{product_name}' not found in database"
                return result
            
            # Get or create the pokequant_product_id early
            product = product_info['product']
            pokequant_product_id = self.price_data_service.ensure_product_exists(
                product['type'], product['id'], product['name'], product.get('set_name')
            )
            
            # Stage 1.5: Check for cached analysis (NEW)
            if not force_analysis:
                print("\n🔍 Stage 1.5: Checking for Cached Analysis")
                cached_analysis = self._check_cached_analysis(pokequant_product_id)
                if cached_analysis:
                    print(f"   ✅ Using cached analysis from {cached_analysis['analysis_metadata']['analysis_date']}")
                    result['used_cached_analysis'] = True
                    result['success'] = True
                    result['final_analysis'] = cached_analysis
                    return result
                else:
                    print("   💾 No recent cached analysis found, proceeding with full analysis")
            
            # Stage 2: Check data freshness
            print("\n📅 Stage 2: Data Freshness Check")
            freshness_info = self.freshness_checker.check_product_freshness(product_name)
            result['stages']['freshness_check'] = freshness_info
            
            # Stage 3: Data collection (if needed)
            if force_refresh or not freshness_info['is_fresh']:
                print("\n🔄 Stage 3: Data Collection")
                collection_result = self._collect_fresh_data(product_info, freshness_info)
                result['stages']['data_collection'] = collection_result
            else:
                print("\n✅ Stage 3: Using cached data (fresh enough)")
                result['stages']['data_collection'] = {'status': 'skipped', 'reason': 'data_is_fresh'}
            
            # Stage 4: Load and prepare data for analysis
            print("\n📊 Stage 4: Data Preparation")
            analysis_data = self._prepare_analysis_data(product_info)
            result['stages']['data_preparation'] = analysis_data
            
            if not analysis_data['success']:
                result['error'] = "Insufficient data for analysis"
                return result
            
            # Stage 5: Quantitative analysis
            print("\n🧮 Stage 5: Quantitative Analysis")
            analysis_results = self._perform_quantitative_analysis(analysis_data)
            result['stages']['quantitative_analysis'] = analysis_results
            
            # Stage 6: Generate recommendations
            print("\n💡 Stage 6: Investment Recommendation")
            recommendation = self._generate_recommendation(analysis_results)
            result['stages']['recommendation'] = recommendation
            
            # Compile final results
            final_analysis = {
                'product': product_info,
                'data_summary': analysis_data.get('summary', {}),
                'metrics': analysis_results.get('metrics', {}),
                'recommendation': recommendation,
                'analysis_metadata': {
                    'pokequant_product_id': pokequant_product_id,
                    'analysis_date': datetime.now().isoformat(),
                    'data_range': analysis_data.get('summary', {}).get('date_range', {}),
                    'total_data_points': analysis_data.get('summary', {}).get('total_data_points', 0)
                }
            }
            
            result['final_analysis'] = final_analysis
            result['success'] = True
            
            # Stage 7: Store analysis results (NEW)
            print("\n💾 Stage 7: Storing Analysis Results")
            self._store_analysis_results(pokequant_product_id, final_analysis)
            
            print(f"\n🎉 Analysis Complete for {product_name}!")
            
        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            result['error'] = str(e)
        
        return result
    
    def _find_product(self, product_name: str) -> Dict[str, Any]:
        """Find and identify a product in the database"""
        
        print(f"   🔍 Searching for: {product_name}")
        
        # Search in pokemon_cards
        card_results = []
        try:
            card_query = self.supabase.table('pokemon_cards').select('*').ilike('card_name', f'%{product_name}%').limit(5).execute()
            card_results = card_query.data
        except Exception as e:
            print(f"   ⚠️ Error searching cards: {e}")
        
        # Search in sealed_products
        sealed_results = []
        try:
            sealed_query = self.supabase.table('sealed_products').select('*').ilike('product_name', f'%{product_name}%').limit(5).execute()
            sealed_results = sealed_query.data
        except Exception as e:
            print(f"   ⚠️ Error searching sealed products: {e}")
        
        # Combine and format results
        all_results = []
        
        for card in card_results:
            all_results.append({
                'type': 'card',
                'id': str(card['id']),
                'name': card['card_name'],
                'set_name': card.get('set_name', ''),
                'display_name': f"{card['card_name']} - {card.get('set_name', 'Unknown Set')}",
                'raw_data': card
            })
        
        for product in sealed_results:
            all_results.append({
                'type': 'sealed',
                'id': str(product['id']),
                'name': product['product_name'],
                'set_name': product.get('set_name', ''),
                'display_name': f"{product['product_name']}",
                'raw_data': product
            })
        
        if all_results:
            # For now, return the first match
            # TODO: In the future, let user choose from multiple matches
            selected = all_results[0]
            print(f"   ✅ Found: {selected['display_name']} ({selected['type']})")
            
            return {
                'found': True,
                'product': selected,
                'all_matches': all_results,
                'match_count': len(all_results)
            }
        else:
            print(f"   ❌ No products found matching '{product_name}'")
            return {
                'found': False,
                'product': None,
                'all_matches': [],
                'match_count': 0
            }
    
    def _collect_fresh_data(self, product_info: Dict, freshness_info: Dict) -> Dict[str, Any]:
        """Collect fresh data using existing scrapers"""
        
        product = product_info['product']
        product_type = product['type']
        product_id = product['id']
        
        print(f"   🔄 Collecting fresh data for {product['display_name']}")
        
        collection_result = {
            'ebay_scraping': {'status': 'skipped'},
            'pricecharting_scraping': {'status': 'skipped'},
            'success': False
        }
        
        # Determine what needs scraping
        action = freshness_info.get('recommended_action', 'scrape_both')
        
        if action in ['scrape_both', 'scrape_ebay_only']:
            print("   📈 Scraping eBay data...")
            ebay_result = self._scrape_ebay_data(product_type, product_id, product['name'])
            collection_result['ebay_scraping'] = ebay_result
            
            # Aggregate eBay data into PokeQuant price series
            if ebay_result.get('status') == 'success':
                print("   📊 Aggregating eBay data...")
                agg_result = self.price_data_service.aggregate_ebay_data(
                    product_type, product_id, product['name'], product.get('set_name')
                )
                collection_result['ebay_aggregation'] = agg_result
        
        if action in ['scrape_both', 'scrape_pricecharting_only']:
            print("   💰 Scraping PriceCharting data...")
            pc_result = self._scrape_pricecharting_data(product_type, product_id, product['name'])
            collection_result['pricecharting_scraping'] = pc_result
            
            # Aggregate PriceCharting data into PokeQuant price series
            if pc_result.get('status') == 'success':
                print("   📊 Aggregating PriceCharting data...")
                agg_result = self.price_data_service.aggregate_pricecharting_data(
                    product_type, product_id, product['name'], pc_result['pc_data'], product.get('set_name')
                )
                collection_result['pricecharting_aggregation'] = agg_result
        
        # Check if any scraping was successful
        ebay_success = collection_result['ebay_scraping'].get('status') == 'success'
        pc_success = collection_result['pricecharting_scraping'].get('status') == 'success'
        
        collection_result['success'] = ebay_success or pc_success or action == 'use_cache'
        
        return collection_result
    
    def _scrape_ebay_data(self, product_type: str, product_id: str, product_name: str) -> Dict[str, Any]:
        """Scrape eBay data for a product"""
        
        try:
            # Search eBay for the product
            search_terms = product_name
            html_pages = self.ebay_searcher.search_sold_listings(search_terms, max_pages=3)
            
            if not html_pages:
                return {'status': 'failed', 'error': 'No eBay pages retrieved'}
            
            # Parse the HTML
            all_listings = []
            for html in html_pages:
                listings = self.ebay_parser.parse_listing_html(html, product_name, product_type == 'sealed')
                all_listings.extend(listings)
            
            if not all_listings:
                return {'status': 'failed', 'error': 'No listings parsed from eBay'}
            
            # Upload to database
            if product_type == 'card':
                upload_success = self.ebay_uploader.upload_targeted_listings(all_listings, int(product_id), search_terms)
            else:  # sealed
                upload_success = self.ebay_uploader.upload_sealed_product_listings(all_listings, int(product_id), search_terms)
            
            if upload_success:
                return {
                    'status': 'success',
                    'listings_found': len(all_listings),
                    'pages_scraped': len(html_pages)
                }
            else:
                return {'status': 'failed', 'error': 'Failed to upload to database'}
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def _scrape_pricecharting_data(self, product_type: str, product_id: str, product_name: str) -> Dict[str, Any]:
        """Scrape PriceCharting data for a product"""
        
        try:
            print(f"   🔍 Searching PriceCharting for: {product_name}")
            
            # Search for the product on PriceCharting
            if product_type == 'card':
                pc_url = self.pricecharting_scraper.search_card_on_pricecharting(product_name)
            else:  # sealed
                pc_url = self.pricecharting_scraper.search_sealed_product_on_pricecharting(product_name)
            
            if not pc_url:
                return {
                    'status': 'failed',
                    'error': 'Product not found on PriceCharting'
                }
            
            print(f"   📈 Scraping price history from: {pc_url}")
            
            # Scrape historical price data
            pc_data = self.pricecharting_scraper.scrape_price_history(pc_url)
            
            if not pc_data or not pc_data.get('historical_chart_data'):
                return {
                    'status': 'failed',
                    'error': 'No historical data found on PriceCharting'
                }
            
            print(f"   ✅ Found {len(pc_data.get('historical_chart_data', []))} historical data points")
            
            return {
                'status': 'success',
                'url': pc_url,
                'data_points': len(pc_data.get('historical_chart_data', [])),
                'current_prices': pc_data.get('current_prices', {}),
                'pc_data': pc_data
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _prepare_analysis_data(self, product_info: Dict) -> Dict[str, Any]:
        """Load and prepare data for quantitative analysis from pokequant_price_series"""
        
        product = product_info['product']
        product_type = product['type']
        product_id = product['id']
        
        print(f"   📊 Loading price data for analysis...")
        
        try:
            # First, get or create the pokequant_product_id
            pokequant_product_id = self.price_data_service.ensure_product_exists(
                product_type, product_id, product['name'], product.get('set_name')
            )
            
            if not pokequant_product_id:
                return {
                    'success': False,
                    'error': 'Failed to create PokeQuant product entry'
                }
            
            # Load aggregated price series data from PokeQuant tables
            price_series_result = self.price_data_service.get_price_series(pokequant_product_id)
            
            if not price_series_result['success']:
                # Fallback: try to aggregate existing raw data
                print("   🔄 No aggregated data found, attempting to aggregate existing data...")
                
                ebay_agg = self.price_data_service.aggregate_ebay_data(
                    product_type, product_id, product['name'], product.get('set_name')
                )
                
                if ebay_agg['success']:
                    # Retry loading price series
                    price_series_result = self.price_data_service.get_price_series(pokequant_product_id)
                
                if not price_series_result['success']:
                    return {
                        'success': False,
                        'error': 'No price data available for analysis'
                    }
            
            # Extract price data for analysis
            price_data = price_series_result['raw_data']
            all_prices = [point['price'] for point in price_data]
            
            if not all_prices:
                return {
                    'success': False,
                    'error': 'No valid price data found'
                }
            
            # Apply enhanced outlier filtering
            print(f"   🔍 Applying enhanced outlier filtering...")
            
            # Prepare data for filtering (add title information for eBay data)
            raw_data_with_titles = []
            for point in price_data:
                if point['source'] == 'ebay' and 'sample_titles' in point:
                    # Use the first available title for filtering
                    titles = point.get('sample_titles', [])
                    if titles:
                        point['title'] = titles[0]
                raw_data_with_titles.append(point)
            
            # Apply enhanced filtering (with optional LLM enhancement)
            # Extract the actual product info from the nested structure
            actual_product_info = product_info['product'] if 'product' in product_info else product_info
            
            # Check if LLM filtering is enabled (via env var or CLI flag)
            use_llm = (LLM_FILTERING_AVAILABLE and 
                      os.getenv('OPENAI_API_KEY') and 
                      (os.getenv('POKEQUANT_USE_LLM', 'false').lower() == 'true' or 
                       getattr(self, '_use_llm_flag', False)))
            
            if use_llm:
                print(f"   🤖 Using LLM-enhanced filtering...")
                filtered_data = apply_llm_enhanced_filtering(
                    raw_data_with_titles,
                    actual_product_info,
                    verbose=False
                )
            else:
                filtered_data = apply_enhanced_filtering(
                    raw_data_with_titles, 
                    actual_product_info, 
                    verbose=False
                )
            
            # Update price data with filtered results
            price_data = filtered_data
            all_prices = [p['price'] for p in filtered_data]
            
            print(f"   ✅ After filtering: {len(filtered_data)} data points (removed {len(price_series_result['raw_data']) - len(filtered_data)} outliers)")
            
            # Create analysis-ready data structure
            summary = price_series_result['summary']
            summary['total_data_points'] = len(filtered_data)  # Update count after filtering
            
            return {
                'success': True,
                'price_series': price_data,
                'prices': all_prices,
                'summary': summary,
                'organized_data': price_series_result['organized_data'],
                'pokequant_product_id': pokequant_product_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_date_range(self, listings: List[Dict]) -> Dict[str, str]:
        """Get date range from listings"""
        
        dates = []
        for listing in listings:
            if listing.get('created_at'):
                dates.append(listing['created_at'])
            elif listing.get('sold_date'):
                dates.append(listing['sold_date'])
        
        if dates:
            return {
                'earliest': min(dates),
                'latest': max(dates)
            }
        else:
            return {'earliest': None, 'latest': None}
    
    def _perform_quantitative_analysis(self, data: Dict) -> Dict[str, Any]:
        """Perform enhanced quantitative analysis with multi-source data"""
        
        prices = data['prices']
        price_series = data['price_series']
        summary = data['summary']
        organized_data = data['organized_data']
        
        print(f"   🧮 Calculating metrics for {len(prices)} price points from {len(summary['sources'])} sources...")
        
        try:
            # Basic price statistics
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            # Price volatility (simple standard deviation)
            variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
            volatility = variance ** 0.5
            
            # Enhanced trend analysis using chronological order
            sorted_prices = sorted(price_series, key=lambda x: x['price_date'])
            chronological_prices = [p['price'] for p in sorted_prices]
            
            # Compare first and last thirds for trend
            third = len(chronological_prices) // 3
            if third > 0:
                early_avg = sum(chronological_prices[:third]) / third
                late_avg = sum(chronological_prices[-third:]) / third
                trend_direction = 'rising' if late_avg > early_avg else 'falling'
                trend_strength = abs(late_avg - early_avg) / early_avg if early_avg > 0 else 0
            else:
                trend_direction = 'stable'
                trend_strength = 0
            
            # Calculate data quality score
            quality_score = self.price_data_service.calculate_data_quality_score(data['pokequant_product_id'])
            
            # Multi-source analysis
            source_breakdown = {}
            for source in summary['sources']:
                source_prices = [p['price'] for p in price_series if p['source'] == source]
                if source_prices:
                    source_breakdown[source] = {
                        'count': len(source_prices),
                        'average': round(sum(source_prices) / len(source_prices), 2),
                        'range': [round(min(source_prices), 2), round(max(source_prices), 2)]
                    }
            
            metrics = {
                'price_stats': {
                    'average': round(avg_price, 2),
                    'minimum': round(min_price, 2),
                    'maximum': round(max_price, 2),
                    'volatility': round(volatility, 2),
                    'volatility_percent': round((volatility / avg_price) * 100, 2)
                },
                'trend_analysis': {
                    'direction': trend_direction,
                    'strength': round(trend_strength * 100, 2),
                    'chronological_sample': len(chronological_prices)
                },
                'market_position': {
                    'current_vs_max': round((avg_price / max_price) * 100, 2),
                    'current_vs_min': round((avg_price / min_price) * 100, 2)
                },
                'data_sources': source_breakdown,
                'date_coverage': {
                    'start': summary['date_range']['start'] if summary['date_range'] else None,
                    'end': summary['date_range']['end'] if summary['date_range'] else None,
                    'total_points': summary['total_data_points']
                }
            }
            
            print(f"   ✅ Calculated enhanced metrics with data quality score: {quality_score:.2f}")
            
            return {
                'success': True,
                'metrics': metrics,
                'data_quality': {
                    'quality_score': round(quality_score, 2),
                    'sample_size': len(prices),
                    'source_diversity': len(summary['sources']),
                    'date_range_days': self.price_data_service._calculate_date_range_days(summary['date_range'])
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_recommendation(self, analysis: Dict) -> Dict[str, Any]:
        """Generate investment recommendation based on analysis"""
        
        if not analysis.get('success'):
            return {
                'recommendation': 'INSUFFICIENT_DATA',
                'confidence': 0.0,
                'reasoning': ['Not enough data for reliable recommendation']
            }
        
        metrics = analysis['metrics']
        price_stats = metrics['price_stats']
        trend = metrics['trend_analysis']
        position = metrics['market_position']
        
        print(f"   💡 Generating recommendation...")
        
        # Simple recommendation logic
        reasoning = []
        score = 0
        
        # Factor 1: Data quality (affects confidence)
        data_quality = analysis.get('data_quality', {})
        quality_score = data_quality.get('quality_score', 0.5)
        
        if quality_score >= 0.8:
            score += 1
            reasoning.append(f"High-quality data (score: {quality_score:.2f}) increases confidence")
        elif quality_score < 0.4:
            score -= 1
            reasoning.append(f"Limited data quality (score: {quality_score:.2f}) reduces confidence")
        
        # Factor 2: Volatility (lower is better for stability)
        if price_stats['volatility_percent'] < 15:
            score += 2
            reasoning.append(f"Low volatility ({price_stats['volatility_percent']:.1f}%) indicates stable pricing")
        elif price_stats['volatility_percent'] > 30:
            score -= 1
            reasoning.append(f"High volatility ({price_stats['volatility_percent']:.1f}%) indicates risky investment")
        
        # Factor 3: Trend direction
        if trend['direction'] == 'rising' and trend['strength'] > 5:
            score += 2
            reasoning.append(f"Strong upward trend (+{trend['strength']:.1f}%)")
        elif trend['direction'] == 'falling' and trend['strength'] > 10:
            score -= 2
            reasoning.append(f"Downward trend (-{trend['strength']:.1f}%)")
        
        # Factor 4: Current price position
        if position['current_vs_max'] < 80:
            score += 1
            reasoning.append(f"Currently {100 - position['current_vs_max']:.0f}% below peak price")
        elif position['current_vs_max'] > 95:
            score -= 1
            reasoning.append("Currently near peak price")
        
        # Factor 5: Multi-source data validation
        data_sources = metrics.get('data_sources', {})
        if len(data_sources) >= 2:
            score += 1
            reasoning.append(f"Data validated across {len(data_sources)} sources")
        elif len(data_sources) == 1:
            reasoning.append("Single data source - limited validation")
        
        # Determine recommendation with enhanced confidence calculation
        base_confidence = quality_score * 0.7 + 0.3  # Quality score affects confidence significantly
        
        if score >= 4:
            recommendation = 'BUY'
            confidence = min(0.9, base_confidence + 0.2)
            risk_level = 'LOW' if price_stats['volatility_percent'] < 20 else 'MEDIUM'
        elif score >= 2:
            recommendation = 'HOLD'
            confidence = min(0.8, base_confidence + 0.1)
            risk_level = 'MEDIUM'
        elif score >= 0:
            recommendation = 'HOLD'
            confidence = base_confidence
            risk_level = 'MEDIUM' if price_stats['volatility_percent'] < 30 else 'HIGH'
        elif score <= -2:
            recommendation = 'AVOID'
            confidence = min(0.8, base_confidence + 0.1)
            risk_level = 'HIGH'
        else:
            recommendation = 'HOLD'
            confidence = base_confidence - 0.1
            risk_level = 'MEDIUM'
        
        # Add target prices (enhanced calculation based on volatility)
        avg_price = price_stats['average']
        volatility_factor = price_stats['volatility_percent'] / 100
        
        # More conservative targets for high-volatility products
        buy_discount = 0.1 + (volatility_factor * 0.1)  # 10-20% discount
        sell_premium = 0.15 + (volatility_factor * 0.15)  # 15-30% premium
        
        target_buy = round(avg_price * (1 - buy_discount), 2)
        target_sell = round(avg_price * (1 + sell_premium), 2)
        
        print(f"   ✅ Recommendation: {recommendation} (confidence: {confidence:.2f}, risk: {risk_level})")
        
        return {
            'recommendation': recommendation,
            'confidence': round(confidence, 2),
            'risk_level': risk_level,
            'reasoning': reasoning,
            'target_prices': {
                'buy_below': target_buy,
                'sell_above': target_sell
            },
            'risk_level': 'HIGH' if price_stats['volatility_percent'] > 25 else 'MEDIUM' if price_stats['volatility_percent'] > 15 else 'LOW'
        }

    def _check_cached_analysis(self, pokequant_product_id: str) -> Optional[Dict[str, Any]]:
        """Check if a recent analysis exists in cache"""
        
        try:
            # Calculate cutoff time for cache expiry
            cutoff_time = datetime.now() - timedelta(hours=self.analysis_cache_hours)
            
            # Query for recent analysis
            result = self.supabase.table('pokequant_analyses').select('*').eq('pokequant_product_id', pokequant_product_id).gte('analysis_date', cutoff_time.isoformat()).order('analysis_date', desc=True).limit(1).execute()
            
            if not result.data:
                return None
            
            analysis_row = result.data[0]
            
            # Get the associated product info
            product_result = self.supabase.table('pokequant_products').select('*').eq('id', pokequant_product_id).execute()
            
            if not product_result.data:
                return None
            
            product_row = product_result.data[0]
            
            # Reconstruct the analysis format
            return {
                'product': {
                    'product': {
                        'type': product_row['product_type'],
                        'id': product_row['product_id'],
                        'name': product_row['product_name'],
                        'set_name': product_row['set_name'],
                        'display_name': product_row['product_name']
                    },
                    'found': True
                },
                'data_summary': {
                    'total_data_points': analysis_row['total_data_points'],
                    'date_range': {
                        'start': str(analysis_row['data_range_start']) if analysis_row['data_range_start'] else None,
                        'end': str(analysis_row['data_range_end']) if analysis_row['data_range_end'] else None
                    }
                },
                'metrics': analysis_row['metrics'],
                'recommendation': {
                    'recommendation': analysis_row['recommendation'],
                    'confidence': float(analysis_row['confidence_score']) if analysis_row['confidence_score'] else 0.0
                },
                'analysis_metadata': {
                    'pokequant_product_id': pokequant_product_id,
                    'analysis_date': str(analysis_row['analysis_date']),
                    'analysis_version': analysis_row['analysis_version'],
                    'cached': True
                }
            }
            
        except Exception as e:
            print(f"   ⚠️ Error checking cached analysis: {e}")
            return None
    
    def _store_analysis_results(self, pokequant_product_id: str, analysis: Dict[str, Any]) -> bool:
        """Store analysis results in pokequant_analyses table"""
        
        try:
            metrics = analysis.get('metrics', {})
            recommendation = analysis.get('recommendation', {})
            data_summary = analysis.get('data_summary', {})
            date_range = data_summary.get('date_range', {})
            
            # Prepare data for storage
            analysis_data = {
                'pokequant_product_id': pokequant_product_id,
                'metrics': metrics,
                'recommendation': recommendation.get('recommendation'),
                'confidence_score': recommendation.get('confidence', 0.0),
                'analysis_version': '1.0',
                'data_range_start': date_range.get('start'),
                'data_range_end': date_range.get('end'),
                'total_data_points': data_summary.get('total_data_points', 0)
            }
            
            # Insert into database
            result = self.supabase.table('pokequant_analyses').insert(analysis_data).execute()
            
            if result.data:
                print(f"   ✅ Analysis results stored successfully")
                return True
            else:
                print(f"   ⚠️ No data returned from analysis storage")
                return False
                
        except Exception as e:
            print(f"   ❌ Error storing analysis results: {e}")
            return False
    
    def get_analysis_history(self, product_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get analysis history for a product"""
        
        try:
            # Find the product first
            product_info = self._find_product(product_name)
            if not product_info['found']:
                return []
            
            product = product_info['product']
            pokequant_product_id = self.price_data_service.ensure_product_exists(
                product['type'], product['id'], product['name'], product.get('set_name')
            )
            
            # Get analysis history
            result = self.supabase.table('pokequant_analyses').select('*').eq('pokequant_product_id', pokequant_product_id).order('analysis_date', desc=True).limit(limit).execute()
            
            history = []
            for row in result.data:
                history.append({
                    'analysis_date': row['analysis_date'],
                    'recommendation': row['recommendation'],
                    'confidence_score': float(row['confidence_score']) if row['confidence_score'] else 0.0,
                    'total_data_points': row['total_data_points'],
                    'data_range': {
                        'start': row['data_range_start'],
                        'end': row['data_range_end']
                    },
                    'metrics': row['metrics']
                })
            
            return history
            
        except Exception as e:
            print(f"Error getting analysis history: {e}")
            return []

def main():
    """CLI interface for PokeQuant analysis"""
    
    parser = argparse.ArgumentParser(description="PokeQuant: Complete Pokemon card and sealed product analysis")
    parser.add_argument('product_name', help='Name of the product to analyze')
    parser.add_argument('--force-refresh', action='store_true', help='Force data refresh even if recent data exists')
    parser.add_argument('--force-analysis', action='store_true', help='Force analysis even if cached analysis exists')
    parser.add_argument('--max-age', type=int, default=7, help='Maximum age in days before data is stale')
    parser.add_argument('--cache-hours', type=int, default=24, help='Cache analysis results for this many hours')
    parser.add_argument('--history', action='store_true', help='Show analysis history instead of running new analysis')
    parser.add_argument('--use-llm', action='store_true', help='Enable LLM-enhanced filtering (requires OpenAI API key)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    orchestrator = PokeQuantOrchestrator(max_age_days=args.max_age, analysis_cache_hours=args.cache_hours, use_llm=args.use_llm)
    
    # Show analysis history instead of running new analysis
    if args.history:
        print(f"📈 Analysis History for: {args.product_name}")
        print("=" * 60)
        
        history = orchestrator.get_analysis_history(args.product_name)
        
        if not history:
            print("No analysis history found for this product.")
            return
        
        for i, analysis in enumerate(history, 1):
            print(f"\n#{i} Analysis Date: {analysis['analysis_date']}")
            print(f"   Recommendation: {analysis['recommendation']}")
            print(f"   Confidence: {analysis['confidence_score']:.2f}")
            print(f"   Data Points: {analysis['total_data_points']}")
            print(f"   Date Range: {analysis['data_range']['start']} to {analysis['data_range']['end']}")
        
        return
    
    # Run the complete analysis
    result = orchestrator.analyze_product(args.product_name, force_refresh=args.force_refresh, force_analysis=args.force_analysis)
    
    if result['success']:
        # Print clean summary
        print("\n" + "="*60)
        print("🎯 POKEQUANT ANALYSIS SUMMARY")
        print("="*60)
        
        # Show if we used cached analysis
        if result.get('used_cached_analysis'):
            print("💾 Using cached analysis results")
            print("   (Use --force-analysis to force fresh analysis)")
        else:
            print("🔄 Fresh analysis completed")
            print("   (Results cached for next 24 hours)")
        
        final = result['final_analysis']
        product = final['product']['product']
        metrics = final.get('metrics', {})
        rec = final.get('recommendation', {})
        
        print(f"\nProduct: {product['display_name']}")
        print(f"Type: {product['type'].title()}")
        
        # Show analysis metadata
        if 'analysis_metadata' in final:
            meta = final['analysis_metadata']
            print(f"Analysis Date: {meta.get('analysis_date', 'Unknown')}")
            if meta.get('cached'):
                print("📊 Source: Cached Analysis")
            else:
                print("📊 Source: Fresh Analysis")
        
        if 'price_stats' in metrics:
            stats = metrics['price_stats']
            print(f"\nPrice Analysis:")
            print(f"  Average Price: ${stats['average']}")
            print(f"  Price Range: ${stats['minimum']} - ${stats['maximum']}")
            print(f"  Volatility: {stats['volatility_percent']:.1f}%")
        
        if 'trend_analysis' in metrics:
            trend = metrics['trend_analysis']
            print(f"\nTrend: {trend['direction'].title()} ({trend['strength']:.1f}%)")
        
        if rec:
            print(f"\n🎯 Recommendation: {rec['recommendation']}")
            print(f"Confidence: {rec['confidence']:.0%}")
            
            # Handle both fresh and cached analysis formats
            if 'risk_level' in rec:
                print(f"Risk Level: {rec['risk_level']}")
            
            if rec.get('reasoning'):
                print("\nReasoning:")
                for reason in rec['reasoning']:
                    print(f"  • {reason}")
            
            if 'target_prices' in rec:
                targets = rec['target_prices']
                print(f"\nTarget Prices:")
                print(f"  Buy Below: ${targets['buy_below']}")
                print(f"  Sell Above: ${targets['sell_above']}")
        
        # Show helpful commands
        print(f"\n💡 Helpful Commands:")
        print(f"  View history: python -m quant.pokequant_main \"{args.product_name}\" --history")
        print(f"  Force refresh: python -m quant.pokequant_main \"{args.product_name}\" --force-analysis")
    
    else:
        print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")
        if args.verbose and 'stages' in result:
            print("\nStage Details:")
            for stage, data in result['stages'].items():
                print(f"  {stage}: {data}")

if __name__ == "__main__":
    main() 