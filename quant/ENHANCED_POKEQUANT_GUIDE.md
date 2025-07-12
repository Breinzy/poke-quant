# Enhanced PokeQuant Analysis Guide

## 🎯 **Overview**

Enhanced PokeQuant elevates your Pokemon card and sealed product investment analysis to institutional-grade quantitative analysis. This upgrade introduces sophisticated financial metrics, LLM-powered insights, and portfolio-level analysis capabilities.

## 🚀 **New Capabilities**

### **Advanced Quantitative Metrics**
- **CAGR (Compound Annual Growth Rate)**: Annualized return calculation
- **Sharpe Ratio**: Risk-adjusted return measurement
- **Sortino Ratio**: Downside risk-adjusted returns
- **Maximum Drawdown**: Peak-to-trough loss analysis
- **Value at Risk (VaR)**: 95% and 99% confidence intervals
- **Technical Indicators**: RSI, Bollinger Bands, Moving Averages
- **Performance Metrics**: Win rate, profit factor, consistency scores

### **LLM-Enhanced Analysis**
- **Natural Language Insights**: Professional investment analysis
- **Market Commentary**: Contextual market interpretation
- **Risk Assessment**: Detailed risk factor analysis
- **Investment Recommendations**: STRONG_BUY to STRONG_SELL ratings
- **Portfolio Guidance**: Position sizing and diversification advice

### **Portfolio Analysis**
- **Correlation Analysis**: Cross-product correlation matrices
- **Diversification Metrics**: Risk concentration assessment
- **Portfolio Optimization**: Optimal allocation recommendations

## 📊 **Quick Start**

### **1. Install Dependencies**
```bash
pip install -r quant/requirements.txt
```

### **2. Set Environment Variables**
```bash
# Required for LLM analysis
export GEMINI_API_KEY="your-gemini-api-key"

# Optional: Enable LLM by default
export POKEQUANT_USE_LLM="true"
```

### **3. Run Enhanced Analysis**
```bash
# Basic enhanced analysis
python -m quant.enhanced_pokequant_main "Brilliant Stars Booster Box"

# With LLM insights
python -m quant.enhanced_pokequant_main "Brilliant Stars Booster Box" --use-llm

# Force fresh analysis
python -m quant.enhanced_pokequant_main "Brilliant Stars Booster Box" --use-llm --force-analysis
```

### **4. Run Comprehensive Tests**
```bash
# Test all capabilities
python -m quant.test_enhanced_analysis
```

## 🧮 **Advanced Metrics Explained**

### **Returns Analysis**
- **CAGR**: Compound Annual Growth Rate - annualized return
- **Total Return**: Absolute return over holding period
- **Volatility**: Annualized price volatility (standard deviation)
- **Best/Worst Day**: Extreme single-day performance

### **Risk Metrics**
- **Sharpe Ratio**: (Return - Risk-free rate) / Volatility
  - `> 1.0` = Excellent risk-adjusted returns
  - `0.5 - 1.0` = Good risk-adjusted returns
  - `< 0.5` = Poor risk-adjusted returns

- **Sortino Ratio**: Like Sharpe but only considers downside volatility
- **Calmar Ratio**: CAGR / Maximum Drawdown
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Recovery Time**: Days to recover from maximum drawdown

### **Technical Indicators**
- **RSI (Relative Strength Index)**: Momentum oscillator (0-100)
  - `> 70` = Overbought
  - `< 30` = Oversold
  - `30-70` = Neutral

- **Bollinger Bands**: Price channels based on volatility
- **Moving Averages**: Trend identification (SMA, EMA)
- **Momentum**: Short-term price momentum

### **Value at Risk (VaR)**
- **VaR 95%**: Maximum expected loss in 95% of scenarios
- **VaR 99%**: Maximum expected loss in 99% of scenarios
- **Expected Shortfall**: Average loss when VaR is exceeded

## 🤖 **LLM Analysis Features**

### **Executive Summary**
- Overall investment assessment
- Key highlights and insights
- Investment thesis

### **Risk Assessment**
- Risk level classification (LOW/MEDIUM/HIGH)
- Specific risk factors
- Risk mitigation strategies

