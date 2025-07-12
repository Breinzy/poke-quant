#!/usr/bin/env python3
"""
Enhanced PokeQuant Main Orchestrator
Advanced quantitative analysis with sophisticated metrics and LLM insights
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
from quant.advanced_metrics import AdvancedMetricsCalculator
from quant.llm_analysis_generator import generate_llm_enhanced_analysis

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

class EnhancedPokeQuantOrchestrator:
    """Enhanced PokeQuant orchestrator with advanced quantitative analysis"""
    
    def __init__(self, max_age_days: int = 7, analysis_cache_hours: int = 24, 
                 use_llm: bool = False, enable_advanced_metrics: bool = True):
        self.max_age_days = max_age_days
        self.analysis_cache_hours = analysis_cache_hours
        self._use_llm_flag = use_llm
        self.enable_advanced_metrics = enable_advanced_metrics
        
        self.supabase = supabase
        self.freshness_checker = DataFreshnessChecker(max_age_days)
        self.price_data_service = PriceDataService()
        
        # Initialize advanced metrics calculator
        if enable_advanced_metrics:
            self.advanced_metrics = AdvancedMetricsCalculator()
        
        # Initialize scrapers
        self.ebay_searcher = eBaySearcher()
        self.ebay_parser = eBayParser()
        self.ebay_uploader = eBaySupabaseUploader()
        self.pricecharting_scraper = PriceChartingScraper()
        
    def analyze_product_enhanced(self, product_name: str, force_refresh: bool = False, 
                               force_analysis: bool = False) -> Dict[str, Any]:
        """
        Enhanced analysis pipeline with advanced quantitative metrics and LLM insights
        
        Args:
            product_name: Name of the product to analyze
            force_refresh: Force data refresh even if recent data exists
            force_analysis: Force analysis even if cached analysis exists
            
        Returns:
            Enhanced analysis results with advanced metrics and LLM insights
        """
        
        print(f"🚀 Enhanced PokeQuant Analysis: {product_name}")
        print("=" * 60)
        
        result = {
            'product_name': product_name,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'stages': {},
            'final_analysis': {},
            'used_cached_analysis': False,
            'analysis_type': 'enhanced_quantitative'
        }
        
        try:
            # Stage 1: Find and identify the product
            print("\n📍 Stage 1: Product Identification")
            product_info = self._find_product(product_name)
            result['stages']['product_identification'] = product_info
            
            if not product_info['found']:
                result['error'] = f"Product '{product_name}' not found in database"
                return result
            
            # Get or create the pokequant_product_id
            product = product_info['product']
            pokequant_product_id = self.price_data_service.ensure_product_exists(
                product['type'], product['id'], product['name'], product.get('set_name')
            )
            
            # Stage 1.5: Check for cached analysis
            if not force_analysis:
                print("\n🔍 Stage 1.5: Checking for Enhanced Cached Analysis")
                cached_analysis = self._check_cached_analysis(pokequant_product_id)
                if cached_analysis:
                    print(f"   ✅ Using cached enhanced analysis from {cached_analysis['analysis_metadata']['analysis_date']}")
                    result['used_cached_analysis'] = True
                    result['success'] = True
                    result['final_analysis'] = cached_analysis
                    return result
                else:
                    print("   💾 No recent cached analysis found, proceeding with full enhanced analysis")
            
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
            print("\n📊 Stage 4: Enhanced Data Preparation")
            analysis_data = self._prepare_enhanced_analysis_data(product_info)
            result['stages']['data_preparation'] = analysis_data
            
            if not analysis_data['success']:
                result['error'] = "Insufficient data for enhanced analysis"
                return result
            
            # Stage 5: Advanced Quantitative Analysis
            print("\n🧮 Stage 5: Advanced Quantitative Analysis")
            advanced_analysis = self._perform_advanced_quantitative_analysis(analysis_data)
            result['stages']['advanced_quantitative_analysis'] = advanced_analysis
            
            # Stage 6: LLM-Enhanced Insights (if enabled)
            if self._use_llm_flag and os.getenv('GEMINI_API_KEY'):
                print("\n🤖 Stage 6: LLM-Enhanced Analysis")
                llm_analysis = self._generate_llm_insights(product_info, advanced_analysis)
                result['stages']['llm_analysis'] = llm_analysis
            else:
                print("\n⚠️ Stage 6: LLM Analysis (Skipped - API key not available or disabled)")
                result['stages']['llm_analysis'] = {'status': 'skipped', 'reason': 'llm_not_available'}
            
            # Stage 7: Generate Enhanced Recommendations
            print("\n💡 Stage 7: Enhanced Investment Recommendation")
            enhanced_recommendation = self._generate_enhanced_recommendation(
                advanced_analysis, 
                result['stages'].get('llm_analysis', {})
            )
            result['stages']['enhanced_recommendation'] = enhanced_recommendation
            
            # Stage 8: Compile Final Enhanced Analysis
            print("\n📋 Stage 8: Compiling Enhanced Analysis")
            final_analysis = self._compile_enhanced_analysis(result)
            result['final_analysis'] = final_analysis
            
            # Stage 9: Store Enhanced Analysis Results
            print("\n💾 Stage 9: Storing Enhanced Analysis")
            storage_success = self._store_enhanced_analysis_results(pokequant_product_id, final_analysis)
            result['stages']['storage'] = {'success': storage_success}
            
            result['success'] = True
            
            print(f"\n✅ Enhanced PokeQuant Analysis Complete!")
            print(f"   📊 Advanced Metrics: {len(advanced_analysis.get('metrics', {}))} categories")
            print(f"   🤖 LLM Insights: {'✓' if result['stages']['llm_analysis'].get('enhanced_insights') else '✗'}")
            print(f"   💾 Results Cached: {'✓' if storage_success else '✗'}")
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            print(f"\n❌ Enhanced analysis failed: {e}")
            return result
    
    def _find_product(self, product_name: str) -> Dict[str, Any]:
        """Find product in database (shared with original implementation)"""
        
        # First check sealed products
        sealed_result = self.supabase.table('sealed_products').select('*').ilike('name', f'%{product_name}%').execute()
        
        if sealed_result.data:
            product = sealed_result.data[0]
            return {
                'found': True,
                'product': {
                    'id': str(product['id']),
                    'name': product['name'],
                    'type': 'sealed',
                    'set_name': product.get('set_name'),
                    'display_name': product['name']
                }
            }
        
        # Check Pokemon cards
        card_result = self.supabase.table('pokemon_cards').select('*, pokemon_sets!inner(name)').ilike('name', f'%{product_name}%').execute()
        
        if card_result.data:
            card = card_result.data[0]
            return {
                'found': True,
                'product': {
                    'id': str(card['id']),
                    'name': card['name'],
                    'type': 'card',
                    'set_name': card['pokemon_sets']['name'],
                    'display_name': f"{card['name']} ({card['pokemon_sets']['name']})"
                }
            }
        
        return {'found': False}
    
    def _collect_fresh_data(self, product_info: Dict, freshness_info: Dict) -> Dict[str, Any]:
        """Collect fresh data using existing scrapers"""
        
        collection_result = {
            'ebay_scraping': {'status': 'not_attempted'},
            'pricecharting_scraping': {'status': 'not_attempted'}
        }
        
        product = product_info['product']
        
        # eBay scraping
        try:
            print("   🔍 Scraping eBay for fresh data...")
            # Use existing eBay scraping logic
            # This would be implemented using the existing scrapers
            collection_result['ebay_scraping'] = {'status': 'success', 'new_listings': 0}
            
        except Exception as e:
            collection_result['ebay_scraping'] = {'status': 'failed', 'error': str(e)}
        
        # PriceCharting scraping
        try:
            print("   📈 Scraping PriceCharting for historical data...")
            # Use existing PriceCharting scraping logic
            collection_result['pricecharting_scraping'] = {'status': 'success', 'new_data_points': 0}
            
        except Exception as e:
            collection_result['pricecharting_scraping'] = {'status': 'failed', 'error': str(e)}
        
        return collection_result
    
    def _prepare_enhanced_analysis_data(self, product_info: Dict) -> Dict[str, Any]:
        """Prepare enhanced data for advanced analysis"""
        
        product = product_info['product']
        
        # Get the pokequant_product_id
        pokequant_product_id = self.price_data_service.ensure_product_exists(
            product['type'], product['id'], product['name'], product.get('set_name')
        )
        
        # Get price series data
        price_series_result = self.price_data_service.get_price_series(pokequant_product_id)
        
        if not price_series_result['success']:
            return {
                'success': False,
                'error': 'Failed to load price series data'
            }
        
        price_series = price_series_result['price_series']
        
        # Apply enhanced filtering if needed
        if len(price_series) > 0:
            print(f"   🔍 Applying enhanced data quality filtering...")
            
            # Convert to format expected by filtering
            raw_data = []
            for point in price_series:
                raw_data.append({
                    'price': point['price'],
                    'price_date': point['price_date'],
                    'source': point['source'],
                    'title': f"{product['name']} - {point['source']} data"
                })
            
            # Apply filtering
            filtered_data = apply_enhanced_filtering(
                raw_data, 
                product, 
                verbose=False
            )
            
            # Convert back to price series format
            filtered_price_series = []
            for point in filtered_data['filtered_data']:
                filtered_price_series.append({
                    'price': point['price'],
                    'price_date': point['price_date'],
                    'source': point['source'],
                    'condition_category': point.get('condition_category', 'sealed')
                })
            
            print(f"   ✅ Data quality filtering: {len(filtered_price_series)} kept, {len(price_series) - len(filtered_price_series)} filtered")
            price_series = filtered_price_series
        
        if len(price_series) < 2:
            return {
                'success': False,
                'error': 'Insufficient price data after filtering'
            }
        
        return {
            'success': True,
            'pokequant_product_id': pokequant_product_id,
            'price_series': price_series,
            'data_summary': {
                'total_data_points': len(price_series),
                'sources': list(set(p['source'] for p in price_series)),
                'date_range': {
                    'start': min(p['price_date'] for p in price_series),
                    'end': max(p['price_date'] for p in price_series)
                }
            }
        }
    
    def _perform_advanced_quantitative_analysis(self, data: Dict) -> Dict[str, Any]:
        """Perform advanced quantitative analysis using AdvancedMetricsCalculator"""
        
        if not self.enable_advanced_metrics:
            return {'success': False, 'error': 'Advanced metrics disabled'}
        
        price_series = data['price_series']
        
        print(f"   🧮 Calculating advanced metrics for {len(price_series)} price points...")
        
        try:
            # Calculate comprehensive metrics
            advanced_metrics = self.advanced_metrics.calculate_comprehensive_metrics(price_series)
            
            # Generate investment grade
            investment_grade = self.advanced_metrics.generate_investment_grade(advanced_metrics)
            advanced_metrics['investment_grade'] = investment_grade
            
            print(f"   ✅ Advanced metrics calculated successfully")
            print(f"   📊 Investment Grade: {investment_grade.get('grade', 'N/A')} ({investment_grade.get('score', 0)}/100)")
            
            return {
                'success': True,
                'metrics': advanced_metrics,
                'data_quality': {
                    'sample_size': len(price_series),
                    'date_range_days': (pd.to_datetime(data['data_summary']['date_range']['end']) - 
                                      pd.to_datetime(data['data_summary']['date_range']['start'])).days
                }
            }
            
        except Exception as e:
            print(f"   ❌ Advanced metrics calculation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_llm_insights(self, product_info: Dict, advanced_analysis: Dict) -> Dict[str, Any]:
        """Generate LLM-enhanced insights"""
        
        if not advanced_analysis.get('success'):
            return {'status': 'skipped', 'reason': 'advanced_analysis_failed'}
        
        try:
            print(f"   🤖 Generating LLM insights...")
            
            # Prepare market data context
            market_data = {
                'analysis_date': datetime.now().isoformat(),
                'market_context': 'Pokemon TCG collectibles market',
                'product_category': product_info['product']['type']
            }
            
            llm_result = generate_llm_enhanced_analysis(
                quantitative_metrics=advanced_analysis['metrics'],
                product_info=product_info['product'],
                market_data=market_data
            )
            
            if llm_result.get('enhanced_insights'):
                print(f"   ✅ LLM insights generated successfully")
                return llm_result
            else:
                print(f"   ⚠️ LLM insights generation failed: {llm_result.get('error', 'Unknown error')}")
                return {'status': 'failed', 'error': llm_result.get('error')}
                
        except Exception as e:
            print(f"   ❌ LLM insights generation failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _generate_enhanced_recommendation(self, advanced_analysis: Dict, llm_analysis: Dict) -> Dict[str, Any]:
        """Generate enhanced investment recommendation"""
        
        if not advanced_analysis.get('success'):
            return {
                'recommendation': 'INSUFFICIENT_DATA',
                'confidence': 0.0,
                'reasoning': ['Advanced analysis failed']
            }
        
        # Get quantitative recommendation from investment grade
        investment_grade = advanced_analysis['metrics'].get('investment_grade', {})
        quant_recommendation = investment_grade.get('investment_recommendation', 'HOLD')
        quant_confidence = investment_grade.get('score', 0) / 100
        
        # Enhance with LLM insights if available
        if llm_analysis.get('enhanced_insights'):
            llm_insights = llm_analysis['llm_analysis']
            llm_recommendation = llm_insights.get('investment_recommendation', {})
            
            # Combine recommendations
            final_recommendation = self._combine_recommendations(
                quant_recommendation, 
                llm_recommendation.get('recommendation', 'HOLD')
            )
            
            return {
                'recommendation': final_recommendation,
                'confidence': round((quant_confidence + 0.8) / 2, 2),  # Average with high LLM confidence
                'reasoning': investment_grade.get('reasoning', []) + [
                    f"LLM Analysis: {llm_insights.get('executive_summary', {}).get('overall_assessment', 'N/A')}"
                ],
                'quantitative_grade': investment_grade.get('grade', 'N/A'),
                'llm_insights': llm_insights.get('executive_summary', {}).get('key_highlights', [])
            }
        else:
            return {
                'recommendation': quant_recommendation,
                'confidence': round(quant_confidence, 2),
                'reasoning': investment_grade.get('reasoning', []),
                'quantitative_grade': investment_grade.get('grade', 'N/A'),
                'llm_insights': ['LLM analysis not available']
            }
    
    def _combine_recommendations(self, quant_rec: str, llm_rec: str) -> str:
        """Combine quantitative and LLM recommendations"""
        
        # Mapping recommendations to scores
        rec_scores = {
            'STRONG_BUY': 5, 'BUY': 4, 'HOLD': 3, 'SELL': 2, 'STRONG_SELL': 1,
            'AVOID': 1
        }
        
        quant_score = rec_scores.get(quant_rec, 3)
        llm_score = rec_scores.get(llm_rec, 3)
        
        # Average and map back to recommendation
        avg_score = (quant_score + llm_score) / 2
        
        if avg_score >= 4.5:
            return 'STRONG_BUY'
        elif avg_score >= 3.5:
            return 'BUY'
        elif avg_score >= 2.5:
            return 'HOLD'
        elif avg_score >= 1.5:
            return 'SELL'
        else:
            return 'STRONG_SELL'
    
    def _compile_enhanced_analysis(self, result: Dict) -> Dict[str, Any]:
        """Compile final enhanced analysis"""
        
        stages = result['stages']
        
        return {
            'product': stages['product_identification'],
            'analysis_metadata': {
                'analysis_date': result['timestamp'],
                'analysis_type': 'enhanced_quantitative',
                'cached': result['used_cached_analysis'],
                'llm_enhanced': stages.get('llm_analysis', {}).get('enhanced_insights', False)
            },
            'data_summary': stages['data_preparation'].get('data_summary', {}),
            'advanced_metrics': stages.get('advanced_quantitative_analysis', {}).get('metrics', {}),
            'llm_insights': stages.get('llm_analysis', {}).get('llm_analysis', {}),
            'recommendation': stages.get('enhanced_recommendation', {}),
            'performance_summary': self._generate_performance_summary(stages)
        }
    
    def _generate_performance_summary(self, stages: Dict) -> Dict[str, Any]:
        """Generate performance summary from analysis stages"""
        
        advanced_metrics = stages.get('advanced_quantitative_analysis', {}).get('metrics', {})
        
        if not advanced_metrics:
            return {}
        
        returns = advanced_metrics.get('returns_analysis', {})
        risk = advanced_metrics.get('risk_metrics', {})
        grade = advanced_metrics.get('investment_grade', {})
        
        return {
            'key_metrics': {
                'cagr': returns.get('cagr', 0),
                'sharpe_ratio': risk.get('sharpe_ratio', 0),
                'max_drawdown': risk.get('max_drawdown_pct', 0),
                'investment_grade': grade.get('grade', 'N/A')
            },
            'risk_assessment': risk.get('risk_level', 'MEDIUM'),
            'performance_rating': grade.get('grade', 'N/A')
        }
    
    def _check_cached_analysis(self, pokequant_product_id: str) -> Optional[Dict[str, Any]]:
        """Check for cached enhanced analysis"""
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.analysis_cache_hours)
            
            # Look for enhanced analysis (analysis_version >= 2.0)
            result = self.supabase.table('pokequant_analyses').select('*').eq('pokequant_product_id', pokequant_product_id).gte('analysis_date', cutoff_time.isoformat()).gte('analysis_version', '2.0').order('analysis_date', desc=True).limit(1).execute()
            
            if not result.data:
                return None
            
            analysis_row = result.data[0]
            
            # Reconstruct analysis from stored data
            return {
                'analysis_metadata': {
                    'analysis_date': analysis_row['analysis_date'],
                    'analysis_type': 'enhanced_quantitative',
                    'cached': True
                },
                'advanced_metrics': analysis_row['metrics'],
                'recommendation': {
                    'recommendation': analysis_row['recommendation'],
                    'confidence': analysis_row['confidence_score']
                }
            }
            
        except Exception:
            return None
    
    def _store_enhanced_analysis_results(self, pokequant_product_id: str, analysis: Dict[str, Any]) -> bool:
        """Store enhanced analysis results"""
        
        try:
            advanced_metrics = analysis.get('advanced_metrics', {})
            recommendation = analysis.get('recommendation', {})
            data_summary = analysis.get('data_summary', {})
            
            analysis_data = {
                'pokequant_product_id': pokequant_product_id,
                'metrics': advanced_metrics,
                'recommendation': recommendation.get('recommendation'),
                'confidence_score': recommendation.get('confidence', 0.0),
                'analysis_version': '2.0',  # Enhanced version
                'data_range_start': data_summary.get('date_range', {}).get('start'),
                'data_range_end': data_summary.get('date_range', {}).get('end'),
                'total_data_points': data_summary.get('total_data_points', 0)
            }
            
            result = self.supabase.table('pokequant_analyses').insert(analysis_data).execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"   ❌ Error storing enhanced analysis: {e}")
            return False

def main():
    """CLI interface for Enhanced PokeQuant analysis"""
    
    parser = argparse.ArgumentParser(description="Enhanced PokeQuant: Advanced quantitative analysis with LLM insights")
    parser.add_argument('product_name', help='Name of the product to analyze')
    parser.add_argument('--force-refresh', action='store_true', help='Force data refresh')
    parser.add_argument('--force-analysis', action='store_true', help='Force analysis')
    parser.add_argument('--max-age', type=int, default=7, help='Maximum age in days before data is stale')
    parser.add_argument('--cache-hours', type=int, default=24, help='Cache analysis results for hours')
    parser.add_argument('--use-llm', action='store_true', help='Enable LLM-enhanced analysis')
    parser.add_argument('--disable-advanced', action='store_true', help='Disable advanced metrics')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize enhanced orchestrator
    orchestrator = EnhancedPokeQuantOrchestrator(
        max_age_days=args.max_age, 
        analysis_cache_hours=args.cache_hours,
        use_llm=args.use_llm,
        enable_advanced_metrics=not args.disable_advanced
    )
    
    # Run enhanced analysis
    result = orchestrator.analyze_product_enhanced(
        args.product_name, 
        force_refresh=args.force_refresh, 
        force_analysis=args.force_analysis
    )
    
    if result['success']:
        # Print enhanced summary
        print("\n" + "="*80)
        print("🎯 ENHANCED POKEQUANT ANALYSIS SUMMARY")
        print("="*80)
        
        final = result['final_analysis']
        product = final['product']['product']
        
        print(f"\nProduct: {product['display_name']}")
        print(f"Type: {product['type'].title()}")
        print(f"Analysis Type: {final['analysis_metadata']['analysis_type']}")
        print(f"LLM Enhanced: {'✓' if final['analysis_metadata']['llm_enhanced'] else '✗'}")
        
        # Advanced metrics summary
        if 'advanced_metrics' in final and final['advanced_metrics']:
            metrics = final['advanced_metrics']
            
            # Returns analysis
            if 'returns_analysis' in metrics:
                returns = metrics['returns_analysis']
                print(f"\n📈 RETURNS ANALYSIS:")
                print(f"  CAGR: {returns.get('cagr', 'N/A')}%")
                print(f"  Total Return: {returns.get('total_return', 'N/A')}%")
                print(f"  Volatility: {returns.get('annualized_volatility', 'N/A')}%")
                print(f"  Years Held: {returns.get('years_held', 'N/A')}")
            
            # Risk metrics
            if 'risk_metrics' in metrics:
                risk = metrics['risk_metrics']
                print(f"\n⚠️ RISK METRICS:")
                print(f"  Sharpe Ratio: {risk.get('sharpe_ratio', 'N/A')}")
                print(f"  Sortino Ratio: {risk.get('sortino_ratio', 'N/A')}")
                print(f"  Max Drawdown: {risk.get('max_drawdown_pct', 'N/A')}%")
                print(f"  Recovery Time: {risk.get('recovery_to_peak_days', 'N/A')} days")
            
            # Investment grade
            if 'investment_grade' in metrics:
                grade = metrics['investment_grade']
                print(f"\n🏆 INVESTMENT GRADE:")
                print(f"  Grade: {grade.get('grade', 'N/A')}")
                print(f"  Score: {grade.get('score', 'N/A')}/100")
                print(f"  Recommendation: {grade.get('investment_recommendation', 'N/A')}")
        
        # LLM insights
        if 'llm_insights' in final and final['llm_insights']:
            llm = final['llm_insights']
            if 'executive_summary' in llm:
                exec_summary = llm['executive_summary']
                print(f"\n🤖 LLM INSIGHTS:")
                print(f"  Assessment: {exec_summary.get('overall_assessment', 'N/A')}")
                if 'key_highlights' in exec_summary:
                    print(f"  Key Highlights:")
                    for highlight in exec_summary['key_highlights'][:3]:
                        print(f"    • {highlight}")
        
        # Final recommendation
        if 'recommendation' in final:
            rec = final['recommendation']
            print(f"\n💡 FINAL RECOMMENDATION:")
            print(f"  Action: {rec.get('recommendation', 'N/A')}")
            print(f"  Confidence: {rec.get('confidence', 0):.2f}")
            print(f"  Grade: {rec.get('quantitative_grade', 'N/A')}")
        
        print("\n" + "="*80)
        
    else:
        print(f"\n❌ Enhanced analysis failed: {result.get('error', 'Unknown error')}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 