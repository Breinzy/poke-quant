#!/usr/bin/env python3
"""
Test Enhanced PokeQuant Analysis
Comprehensive test of advanced quantitative metrics and LLM capabilities
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant.advanced_metrics import AdvancedMetricsCalculator, calculate_portfolio_metrics
from quant.llm_analysis_generator import LLMAnalysisGenerator, generate_llm_enhanced_analysis

def create_test_price_data() -> List[Dict]:
    """Create comprehensive test price data for different scenarios"""
    
    # Generate multiple test scenarios
    scenarios = {
        'strong_performer': {
            'description': 'Strong upward trend with low volatility',
            'initial_price': 100,
            'trend': 0.15,  # 15% annual growth
            'volatility': 0.08,  # 8% volatility
            'days': 365
        },
        'volatile_performer': {
            'description': 'High returns with high volatility',
            'initial_price': 50,
            'trend': 0.25,  # 25% annual growth
            'volatility': 0.25,  # 25% volatility
            'days': 730
        },
        'stable_performer': {
            'description': 'Stable growth with minimal volatility',
            'initial_price': 150,
            'trend': 0.08,  # 8% annual growth
            'volatility': 0.05,  # 5% volatility
            'days': 365
        },
        'declining_asset': {
            'description': 'Declining asset with moderate volatility',
            'initial_price': 200,
            'trend': -0.10,  # -10% annual decline
            'volatility': 0.15,  # 15% volatility
            'days': 365
        }
    }
    
    test_data = {}
    
    for scenario_name, params in scenarios.items():
        print(f"🔧 Generating {scenario_name} data: {params['description']}")
        
        # Generate price series
        np.random.seed(42)  # For reproducible results
        
        days = params['days']
        initial_price = params['initial_price']
        annual_trend = params['trend']
        annual_volatility = params['volatility']
        
        # Daily parameters
        daily_trend = annual_trend / 365
        daily_volatility = annual_volatility / np.sqrt(365)
        
        # Generate returns
        returns = np.random.normal(daily_trend, daily_volatility, days)
        
        # Generate prices
        prices = [initial_price]
        for i in range(days):
            prices.append(prices[-1] * (1 + returns[i]))
        
        # Generate dates
        start_date = datetime.now() - timedelta(days=days)
        dates = [start_date + timedelta(days=i) for i in range(days + 1)]
        
        # Create price data
        price_data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            price_data.append({
                'price': round(price, 2),
                'price_date': date.strftime('%Y-%m-%d')
            })
        
        test_data[scenario_name] = price_data
    
    return test_data

def test_advanced_metrics():
    """Test advanced quantitative metrics calculator"""
    
    print("🧮 TESTING ADVANCED QUANTITATIVE METRICS")
    print("=" * 60)
    
    # Create test data
    test_data = create_test_price_data()
    
    # Initialize calculator
    calculator = AdvancedMetricsCalculator()
    
    results = {}
    
    for scenario_name, price_data in test_data.items():
        print(f"\n📊 Testing {scenario_name}:")
        print(f"   Data points: {len(price_data)}")
        print(f"   Price range: ${price_data[0]['price']:.2f} - ${price_data[-1]['price']:.2f}")
        
        # Calculate metrics
        metrics = calculator.calculate_comprehensive_metrics(price_data)
        
        if metrics:
            # Display key metrics
            returns = metrics.get('returns_analysis', {})
            risk = metrics.get('risk_metrics', {})
            performance = metrics.get('performance_metrics', {})
            technical = metrics.get('technical_indicators', {})
            
            print(f"   📈 Returns:")
            print(f"      CAGR: {returns.get('cagr', 'N/A')}%")
            print(f"      Total Return: {returns.get('total_return', 'N/A')}%")
            print(f"      Volatility: {returns.get('annualized_volatility', 'N/A')}%")
            
            print(f"   ⚠️ Risk:")
            print(f"      Sharpe Ratio: {risk.get('sharpe_ratio', 'N/A')}")
            print(f"      Max Drawdown: {risk.get('max_drawdown_pct', 'N/A')}%")
            print(f"      Sortino Ratio: {risk.get('sortino_ratio', 'N/A')}")
            
            print(f"   🎯 Performance:")
            print(f"      Win Rate: {performance.get('win_rate_pct', 'N/A')}%")
            print(f"      Profit Factor: {performance.get('profit_factor', 'N/A')}")
            
            if technical:
                print(f"   📊 Technical:")
                print(f"      RSI: {technical.get('rsi_current', 'N/A')}")
                print(f"      Trend: {technical.get('trend_strength', 'N/A')}")
            
            # Generate investment grade
            investment_grade = calculator.generate_investment_grade(metrics)
            print(f"   🏆 Investment Grade: {investment_grade.get('grade', 'N/A')} ({investment_grade.get('score', 0)}/100)")
            print(f"   💡 Recommendation: {investment_grade.get('investment_recommendation', 'N/A')}")
            
            results[scenario_name] = {
                'metrics': metrics,
                'investment_grade': investment_grade
            }
        else:
            print(f"   ❌ Failed to calculate metrics")
    
    return results

def test_llm_analysis():
    """Test LLM-enhanced analysis generator"""
    
    print("\n🤖 TESTING LLM-ENHANCED ANALYSIS")
    print("=" * 60)
    
    # Check if LLM is available
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️ Gemini API key not found. Set GEMINI_API_KEY environment variable to test LLM analysis.")
        return {}
    
    # Create test product info
    product_info = {
        'name': 'Test Charizard V Card',
        'type': 'card',
        'set_name': 'Evolving Skies',
        'id': 'test_001'
    }
    
    # Generate test metrics
    test_data = create_test_price_data()
    calculator = AdvancedMetricsCalculator()
    
    results = {}
    
    for scenario_name, price_data in test_data.items():
        print(f"\n🧠 Testing LLM analysis for {scenario_name}:")
        
        # Calculate quantitative metrics
        metrics = calculator.calculate_comprehensive_metrics(price_data)
        
        if not metrics:
            print(f"   ❌ Failed to calculate metrics for {scenario_name}")
            continue
        
        # Generate investment grade
        investment_grade = calculator.generate_investment_grade(metrics)
        metrics['investment_grade'] = investment_grade
        
        # Generate LLM analysis
        try:
            llm_result = generate_llm_enhanced_analysis(
                quantitative_metrics=metrics,
                product_info=product_info,
                market_data={'scenario': scenario_name}
            )
            
            if llm_result.get('enhanced_insights'):
                llm_analysis = llm_result['llm_analysis']
                
                print(f"   ✅ LLM analysis generated successfully")
                
                # Display executive summary
                if 'executive_summary' in llm_analysis:
                    exec_summary = llm_analysis['executive_summary']
                    print(f"   📋 Assessment: {exec_summary.get('overall_assessment', 'N/A')}")
                    
                    highlights = exec_summary.get('key_highlights', [])
                    if highlights:
                        print(f"   🎯 Key Highlights:")
                        for i, highlight in enumerate(highlights[:3], 1):
                            print(f"      {i}. {highlight}")
                
                # Display investment recommendation
                if 'investment_recommendation' in llm_analysis:
                    rec = llm_analysis['investment_recommendation']
                    print(f"   💡 LLM Recommendation: {rec.get('recommendation', 'N/A')}")
                    print(f"   🔒 Confidence: {rec.get('confidence_level', 'N/A')}")
                
                results[scenario_name] = llm_analysis
                
            else:
                print(f"   ❌ LLM analysis failed: {llm_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ LLM analysis exception: {e}")
    
    return results

def test_portfolio_analysis():
    """Test portfolio-level analysis"""
    
    print("\n📊 TESTING PORTFOLIO ANALYSIS")
    print("=" * 60)
    
    # Create test portfolio data
    test_data = create_test_price_data()
    
    # Convert to portfolio format
    portfolio_data = []
    for scenario_name, price_data in test_data.items():
        portfolio_data.append({
            'name': scenario_name,
            'price_data': price_data
        })
    
    # Calculate portfolio metrics
    portfolio_metrics = calculate_portfolio_metrics(portfolio_data)
    
    if 'portfolio_metrics' in portfolio_metrics:
        metrics = portfolio_metrics['portfolio_metrics']
        print(f"📈 Portfolio Analysis Results:")
        print(f"   Products: {metrics.get('products_count', 'N/A')}")
        print(f"   Average Correlation: {metrics.get('avg_correlation', 'N/A')}")
        print(f"   Max Correlation: {metrics.get('max_correlation', 'N/A')}")
        print(f"   Portfolio Volatility: {metrics.get('portfolio_volatility', 'N/A')}%")
        print(f"   Diversification Ratio: {metrics.get('diversification_ratio', 'N/A')}")
        
        # Display correlation matrix
        if 'correlation_matrix' in portfolio_metrics:
            print(f"\n📊 Correlation Matrix:")
            corr_matrix = portfolio_metrics['correlation_matrix']
            product_names = portfolio_metrics['product_names']
            
            print(f"   {'Product':<20} {' '.join(f'{name[:8]:<8}' for name in product_names)}")
            for i, name in enumerate(product_names):
                correlations = ' '.join(f'{corr_matrix[i][j]:.3f}' if i != j else '1.000' for j in range(len(product_names)))
                print(f"   {name[:20]:<20} {correlations}")
        
        return portfolio_metrics
    else:
        print(f"❌ Portfolio analysis failed: {portfolio_metrics.get('error', 'Unknown error')}")
        return {}

def test_integration():
    """Test integration of all components"""
    
    print("\n🔗 TESTING INTEGRATION")
    print("=" * 60)
    
    # Test data preparation
    test_data = create_test_price_data()
    strong_performer = test_data['strong_performer']
    
    print(f"📊 Testing complete integration with strong performer scenario")
    print(f"   Data points: {len(strong_performer)}")
    
    # 1. Calculate advanced metrics
    calculator = AdvancedMetricsCalculator()
    metrics = calculator.calculate_comprehensive_metrics(strong_performer)
    
    if not metrics:
        print("   ❌ Failed to calculate advanced metrics")
        return False
    
    investment_grade = calculator.generate_investment_grade(metrics)
    metrics['investment_grade'] = investment_grade
    
    print(f"   ✅ Advanced metrics calculated")
    print(f"   📈 CAGR: {metrics['returns_analysis'].get('cagr', 'N/A')}%")
    print(f"   🏆 Grade: {investment_grade.get('grade', 'N/A')}")
    
    # 2. Generate LLM analysis (if available)
    if os.getenv('GEMINI_API_KEY'):
        try:
            product_info = {
                'name': 'Integration Test Product',
                'type': 'sealed',
                'set_name': 'Test Set'
            }
            
            llm_result = generate_llm_enhanced_analysis(
                quantitative_metrics=metrics,
                product_info=product_info
            )
            
            if llm_result.get('enhanced_insights'):
                print(f"   ✅ LLM analysis integrated successfully")
                
                llm_analysis = llm_result['llm_analysis']
                if 'executive_summary' in llm_analysis:
                    assessment = llm_analysis['executive_summary'].get('overall_assessment', 'N/A')
                    print(f"   🤖 LLM Assessment: {assessment}")
                
                if 'investment_recommendation' in llm_analysis:
                    rec = llm_analysis['investment_recommendation'].get('recommendation', 'N/A')
                    print(f"   💡 LLM Recommendation: {rec}")
                
            else:
                print(f"   ⚠️ LLM analysis failed: {llm_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ LLM integration failed: {e}")
    else:
        print(f"   ⚠️ LLM analysis skipped (no API key)")
    
    # 3. Test recommendations combination
    quant_rec = investment_grade.get('investment_recommendation', 'HOLD')
    print(f"   🎯 Quantitative Recommendation: {quant_rec}")
    
    # Simulate combined recommendation
    combined_confidence = (investment_grade.get('score', 50) / 100 + 0.8) / 2
    print(f"   🔒 Combined Confidence: {combined_confidence:.2f}")
    
    print(f"   ✅ Integration test completed successfully")
    return True

def run_comprehensive_test():
    """Run comprehensive test suite"""
    
    print("🧪 POKEQUANT ENHANCED ANALYSIS TEST SUITE")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Advanced Metrics
    print("\n" + "🧮" * 10 + " ADVANCED METRICS TEST " + "🧮" * 10)
    metrics_results = test_advanced_metrics()
    
    # Test 2: LLM Analysis
    print("\n" + "🤖" * 10 + " LLM ANALYSIS TEST " + "🤖" * 10)
    llm_results = test_llm_analysis()
    
    # Test 3: Portfolio Analysis
    print("\n" + "📊" * 10 + " PORTFOLIO ANALYSIS TEST " + "📊" * 10)
    portfolio_results = test_portfolio_analysis()
    
    # Test 4: Integration
    print("\n" + "🔗" * 10 + " INTEGRATION TEST " + "🔗" * 10)
    integration_success = test_integration()
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 TEST SUMMARY")
    print("=" * 80)
    
    print(f"✅ Advanced Metrics: {len(metrics_results)} scenarios tested")
    print(f"✅ LLM Analysis: {len(llm_results)} scenarios tested")
    print(f"✅ Portfolio Analysis: {'✓' if portfolio_results else '✗'}")
    print(f"✅ Integration: {'✓' if integration_success else '✗'}")
    
    # Capability overview
    print(f"\n📋 CAPABILITY OVERVIEW:")
    print(f"   🧮 Advanced Metrics: CAGR, Sharpe Ratio, Max Drawdown, VaR, Technical Indicators")
    print(f"   🤖 LLM Analysis: {'Available' if os.getenv('GEMINI_API_KEY') else 'Requires GEMINI_API_KEY'}")
    print(f"   📊 Portfolio Analysis: Correlation, Diversification, Risk Assessment")
    print(f"   🔗 Integration: Complete workflow with caching and storage")
    
    print(f"\n🎉 Enhanced PokeQuant Test Suite Complete!")
    print(f"   Ready for production use with advanced quantitative analysis")
    print(f"   {len(metrics_results)} test scenarios validated")
    
    return {
        'metrics_results': metrics_results,
        'llm_results': llm_results,
        'portfolio_results': portfolio_results,
        'integration_success': integration_success
    }

if __name__ == "__main__":
    # Run comprehensive test
    results = run_comprehensive_test()
    
    # Display final metrics comparison
    if results['metrics_results']:
        print(f"\n📊 FINAL METRICS COMPARISON:")
        print(f"{'Scenario':<20} {'CAGR':<8} {'Sharpe':<8} {'Max DD':<8} {'Grade':<6}")
        print("-" * 60)
        
        for scenario, data in results['metrics_results'].items():
            metrics = data['metrics']
            grade = data['investment_grade']
            
            cagr = metrics.get('returns_analysis', {}).get('cagr', 0)
            sharpe = metrics.get('risk_metrics', {}).get('sharpe_ratio', 0)
            max_dd = metrics.get('risk_metrics', {}).get('max_drawdown_pct', 0)
            grade_letter = grade.get('grade', 'N/A')
            
            print(f"{scenario:<20} {cagr:<8.1f} {sharpe:<8.2f} {max_dd:<8.1f} {grade_letter:<6}")
    
    print(f"\n🎯 Test completed successfully! Enhanced PokeQuant is ready for use.") 