### **Investment Recommendation**
- **STRONG_BUY**: High conviction, excellent metrics
- **BUY**: Positive outlook, good metrics
- **HOLD**: Neutral position, mixed signals
- **SELL**: Negative outlook, poor metrics
- **STRONG_SELL**: High conviction sell, dangerous metrics

### **Market Timing**
- Entry/exit timing guidance
- Support and resistance levels
- Stop-loss recommendations

## 📊 **Investment Grading System**

### **Grade Components (100 points total)**
- **Returns (25 points)**: Based on CAGR performance
- **Risk (25 points)**: Based on Sharpe ratio
- **Performance (25 points)**: Based on win rate
- **Technical (25 points)**: Based on technical indicators

### **Grade Scale**
- **A+ (85-100)**: Exceptional investment
- **A (80-84)**: Excellent investment
- **A- (75-79)**: Very good investment
- **B+ (70-74)**: Good investment
- **B (65-69)**: Above average
- **B- (60-64)**: Average investment
- **C (50-59)**: Below average
- **D (35-49)**: Poor investment
- **F (0-34)**: Avoid

## 🔧 **Usage Examples**

### **Basic Analysis**
```python
from quant.enhanced_pokequant_main import EnhancedPokeQuantOrchestrator

# Initialize
orchestrator = EnhancedPokeQuantOrchestrator(use_llm=True)

# Analyze product
result = orchestrator.analyze_product_enhanced("Evolving Skies Booster Box")

if result['success']:
    analysis = result['final_analysis']
    
    # Access advanced metrics
    returns = analysis['advanced_metrics']['returns_analysis']
    print(f"CAGR: {returns['cagr']}%")
    print(f"Sharpe Ratio: {analysis['advanced_metrics']['risk_metrics']['sharpe_ratio']}")
    
    # Access LLM insights
    if 'llm_insights' in analysis:
        llm = analysis['llm_insights']
        print(f"Assessment: {llm['executive_summary']['overall_assessment']}")
```

### **Portfolio Analysis**
```python
from quant.advanced_metrics import calculate_portfolio_metrics

# Portfolio data
portfolio = [
    {'name': 'Charizard V', 'price_data': charizard_prices},
    {'name': 'Pikachu VMAX', 'price_data': pikachu_prices},
    {'name': 'Rayquaza VMAX', 'price_data': rayquaza_prices}
]

# Calculate portfolio metrics
portfolio_metrics = calculate_portfolio_metrics(portfolio)

# Access results
print(f"Average Correlation: {portfolio_metrics['portfolio_metrics']['avg_correlation']}")
print(f"Diversification Ratio: {portfolio_metrics['portfolio_metrics']['diversification_ratio']}")
```

### **Custom Risk Analysis**
```python
from quant.advanced_metrics import AdvancedMetricsCalculator

calculator = AdvancedMetricsCalculator(risk_free_rate=0.045)
metrics = calculator.calculate_comprehensive_metrics(price_data)

# Access specific risk metrics
var_95 = metrics['value_at_risk']['var_95_pct']
max_drawdown = metrics['risk_metrics']['max_drawdown_pct']
sharpe_ratio = metrics['risk_metrics']['sharpe_ratio']

print(f"95% VaR: {var_95}%")
print(f"Maximum Drawdown: {max_drawdown}%")
print(f"Sharpe Ratio: {sharpe_ratio}")
```

## 🎛️ **Configuration Options**

### **Environment Variables**
```bash
# LLM Configuration
GEMINI_API_KEY="your-api-key"              # Required for LLM analysis
POKEQUANT_USE_LLM="true"                   # Enable LLM by default

# Analysis Parameters
POKEQUANT_RISK_FREE_RATE="0.045"          # Risk-free rate (default: 4.5%)
POKEQUANT_MAX_AGE_DAYS="7"                # Data freshness threshold
POKEQUANT_CACHE_HOURS="24"                # Analysis cache duration
```

### **CLI Options**
```bash
# Enhanced analysis options
--use-llm                 # Enable LLM analysis
--disable-advanced        # Disable advanced metrics
--force-analysis          # Force fresh analysis
--force-refresh           # Force data refresh
--verbose                 # Detailed output
```

## 📈 **Performance Interpretation**

