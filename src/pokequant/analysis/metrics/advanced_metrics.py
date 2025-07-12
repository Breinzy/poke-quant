#!/usr/bin/env python3
"""
Advanced Quantitative Metrics for PokeQuant
Sophisticated financial analysis including CAGR, Sharpe ratio, max drawdown, VaR, and technical indicators
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

class AdvancedMetricsCalculator:
    """Advanced quantitative metrics calculator for Pokemon card/sealed product investments"""
    
    def __init__(self, risk_free_rate: float = 0.045):
        """
        Initialize calculator
        
        Args:
            risk_free_rate: Annual risk-free rate (default 4.5% - current 10-year Treasury)
        """
        self.risk_free_rate = risk_free_rate
        
    def calculate_comprehensive_metrics(self, price_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate comprehensive financial metrics for investment analysis
        
        Args:
            price_data: List of price points with 'price' and 'price_date' keys
        
        Returns:
            Dict containing all calculated metrics
        """
        
        if not price_data or len(price_data) < 2:
            return self._empty_metrics()
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(price_data)
        df['price_date'] = pd.to_datetime(df['price_date'])
        df = df.sort_values('price_date').reset_index(drop=True)
        
        # Calculate returns
        df['returns'] = df['price'].pct_change().fillna(0)
        df['log_returns'] = np.log(df['price'] / df['price'].shift(1)).fillna(0)
        
        # Remove infinite values and outliers
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(df) < 2:
            return self._empty_metrics()
        
        # Calculate all metrics
        metrics = {
            'returns_analysis': self._calculate_returns_metrics(df),
            'risk_metrics': self._calculate_risk_metrics(df),
            'performance_metrics': self._calculate_performance_metrics(df),
            'technical_indicators': self._calculate_technical_indicators(df),
            'value_at_risk': self._calculate_var_metrics(df),
            'statistical_properties': self._calculate_statistical_properties(df),
            'time_series_analysis': self._calculate_time_series_metrics(df),
            'market_timing': self._calculate_market_timing_metrics(df)
        }
        
        return metrics
    
    def _calculate_returns_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive returns-based metrics"""
        
        if len(df) < 2:
            return {}
        
        # Basic return calculations
        total_return = (df['price'].iloc[-1] / df['price'].iloc[0]) - 1
        
        # Time period calculations
        start_date = df['price_date'].iloc[0]
        end_date = df['price_date'].iloc[-1]
        days_held = (end_date - start_date).days
        years_held = max(days_held / 365.25, 1/365.25)  # Minimum 1 day
        
        # Annualized metrics
        cagr = (df['price'].iloc[-1] / df['price'].iloc[0]) ** (1/years_held) - 1
        
        # Periodic returns
        daily_returns = df['returns'].mean()
        daily_volatility = df['returns'].std()
        
        # Annualized volatility
        annualized_volatility = daily_volatility * np.sqrt(365.25)
        
        return {
            'total_return': round(total_return * 100, 2),
            'cagr': round(cagr * 100, 2),
            'annualized_volatility': round(annualized_volatility * 100, 2),
            'daily_return_avg': round(daily_returns * 100, 4),
            'daily_volatility': round(daily_volatility * 100, 2),
            'years_held': round(years_held, 2),
            'days_held': days_held,
            'best_single_day': round(df['returns'].max() * 100, 2),
            'worst_single_day': round(df['returns'].min() * 100, 2)
        }
    
    def _calculate_risk_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics"""
        
        if len(df) < 2:
            return {}
        
        # Sharpe Ratio
        excess_returns = df['returns'].mean() - (self.risk_free_rate / 365.25)
        sharpe_ratio = excess_returns / df['returns'].std() * np.sqrt(365.25) if df['returns'].std() > 0 else 0
        
        # Maximum Drawdown
        running_max = df['price'].expanding().max()
        drawdown = (df['price'] - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Find max drawdown period
        max_dd_end = drawdown.idxmin()
        max_dd_start = df.loc[:max_dd_end, 'price'].idxmax()
        max_dd_duration = (df.loc[max_dd_end, 'price_date'] - df.loc[max_dd_start, 'price_date']).days
        
        # Recovery analysis
        recovery_to_peak = None
        if max_dd_end < len(df) - 1:
            peak_price = df.loc[max_dd_start, 'price']
            recovery_data = df.loc[max_dd_end:, 'price'] >= peak_price
            if recovery_data.any():
                recovery_idx = recovery_data.idxmax()
                recovery_to_peak = (df.loc[recovery_idx, 'price_date'] - df.loc[max_dd_end, 'price_date']).days
        
        # Downside Deviation (Sortino Ratio input)
        negative_returns = df['returns'][df['returns'] < 0]
        downside_deviation = negative_returns.std() * np.sqrt(365.25) if len(negative_returns) > 0 else 0
        
        # Sortino Ratio
        sortino_ratio = (df['returns'].mean() * 365.25 - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        
        # Calmar Ratio
        cagr = (df['price'].iloc[-1] / df['price'].iloc[0]) ** (365.25 / (df['price_date'].iloc[-1] - df['price_date'].iloc[0]).days) - 1
        calmar_ratio = cagr / abs(max_drawdown) if max_drawdown < 0 else 0
        
        return {
            'sharpe_ratio': round(sharpe_ratio, 3),
            'sortino_ratio': round(sortino_ratio, 3),
            'calmar_ratio': round(calmar_ratio, 3),
            'max_drawdown_pct': round(max_drawdown * 100, 2),
            'max_drawdown_duration_days': max_dd_duration,
            'recovery_to_peak_days': recovery_to_peak,
            'downside_deviation': round(downside_deviation * 100, 2),
            'upside_capture': round(df['returns'][df['returns'] > 0].mean() * 100, 2) if len(df['returns'][df['returns'] > 0]) > 0 else 0,
            'downside_capture': round(df['returns'][df['returns'] < 0].mean() * 100, 2) if len(df['returns'][df['returns'] < 0]) > 0 else 0
        }
    
    def _calculate_performance_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance and efficiency metrics"""
        
        if len(df) < 2:
            return {}
        
        # Win rate
        winning_periods = (df['returns'] > 0).sum()
        total_periods = len(df['returns'])
        win_rate = winning_periods / total_periods * 100
        
        # Average win vs average loss
        wins = df['returns'][df['returns'] > 0]
        losses = df['returns'][df['returns'] < 0]
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        
        # Profit factor
        profit_factor = abs(avg_win * len(wins) / (avg_loss * len(losses))) if len(losses) > 0 and avg_loss < 0 else float('inf')
        
        # Consistency metrics
        return_consistency = 1 - (df['returns'].std() / abs(df['returns'].mean())) if df['returns'].mean() != 0 else 0
        
        # Stability metrics
        price_stability = 1 - (df['price'].std() / df['price'].mean())
        
        return {
            'win_rate_pct': round(win_rate, 2),
            'avg_win_pct': round(avg_win * 100, 2),
            'avg_loss_pct': round(avg_loss * 100, 2),
            'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 999,
            'return_consistency': round(return_consistency, 3),
            'price_stability': round(price_stability, 3),
            'winning_periods': int(winning_periods),
            'losing_periods': int(total_periods - winning_periods),
            'total_periods': int(total_periods)
        }
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical analysis indicators"""
        
        if len(df) < 20:
            return {}
        
        # Moving averages
        df['sma_10'] = df['price'].rolling(window=10).mean()
        df['sma_20'] = df['price'].rolling(window=20).mean()
        df['ema_10'] = df['price'].ewm(span=10).mean()
        df['ema_20'] = df['price'].ewm(span=20).mean()
        
        # Current price position relative to moving averages
        current_price = df['price'].iloc[-1]
        sma_10_current = df['sma_10'].iloc[-1]
        sma_20_current = df['sma_20'].iloc[-1]
        ema_10_current = df['ema_10'].iloc[-1]
        ema_20_current = df['ema_20'].iloc[-1]
        
        # Bollinger Bands
        sma_20 = df['price'].rolling(window=20).mean()
        std_20 = df['price'].rolling(window=20).std()
        upper_band = sma_20 + (std_20 * 2)
        lower_band = sma_20 - (std_20 * 2)
        
        # Bollinger Band position
        bb_position = (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
        
        # RSI (Relative Strength Index)
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Momentum
        momentum_10 = (current_price / df['price'].iloc[-10] - 1) * 100 if len(df) >= 10 else 0
        momentum_20 = (current_price / df['price'].iloc[-20] - 1) * 100 if len(df) >= 20 else 0
        
        return {
            'sma_10_signal': 'bullish' if current_price > sma_10_current else 'bearish',
            'sma_20_signal': 'bullish' if current_price > sma_20_current else 'bearish',
            'ema_10_signal': 'bullish' if current_price > ema_10_current else 'bearish',
            'ema_20_signal': 'bullish' if current_price > ema_20_current else 'bearish',
            'bollinger_position': round(bb_position, 3),
            'bollinger_signal': 'overbought' if bb_position > 0.8 else 'oversold' if bb_position < 0.2 else 'neutral',
            'rsi_current': round(rsi.iloc[-1], 2) if not pd.isna(rsi.iloc[-1]) else 50,
            'rsi_signal': 'overbought' if rsi.iloc[-1] > 70 else 'oversold' if rsi.iloc[-1] < 30 else 'neutral',
            'momentum_10d_pct': round(momentum_10, 2),
            'momentum_20d_pct': round(momentum_20, 2),
            'trend_strength': 'strong' if abs(momentum_20) > 10 else 'moderate' if abs(momentum_20) > 5 else 'weak'
        }
    
    def _calculate_var_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate Value at Risk and related metrics"""
        
        if len(df) < 10:
            return {}
        
        # Calculate VaR at different confidence levels
        returns = df['returns'].dropna()
        
        if len(returns) < 10:
            return {}
        
        # Historical VaR (percentile method)
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Parametric VaR (assuming normal distribution)
        mean_return = returns.mean()
        std_return = returns.std()
        
        # Z-scores for confidence levels
        z_95 = stats.norm.ppf(0.05)
        z_99 = stats.norm.ppf(0.01)
        
        parametric_var_95 = mean_return + z_95 * std_return
        parametric_var_99 = mean_return + z_99 * std_return
        
        # Expected Shortfall (Conditional VaR)
        es_95 = returns[returns <= var_95].mean()
        es_99 = returns[returns <= var_99].mean()
        
        # Current price VaR (dollar terms)
        current_price = df['price'].iloc[-1]
        dollar_var_95 = current_price * var_95
        dollar_var_99 = current_price * var_99
        
        return {
            'var_95_pct': round(var_95 * 100, 2),
            'var_99_pct': round(var_99 * 100, 2),
            'parametric_var_95_pct': round(parametric_var_95 * 100, 2),
            'parametric_var_99_pct': round(parametric_var_99 * 100, 2),
            'expected_shortfall_95_pct': round(es_95 * 100, 2) if not pd.isna(es_95) else 0,
            'expected_shortfall_99_pct': round(es_99 * 100, 2) if not pd.isna(es_99) else 0,
            'dollar_var_95': round(dollar_var_95, 2),
            'dollar_var_99': round(dollar_var_99, 2)
        }
    
    def _calculate_statistical_properties(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistical properties of returns"""
        
        if len(df) < 10:
            return {}
        
        returns = df['returns'].dropna()
        
        if len(returns) < 10:
            return {}
        
        # Basic statistics
        mean_return = returns.mean()
        median_return = returns.median()
        std_return = returns.std()
        
        # Higher moments
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        # Normality test
        jarque_bera_stat, jarque_bera_p = stats.jarque_bera(returns)
        is_normal = jarque_bera_p > 0.05
        
        # Auto-correlation
        autocorr_lag1 = returns.autocorr(lag=1) if len(returns) > 1 else 0
        
        return {
            'mean_return_pct': round(mean_return * 100, 4),
            'median_return_pct': round(median_return * 100, 4),
            'std_return_pct': round(std_return * 100, 2),
            'skewness': round(skewness, 3),
            'kurtosis': round(kurtosis, 3),
            'is_normal_distribution': is_normal,
            'jarque_bera_pvalue': round(jarque_bera_p, 4),
            'autocorrelation_lag1': round(autocorr_lag1, 3),
            'distribution_type': 'normal' if is_normal else 'fat-tailed' if kurtosis > 3 else 'thin-tailed'
        }
    
    def _calculate_time_series_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate time series specific metrics"""
        
        if len(df) < 30:
            return {}
        
        # Seasonality analysis (if enough data)
        df['month'] = df['price_date'].dt.month
        df['quarter'] = df['price_date'].dt.quarter
        df['day_of_week'] = df['price_date'].dt.dayofweek
        
        # Monthly performance
        monthly_returns = df.groupby('month')['returns'].mean()
        best_month = monthly_returns.idxmax()
        worst_month = monthly_returns.idxmin()
        
        # Quarterly performance
        quarterly_returns = df.groupby('quarter')['returns'].mean()
        best_quarter = quarterly_returns.idxmax()
        worst_quarter = quarterly_returns.idxmin()
        
        # Volatility clustering (GARCH-like measure)
        volatility_clustering = returns.rolling(window=10).std().std() if len(df) >= 10 else 0
        
        return {
            'best_month': int(best_month),
            'worst_month': int(worst_month),
            'best_quarter': int(best_quarter),
            'worst_quarter': int(worst_quarter),
            'monthly_volatility': round(monthly_returns.std() * 100, 2),
            'quarterly_volatility': round(quarterly_returns.std() * 100, 2),
            'volatility_clustering': round(volatility_clustering, 4),
            'data_frequency': 'daily' if len(df) > 100 else 'weekly' if len(df) > 20 else 'monthly'
        }
    
    def _calculate_market_timing_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate market timing and entry/exit metrics"""
        
        if len(df) < 20:
            return {}
        
        # Rolling period analysis
        current_price = df['price'].iloc[-1]
        
        # Entry timing analysis
        prices_30d = df['price'].iloc[-30:] if len(df) >= 30 else df['price']
        prices_90d = df['price'].iloc[-90:] if len(df) >= 90 else df['price']
        
        # Current position relative to recent ranges
        position_30d = (current_price - prices_30d.min()) / (prices_30d.max() - prices_30d.min()) if prices_30d.max() != prices_30d.min() else 0.5
        position_90d = (current_price - prices_90d.min()) / (prices_90d.max() - prices_90d.min()) if prices_90d.max() != prices_90d.min() else 0.5
        
        # Support and resistance levels
        support_level = prices_90d.quantile(0.25)
        resistance_level = prices_90d.quantile(0.75)
        
        # Entry recommendation
        entry_signal = 'buy' if position_90d < 0.3 else 'sell' if position_90d > 0.7 else 'hold'
        
        return {
            'position_30d_range': round(position_30d, 3),
            'position_90d_range': round(position_90d, 3),
            'support_level': round(support_level, 2),
            'resistance_level': round(resistance_level, 2),
            'entry_signal': entry_signal,
            'distance_to_support_pct': round((current_price - support_level) / support_level * 100, 2),
            'distance_to_resistance_pct': round((resistance_level - current_price) / current_price * 100, 2),
            'market_timing_score': round(1 - position_90d, 2)  # Higher score = better entry timing
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure when insufficient data"""
        return {
            'returns_analysis': {},
            'risk_metrics': {},
            'performance_metrics': {},
            'technical_indicators': {},
            'value_at_risk': {},
            'statistical_properties': {},
            'time_series_analysis': {},
            'market_timing': {},
            'data_quality': 'insufficient_data'
        }
    
    def generate_investment_grade(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall investment grade based on comprehensive metrics"""
        
        if not metrics or 'returns_analysis' not in metrics:
            return {'grade': 'F', 'score': 0, 'reasoning': ['Insufficient data for analysis']}
        
        score = 0
        reasoning = []
        
        # Returns component (25 points)
        returns = metrics.get('returns_analysis', {})
        if returns.get('cagr', 0) > 15:
            score += 25
            reasoning.append(f"Excellent CAGR of {returns.get('cagr', 0):.1f}%")
        elif returns.get('cagr', 0) > 8:
            score += 20
            reasoning.append(f"Good CAGR of {returns.get('cagr', 0):.1f}%")
        elif returns.get('cagr', 0) > 0:
            score += 10
            reasoning.append(f"Positive CAGR of {returns.get('cagr', 0):.1f}%")
        else:
            reasoning.append(f"Negative CAGR of {returns.get('cagr', 0):.1f}%")
        
        # Risk component (25 points)
        risk = metrics.get('risk_metrics', {})
        if risk.get('sharpe_ratio', 0) > 1.5:
            score += 25
            reasoning.append(f"Excellent Sharpe ratio of {risk.get('sharpe_ratio', 0):.2f}")
        elif risk.get('sharpe_ratio', 0) > 1.0:
            score += 20
            reasoning.append(f"Good Sharpe ratio of {risk.get('sharpe_ratio', 0):.2f}")
        elif risk.get('sharpe_ratio', 0) > 0.5:
            score += 10
            reasoning.append(f"Moderate Sharpe ratio of {risk.get('sharpe_ratio', 0):.2f}")
        else:
            reasoning.append(f"Poor Sharpe ratio of {risk.get('sharpe_ratio', 0):.2f}")
        
        # Performance component (25 points)
        performance = metrics.get('performance_metrics', {})
        if performance.get('win_rate_pct', 0) > 70:
            score += 25
            reasoning.append(f"High win rate of {performance.get('win_rate_pct', 0):.1f}%")
        elif performance.get('win_rate_pct', 0) > 60:
            score += 20
            reasoning.append(f"Good win rate of {performance.get('win_rate_pct', 0):.1f}%")
        elif performance.get('win_rate_pct', 0) > 50:
            score += 10
            reasoning.append(f"Moderate win rate of {performance.get('win_rate_pct', 0):.1f}%")
        else:
            reasoning.append(f"Low win rate of {performance.get('win_rate_pct', 0):.1f}%")
        
        # Technical component (25 points)
        technical = metrics.get('technical_indicators', {})
        market_timing = metrics.get('market_timing', {})
        
        bullish_signals = sum([
            technical.get('sma_20_signal') == 'bullish',
            technical.get('ema_20_signal') == 'bullish',
            technical.get('rsi_signal') != 'overbought',
            market_timing.get('entry_signal') == 'buy'
        ])
        
        if bullish_signals >= 3:
            score += 25
            reasoning.append("Strong technical indicators")
        elif bullish_signals >= 2:
            score += 15
            reasoning.append("Mixed technical indicators")
        elif bullish_signals >= 1:
            score += 5
            reasoning.append("Weak technical indicators")
        else:
            reasoning.append("Bearish technical indicators")
        
        # Grade assignment
        if score >= 85:
            grade = 'A+'
        elif score >= 80:
            grade = 'A'
        elif score >= 75:
            grade = 'A-'
        elif score >= 70:
            grade = 'B+'
        elif score >= 65:
            grade = 'B'
        elif score >= 60:
            grade = 'B-'
        elif score >= 55:
            grade = 'C+'
        elif score >= 50:
            grade = 'C'
        elif score >= 45:
            grade = 'C-'
        elif score >= 40:
            grade = 'D+'
        elif score >= 35:
            grade = 'D'
        elif score >= 30:
            grade = 'D-'
        else:
            grade = 'F'
        
        return {
            'grade': grade,
            'score': score,
            'reasoning': reasoning,
            'investment_recommendation': 'BUY' if score >= 70 else 'HOLD' if score >= 50 else 'AVOID'
        }

def calculate_portfolio_metrics(products_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate portfolio-level metrics across multiple products"""
    
    if not products_data:
        return {}
    
    # Extract returns for correlation analysis
    all_returns = []
    product_names = []
    
    for product in products_data:
        if 'price_data' in product and len(product['price_data']) > 1:
            df = pd.DataFrame(product['price_data'])
            df['price_date'] = pd.to_datetime(df['price_date'])
            df = df.sort_values('price_date')
            df['returns'] = df['price'].pct_change().fillna(0)
            
            all_returns.append(df['returns'].values)
            product_names.append(product.get('name', 'Unknown'))
    
    if len(all_returns) < 2:
        return {'error': 'Need at least 2 products for portfolio analysis'}
    
    # Align returns to same length (minimum common length)
    min_length = min(len(returns) for returns in all_returns)
    aligned_returns = np.array([returns[-min_length:] for returns in all_returns])
    
    # Calculate correlation matrix
    correlation_matrix = np.corrcoef(aligned_returns)
    
    # Portfolio diversification metrics
    avg_correlation = np.mean(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)])
    max_correlation = np.max(correlation_matrix[np.triu_indices_from(correlation_matrix, k=1)])
    
    # Equal-weighted portfolio returns
    portfolio_returns = np.mean(aligned_returns, axis=0)
    portfolio_volatility = np.std(portfolio_returns) * np.sqrt(365.25)
    
    return {
        'portfolio_metrics': {
            'avg_correlation': round(avg_correlation, 3),
            'max_correlation': round(max_correlation, 3),
            'portfolio_volatility': round(portfolio_volatility * 100, 2),
            'diversification_ratio': round(1 - avg_correlation, 3),
            'products_count': len(products_data)
        },
        'correlation_matrix': correlation_matrix.tolist(),
        'product_names': product_names
    } 