#!/usr/bin/env python3
"""
LLM-Powered Analysis Generator for PokeQuant
Generates natural language investment insights based on quantitative metrics
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai

class LLMAnalysisGenerator:
    """LLM-powered generator for investment analysis and insights"""
    
    def __init__(self, gemini_api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the LLM analysis generator
        
        Args:
            gemini_api_key: Gemini API key (if None, uses GEMINI_API_KEY env var)
            model_name: Gemini model to use
        """
        api_key = gemini_api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
    def generate_comprehensive_analysis(self, product_info: Dict[str, Any], 
                                      quantitative_metrics: Dict[str, Any],
                                      market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate comprehensive investment analysis with natural language insights
        
        Args:
            product_info: Product information (name, type, set, etc.)
            quantitative_metrics: Advanced metrics from AdvancedMetricsCalculator
            market_data: Additional market context data
            
        Returns:
            Dict containing analysis insights, recommendations, and explanations
        """
        
        # Build comprehensive prompt
        prompt = self._build_analysis_prompt(product_info, quantitative_metrics, market_data)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Moderate creativity for analysis
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text)
            
            # Add metadata
            result['analysis_metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'model_used': 'gemini-2.0-flash-exp',
                'analysis_type': 'comprehensive_quantitative'
            }
            
            return result
            
        except Exception as e:
            return {
                'error': f"LLM analysis generation failed: {str(e)}",
                'fallback_analysis': self._generate_fallback_analysis(quantitative_metrics)
            }
    
    def _build_analysis_prompt(self, product_info: Dict[str, Any], 
                             quantitative_metrics: Dict[str, Any], 
                             market_data: Dict[str, Any] = None) -> str:
        """Build the comprehensive analysis prompt"""
        
        system_prompt = """You are a sophisticated quantitative analyst specializing in Pokemon card and sealed product investments. You have access to advanced financial metrics and need to provide professional investment analysis.

Your task is to analyze the provided quantitative metrics and generate a comprehensive investment report with:
1. Executive Summary
2. Risk Assessment
3. Performance Analysis
4. Technical Analysis
5. Investment Recommendation
6. Market Timing Insights
7. Risk Management Suggestions

Focus on actionable insights and professional-grade analysis. Be specific about numbers and metrics. Provide clear reasoning for your recommendations.

Response format should be JSON with the following structure:
{
  "executive_summary": {
    "overall_assessment": "string",
    "key_highlights": ["string"],
    "investment_thesis": "string"
  },
  "risk_assessment": {
    "risk_level": "LOW|MEDIUM|HIGH",
    "key_risks": ["string"],
    "risk_factors": {
      "volatility_risk": "string",
      "liquidity_risk": "string",
      "market_risk": "string"
    }
  },
  "performance_analysis": {
    "returns_summary": "string",
    "comparison_to_benchmarks": "string",
    "performance_consistency": "string"
  },
  "technical_analysis": {
    "trend_analysis": "string",
    "momentum_indicators": "string",
    "support_resistance": "string"
  },
  "investment_recommendation": {
    "recommendation": "STRONG_BUY|BUY|HOLD|SELL|STRONG_SELL",
    "confidence_level": "HIGH|MEDIUM|LOW",
    "target_allocation": "string",
    "holding_period": "string"
  },
  "market_timing": {
    "entry_timing": "string",
    "exit_strategy": "string",
    "key_levels": {
      "buy_below": "number",
      "sell_above": "number",
      "stop_loss": "number"
    }
  },
  "risk_management": {
    "position_sizing": "string",
    "diversification": "string",
    "monitoring_metrics": ["string"]
  },
  "outlook": {
    "short_term": "string",
    "medium_term": "string",
    "long_term": "string"
  }
}"""
        
        # Format metrics for the prompt
        metrics_summary = self._format_metrics_for_prompt(quantitative_metrics)
        
        user_prompt = f"""
PRODUCT INFORMATION:
{json.dumps(product_info, indent=2)}

QUANTITATIVE METRICS:
{metrics_summary}

MARKET DATA:
{json.dumps(market_data, indent=2) if market_data else "No additional market data provided"}

Please provide a comprehensive investment analysis based on these metrics. Focus on:
- Professional interpretation of the quantitative metrics
- Clear investment recommendation with reasoning
- Specific risk factors and mitigation strategies
- Actionable insights for portfolio management
- Market timing considerations based on technical indicators

Remember: This is for a sophisticated investor looking for quantitative-based investment decisions.
"""
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    def _format_metrics_for_prompt(self, metrics: Dict[str, Any]) -> str:
        """Format metrics in a readable way for the LLM"""
        
        if not metrics:
            return "No quantitative metrics available"
        
        formatted = []
        
        # Returns Analysis
        if 'returns_analysis' in metrics:
            returns = metrics['returns_analysis']
            formatted.append(f"""
RETURNS ANALYSIS:
- Total Return: {returns.get('total_return', 'N/A')}%
- CAGR: {returns.get('cagr', 'N/A')}%
- Annualized Volatility: {returns.get('annualized_volatility', 'N/A')}%
- Years Held: {returns.get('years_held', 'N/A')}
- Best Single Day: {returns.get('best_single_day', 'N/A')}%
- Worst Single Day: {returns.get('worst_single_day', 'N/A')}%
""")
        
        # Risk Metrics
        if 'risk_metrics' in metrics:
            risk = metrics['risk_metrics']
            formatted.append(f"""
RISK METRICS:
- Sharpe Ratio: {risk.get('sharpe_ratio', 'N/A')}
- Sortino Ratio: {risk.get('sortino_ratio', 'N/A')}
- Calmar Ratio: {risk.get('calmar_ratio', 'N/A')}
- Max Drawdown: {risk.get('max_drawdown_pct', 'N/A')}%
- Max Drawdown Duration: {risk.get('max_drawdown_duration_days', 'N/A')} days
- Recovery to Peak: {risk.get('recovery_to_peak_days', 'N/A')} days
- Downside Deviation: {risk.get('downside_deviation', 'N/A')}%
""")
        
        # Performance Metrics
        if 'performance_metrics' in metrics:
            performance = metrics['performance_metrics']
            formatted.append(f"""
PERFORMANCE METRICS:
- Win Rate: {performance.get('win_rate_pct', 'N/A')}%
- Average Win: {performance.get('avg_win_pct', 'N/A')}%
- Average Loss: {performance.get('avg_loss_pct', 'N/A')}%
- Profit Factor: {performance.get('profit_factor', 'N/A')}
- Return Consistency: {performance.get('return_consistency', 'N/A')}
- Price Stability: {performance.get('price_stability', 'N/A')}
""")
        
        # Technical Indicators
        if 'technical_indicators' in metrics:
            technical = metrics['technical_indicators']
            formatted.append(f"""
TECHNICAL INDICATORS:
- SMA 20 Signal: {technical.get('sma_20_signal', 'N/A')}
- EMA 20 Signal: {technical.get('ema_20_signal', 'N/A')}
- Bollinger Position: {technical.get('bollinger_position', 'N/A')}
- Bollinger Signal: {technical.get('bollinger_signal', 'N/A')}
- RSI Current: {technical.get('rsi_current', 'N/A')}
- RSI Signal: {technical.get('rsi_signal', 'N/A')}
- 10-Day Momentum: {technical.get('momentum_10d_pct', 'N/A')}%
- 20-Day Momentum: {technical.get('momentum_20d_pct', 'N/A')}%
- Trend Strength: {technical.get('trend_strength', 'N/A')}
""")
        
        # Value at Risk
        if 'value_at_risk' in metrics:
            var = metrics['value_at_risk']
            formatted.append(f"""
VALUE AT RISK:
- VaR 95%: {var.get('var_95_pct', 'N/A')}%
- VaR 99%: {var.get('var_99_pct', 'N/A')}%
- Expected Shortfall 95%: {var.get('expected_shortfall_95_pct', 'N/A')}%
- Expected Shortfall 99%: {var.get('expected_shortfall_99_pct', 'N/A')}%
- Dollar VaR 95%: ${var.get('dollar_var_95', 'N/A')}
- Dollar VaR 99%: ${var.get('dollar_var_99', 'N/A')}
""")
        
        # Market Timing
        if 'market_timing' in metrics:
            timing = metrics['market_timing']
            formatted.append(f"""
MARKET TIMING:
- Position in 30-Day Range: {timing.get('position_30d_range', 'N/A')}
- Position in 90-Day Range: {timing.get('position_90d_range', 'N/A')}
- Support Level: ${timing.get('support_level', 'N/A')}
- Resistance Level: ${timing.get('resistance_level', 'N/A')}
- Entry Signal: {timing.get('entry_signal', 'N/A')}
- Market Timing Score: {timing.get('market_timing_score', 'N/A')}
""")
        
        # Investment Grade
        if 'investment_grade' in metrics:
            grade = metrics['investment_grade']
            formatted.append(f"""
INVESTMENT GRADE:
- Grade: {grade.get('grade', 'N/A')}
- Score: {grade.get('score', 'N/A')}/100
- Recommendation: {grade.get('investment_recommendation', 'N/A')}
""")
        
        return "\n".join(formatted)
    
    def _generate_fallback_analysis(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback analysis when LLM fails"""
        
        if not metrics:
            return {
                'executive_summary': {
                    'overall_assessment': 'Insufficient data for comprehensive analysis',
                    'key_highlights': ['No quantitative metrics available'],
                    'investment_thesis': 'Cannot provide investment recommendation without data'
                },
                'investment_recommendation': {
                    'recommendation': 'HOLD',
                    'confidence_level': 'LOW',
                    'target_allocation': 'Avoid until more data is available'
                }
            }
        
        # Simple rule-based fallback
        returns = metrics.get('returns_analysis', {})
        risk = metrics.get('risk_metrics', {})
        
        cagr = returns.get('cagr', 0)
        sharpe = risk.get('sharpe_ratio', 0)
        max_dd = risk.get('max_drawdown_pct', 0)
        
        if cagr > 15 and sharpe > 1.0 and max_dd > -20:
            recommendation = 'BUY'
            assessment = 'Strong performance with acceptable risk'
        elif cagr > 8 and sharpe > 0.5:
            recommendation = 'HOLD'
            assessment = 'Moderate performance with balanced risk'
        else:
            recommendation = 'SELL'
            assessment = 'Poor risk-adjusted returns'
        
        return {
            'executive_summary': {
                'overall_assessment': assessment,
                'key_highlights': [
                    f'CAGR: {cagr:.1f}%',
                    f'Sharpe Ratio: {sharpe:.2f}',
                    f'Max Drawdown: {max_dd:.1f}%'
                ],
                'investment_thesis': f'Based on quantitative metrics, this investment shows {assessment.lower()}'
            },
            'investment_recommendation': {
                'recommendation': recommendation,
                'confidence_level': 'MEDIUM',
                'target_allocation': 'Based on quantitative analysis only'
            },
            'risk_assessment': {
                'risk_level': 'HIGH' if max_dd < -25 else 'MEDIUM' if max_dd < -15 else 'LOW',
                'key_risks': ['Quantitative analysis only', 'Limited market context']
            }
        }
    
    def generate_market_commentary(self, portfolio_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market commentary for portfolio-level analysis"""
        
        if not portfolio_metrics:
            return {'error': 'No portfolio metrics provided'}
        
        commentary_prompt = f"""
You are a Pokemon card market analyst providing portfolio-level commentary. Based on the following portfolio metrics, provide market insights:

PORTFOLIO METRICS:
{json.dumps(portfolio_metrics, indent=2)}

Provide commentary on:
1. Portfolio diversification
2. Market correlations
3. Risk concentration
4. Optimal portfolio adjustments

Response format:
{{
  "market_commentary": {{
    "diversification_analysis": "string",
    "correlation_insights": "string",
    "risk_concentration": "string",
    "portfolio_optimization": "string"
  }},
  "recommendations": ["string"],
  "risk_warnings": ["string"]
}}
"""
        
        try:
            response = self.model.generate_content(
                commentary_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            return {
                'error': f"Market commentary generation failed: {str(e)}",
                'fallback_commentary': {
                    'diversification_analysis': 'Portfolio analysis requires LLM processing',
                    'correlation_insights': 'Correlation analysis not available',
                    'risk_concentration': 'Risk assessment requires manual review'
                }
            }
    
    def generate_alert_analysis(self, product_info: Dict[str, Any], 
                              trigger_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis for price alerts and significant changes"""
        
        alert_prompt = f"""
You are a Pokemon card investment alert system. A significant price or metric change has been detected for:

PRODUCT: {product_info.get('name', 'Unknown Product')}
TRIGGER METRICS: {json.dumps(trigger_metrics, indent=2)}

Provide immediate analysis:
1. What triggered this alert?
2. Is this a buying opportunity or warning signal?
3. What should an investor do?

Response format:
{{
  "alert_analysis": {{
    "trigger_reason": "string",
    "severity": "LOW|MEDIUM|HIGH|CRITICAL",
    "action_required": "string",
    "time_sensitivity": "IMMEDIATE|HOURS|DAYS|WEEKS"
  }},
  "recommendations": {{
    "immediate_action": "string",
    "monitoring_required": "string",
    "follow_up_timeline": "string"
  }}
}}
"""
        
        try:
            response = self.model.generate_content(
                alert_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Lower temperature for alerts
                    response_mime_type="application/json"
                )
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            return {
                'error': f"Alert analysis generation failed: {str(e)}",
                'fallback_alert': {
                    'alert_analysis': {
                        'trigger_reason': 'Significant metric change detected',
                        'severity': 'MEDIUM',
                        'action_required': 'Review manually'
                    }
                }
            }

# Integration function for existing PokeQuant system
def generate_llm_enhanced_analysis(quantitative_metrics: Dict[str, Any], 
                                 product_info: Dict[str, Any],
                                 market_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate LLM-enhanced analysis for integration with existing PokeQuant system
    
    Args:
        quantitative_metrics: Output from AdvancedMetricsCalculator
        product_info: Product information
        market_data: Additional market context
        
    Returns:
        Enhanced analysis with natural language insights
    """
    
    # Check if LLM is available
    if not os.getenv('GEMINI_API_KEY'):
        return {
            'llm_analysis': None,
            'error': 'GEMINI_API_KEY not available for LLM analysis'
        }
    
    try:
        generator = LLMAnalysisGenerator()
        analysis = generator.generate_comprehensive_analysis(
            product_info=product_info,
            quantitative_metrics=quantitative_metrics,
            market_data=market_data
        )
        
        return {
            'llm_analysis': analysis,
            'enhanced_insights': True
        }
        
    except Exception as e:
        return {
            'llm_analysis': None,
            'error': f'LLM analysis failed: {str(e)}'
        } 