### **Excellent Performance Indicators**
- **CAGR > 15%**: Strong growth
- **Sharpe Ratio > 1.5**: Excellent risk-adjusted returns
- **Max Drawdown < 15%**: Low downside risk
- **Win Rate > 70%**: Consistent performance
- **Investment Grade A or A+**: Top-tier investment

### **Warning Signs**
- **CAGR < 0%**: Declining asset
- **Sharpe Ratio < 0.5**: Poor risk-adjusted returns
- **Max Drawdown > 30%**: High downside risk
- **Win Rate < 50%**: Inconsistent performance
- **Investment Grade D or F**: Avoid

## 🔍 **Comparison with Basic Analysis**

| Feature | Basic PokeQuant | Enhanced PokeQuant |
|---------|-----------------|-------------------|
| **Metrics** | Price stats, volatility, trend | CAGR, Sharpe, VaR, Technical indicators |
| **Risk Analysis** | Simple volatility | Max drawdown, Sortino ratio, VaR |
| **Recommendations** | BUY/HOLD/SELL | STRONG_BUY to STRONG_SELL with confidence |
| **Insights** | Basic statistics | LLM-generated professional analysis |
| **Portfolio** | Single product | Multi-product correlation analysis |
| **Grading** | None | Investment grade (A+ to F) |

## 🎯 **Use Cases**

### **Individual Investors**
- **Product Evaluation**: Comprehensive analysis before purchase
- **Portfolio Review**: Assess current holdings
- **Risk Management**: Understand downside scenarios
- **Market Timing**: Optimal entry/exit points

### **Professional Traders**
- **Due Diligence**: Institutional-grade analysis
- **Risk Assessment**: Quantitative risk metrics
- **Portfolio Optimization**: Correlation-based allocation
- **Performance Reporting**: Professional-grade metrics

### **Investment Groups**
- **Diversification Analysis**: Portfolio risk concentration
- **Comparative Analysis**: Rank investment opportunities
- **Risk Budgeting**: Allocate risk across products
- **Performance Attribution**: Understand return sources

## 🛠️ **Technical Architecture**

### **Core Components**
- **AdvancedMetricsCalculator**: Sophisticated financial metrics
- **LLMAnalysisGenerator**: Natural language insights
- **EnhancedPokeQuantOrchestrator**: Integration layer
- **Portfolio Analysis**: Multi-product analysis

### **Data Flow**
1. **Data Collection**: eBay + PriceCharting scraping
2. **Data Quality**: Enhanced filtering with LLM validation
3. **Storage**: Clean data in `pokequant_price_series`
4. **Analysis**: Advanced metrics calculation
5. **Insights**: LLM-generated analysis
6. **Caching**: Results stored in `pokequant_analyses`

## 🔒 **Security & Privacy**

### **API Key Management**
- Store `GEMINI_API_KEY` securely
- Use environment variables, not hardcoded keys
- Rotate keys regularly

### **Data Protection**
- All analysis data stored in your Supabase instance
- No data sent to external services except LLM APIs
- LLM requests contain only aggregated metrics, not raw data

## 📚 **Additional Resources**

### **Documentation**
- [Original PokeQuant Roadmap](roadmap/quant.md)
- [LLM Enhanced Filtering Guide](../LLM_ENHANCED_FILTERING_GUIDE.md)
- [Database Schema](database_schema_pokequant.sql)

### **Testing**
- Run `python -m quant.test_enhanced_analysis` for comprehensive testing
- Test data includes 4 different investment scenarios
- Validates all advanced metrics and LLM integration

### **Support**
- Review test output for capability validation
- Check environment variable configuration
- Verify API key permissions for LLM access

## 🎉 **Conclusion**

Enhanced PokeQuant transforms your Pokemon card investment analysis from basic statistics to institutional-grade quantitative analysis. With sophisticated financial metrics, LLM-powered insights, and portfolio-level analysis, you now have the tools to make data-driven investment decisions with confidence.

**Key Benefits:**
- **Professional-grade analysis** with 20+ advanced metrics
- **Natural language insights** from state-of-the-art LLM
- **Portfolio optimization** with correlation analysis
- **Risk management** with VaR and drawdown analysis
- **Investment grading** system for easy comparison

Ready to elevate your Pokemon card investments? Start with the enhanced analysis today! 