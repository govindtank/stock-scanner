"""
Risk Management Module for Stock Scanner
Implements professional risk controls:
- Stop-Loss Calculators (ATR-based, Volatility-adjusted, Fixed %)
- Take-Profit Targets (Trailing stops, Risk/reward ratios)
- Position Sizing (Kelly Criterion, Volatility targeting)
- Portfolio Value-at-Risk (VaR) calculations
- Drawdown tracking and monitoring
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum


class StopLossType(Enum):
    """Types of stop-loss strategies."""
    FIXED_PCT = "fixed_pct"
    ATR_BASED = "atr_based"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    CHAIN_STOP = "chain_stop"
    TREND_FOLLOWING = "trend_following"


class TakeProfitType(Enum):
    """Types of take-profit strategies."""
    FIXED_PCT = "fixed_pct"
    RISK_REWARD_RATIO = "risk_reward_ratio"
    TRAILING_STOP = "trailing_stop"
    RSI_OVERBOUGHT = "rsi_overbought"
    VOLUME_PROFILE = "volume_profile"


class PositionSizingType(Enum):
    """Types of position sizing strategies."""
    FIXED_PERCENT = "fixed_percent"
    KELY_CRITERION = "kelly_criterion"
    VOLATILITY_TARGETING = "volatility_targeting"
    RISK_PARITY = "risk_parity"


class RiskManager:
    """
    Professional risk management system for stock trading.
    
    Implements multiple strategies for each risk control category.
    """
    
    @staticmethod
    def calculate_stop_loss(
        entry_price: float,
        stop_type: StopLossType = StopLossType.FIXED_PCT,
        price_data: Optional[pd.Series] = None,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        volatility_threshold: float = 0.25
    ) -> float:
        """
        Calculate appropriate stop-loss level based on strategy.
        
        Args:
            entry_price: Price where position was entered
            stop_type: Type of stop-loss strategy
            price_data: OHLC data (used for volatility-based stops)
            atr_period: ATR calculation period
            atr_multiplier: Number of ATRs for stop distance
            volatility_threshold: Volatility multiplier for dynamic stops
            
        Returns:
            Stop-loss price level
        """
        if stop_type == StopLossType.FIXED_PCT:
            # Fixed percentage stop (e.g., 5% below entry)
            stop_pct = 0.05
            return entry_price * (1 - stop_pct)
            
        elif stop_type == StopLossType.ATR_BASED:
            if price_data is None or len(price_data) < atr_period + 1:
                # Fallback to fixed percentage
                return entry_price * 0.95
            else:
                from technical_indicators import TechnicalIndicators
                atr = TechnicalIndicators.atr(
                    pd.Series(price_data),
                    pd.Series(price_data),
                    pd.Series(price_data).shift(1).ffill(),
                    atr_period
                )
                atr_val = atr.iloc[-1] if len(atr) > 0 else price_data.iloc[-1] * 0.02
                
                return entry_price - (atr_val * atr_multiplier)
            
        elif stop_type == StopLossType.VOLATILITY_ADJUSTED:
            if price_data is None or len(price_data) < 30:
                return entry_price * 0.95
            else:
                # Calculate recent volatility (20-day rolling std of returns)
                returns = np.log(price_data.pct_change().fillna(0))
                vol_20d = returns.rolling(window=20).std().iloc[-1]
                vol_monthly = vol_20d * np.sqrt(21)  # Annualized to monthly
                
                # Stop based on monthly volatility (e.g., 1x monthly vol)
                stop_distance = entry_price * vol_monthly * volatility_threshold
                
                return entry_price - stop_distance
            
        elif stop_type == StopLossType.CHAIN_STOP:
            # Multiple stops tightening over time
            time_days = len(price_data) if price_data is not None else 0
            
            if time_days < 5:
                # Early in trade - wider stop
                return entry_price * 0.07  # 7% stop initially
            elif time_days < 20:
                # Medium term - moderate stop
                return entry_price * 0.05  # 5% stop
            else:
                # Late in trade - tight stop near breakeven eventually
                return entry_price * 0.04  # 4% stop
            
        elif stop_type == StopLossType.TREND_FOLLOWING:
            if price_data is None or len(price_data) < 50:
                return entry_price * 0.95
            
            from technical_indicators import TechnicalIndicators
            sma_20 = pd.Series(price_data).rolling(window=20).mean().iloc[-1]
            
            # Stop below short-term trend (SMA 20) with buffer
            stop_distance_pct = 0.03  # 3% below SMA
            return sma_20 * (1 - stop_distance_pct)
        
        else:
            raise ValueError(f"Unknown stop-loss type: {stop_type}")
    
    @staticmethod
    def calculate_take_profit(
        entry_price: float,
        tp_type: TakeProfitType = TakeProfitType.FIXED_PCT,
        position_data: Optional[Dict] = None,
        rsi_periods: Tuple[int, int] = (70, 30),
        risk_reward_ratio: float = 2.0
    ) -> float:
        """
        Calculate appropriate take-profit level based on strategy.
        
        Args:
            entry_price: Price where position was entered
            tp_type: Type of take-profit strategy
            position_data: Additional position context (stop_loss, risk_amount)
            rsi_periods: RSI periods for overbought/oversold signals
            risk_reward_ratio: Target R:R ratio (e.g., 2.0 = $2 profit per $1 risk)
            
        Returns:
            Take-profit price level (or None if trailing/target is active)
        """
        if tp_type == TakeProfitType.FIXED_PCT:
            # Fixed percentage take-profit
            tp_pct = 0.15  # 15% above entry
            return entry_price * (1 + tp_pct)
            
        elif tp_type == TakeProfitType.RISK_REWARD_RATIO:
            if position_data is None or 'stop_loss' not in position_data:
                # Fallback to fixed percentage
                return entry_price * 0.30
            
            risk_amount = abs(position_data['entry_price'] - position_data['stop_loss'])
            target_risk_reward = position_data.get('risk_reward_ratio', risk_reward_ratio)
            
            profit_target = risk_amount * target_risk_reward
            return entry_price + profit_target
        
        elif tp_type == TakeProfitType.TRAILING_STOP:
            # Return current trailing TP level (would track with price)
            if 'current_profit_pct' in position_data:
                trail_distance = 0.08  # 8% from highest price
                high_since_entry = position_data.get('highest_price', entry_price)
                return high_since_entry * (1 - trail_distance)
            
            # Initial TP based on R:R
            risk_amount = abs(position_data.get('stop_loss', entry_price) - entry_price)
            target_risk_reward = position_data.get('risk_reward_ratio', 3.0)
            profit_target = risk_amount * target_risk_reward
            return entry_price + profit_target
        
        elif tp_type == TakeProfitType.RSI_OVERBOUGHT:
            from technical_indicators import TechnicalIndicators
            
            if position_data is None or 'current_price' not in position_data:
                return None
            
            # Check RSI levels
            rsi = pd.Series(position_data.get('rsi_data', []))
            if len(rsi) > 0 and rsi.iloc[-1] < rsi_periods[1]:  # RSI below oversold threshold
                return position_data['current_price'] * (1 + risk_reward_ratio)
            
            return None
        
        elif tp_type == TakeProfitType.VOLUME_PROFILE:
            # High volume node target (simplified version)
            if position_data is None or 'volume_profile' not in position_data:
                return None
            
            high_volume_nodes = position_data['volume_profile'].get('nodes', [])
            next_node = min([n for n in high_volume_nodes if n > entry_price], default=None)
            
            if next_node is not None:
                return next_node
            
            # Fallback to R:R based target
            risk_amount = abs(position_data.get('stop_loss', entry_price) - entry_price)
            return entry_price + (risk_amount * position_data.get('risk_reward_ratio', 2.0))
        
        else:
            raise ValueError(f"Unknown take-profit type: {tp_type}")
    
    @staticmethod
    def calculate_position_size(
        account_balance: float,
        stock_price: float,
        sizing_type: PositionSizingType = PositionSizingType.FIXED_PERCENT,
        risk_per_trade_pct: float = 0.02,
        kelly_fraction: float = 0.25,  # Half-Kelly for reduced risk
        target_portfolio_volatility: float = 0.15
    ) -> float:
        """
        Calculate appropriate position size based on strategy.
        
        Args:
            account_balance: Total account balance
            stock_price: Current price of the stock
            sizing_type: Position sizing strategy
            risk_per_trade_pct: Maximum risk per trade as % of account
            kelly_fraction: Fraction of full Kelly criterion (e.g., 0.25 = quarter-Kelly)
            target_portfolio_volatility: Target annualized volatility
            
        Returns:
            Dollar amount to invest in this position
        """
        if sizing_type == PositionSizingType.FIXED_PERCENT:
            # Fixed percentage of account (e.g., $10k per position on $100k account)
            fixed_amount = account_balance * 0.10  # 10% of account
            
            # Adjust for stop distance to ensure max risk is met
            stop_distance = 0.05  # Default 5% stop
            position_value = stock_price / (1 - stop_distance)
            
            return min(fixed_amount, position_value * risk_per_trade_pct / stop_distance)
        
        elif sizing_type == PositionSizingType.KELY_CRITERION:
            # Kelly Criterion (simplified single-asset version)
            win_rate = position_data.get('win_rate', 0.45) if position_data else 0.45
            avg_wins = position_data.get('avg_win_pct', 15) if position_data else 15
            avg_losses = position_data.get('avg_loss_pct', -8) if position_data else -8
            
            win_loss_ratio = abs(avg_wins / avg_losses)
            net_pnl = (win_rate * avg_wins) + ((1 - win_rate) * avg_losses)
            
            # Full Kelly
            kelly_ratio = net_pnl / avg_losses
            
            # Apply fraction to reduce risk
            position_value = account_balance * kelly_ratio * kelly_fraction
            
            return max(0, min(position_value, account_balance * 0.10))  # Cap at 10% of account
        
        elif sizing_type == PositionSizingType.VOLATILITY_TARGETING:
            # Size position to achieve target portfolio volatility
            if position_data is None or 'stock_volatility' not in position_data:
                stock_vol = 0.30  # Default 30% annualized vol
            else:
                stock_vol = position_data['stock_volatility']
            
            correlation = position_data.get('correlation_to_portfolio', 0.5)
            target_vol_annual = np.sqrt(target_portfolio_volatility * 252)  # Daily to annual
            
            # Position sizing formula
            position_value = account_balance * target_vol_annual / (stock_vol * np.sqrt(1 - correlation**2))
            
            return min(position_value, account_balance * 0.15)  # Cap at 15% of account
        
        elif sizing_type == PositionSizingType.RISK_PARITY:
            # Equal risk contribution from each position
            if position_data is None or 'stop_loss' not in position_data:
                return account_balance * 0.10
            
            stop_distance = abs(position_data['entry_price'] - position_data['stop_loss']) / entry_price
            target_risk_per_position = risk_per_trade_pct / len(position_data.get('active_positions', [1]))
            
            return min(target_risk_per_position / stop_distance * stock_price, account_balance * 0.12)
        
        else:
            raise ValueError(f"Unknown sizing type: {sizing_type}")
    
    @staticmethod
    def calculate_var(
        returns_data: pd.Series,
        confidence_level: float = 0.95,
        horizon_days: int = 1
    ) -> float:
        """
        Calculate Value-at-Risk (VaR) for a portfolio.
        
        Args:
            returns_data: Historical returns series
            confidence_level: Confidence level (e.g., 0.95 = 95% confidence)
            horizon_days: Time horizon for VaR calculation
            
        Returns:
            Daily VaR as percentage of portfolio value
        """
        if len(returns_data) < 25:
            # Not enough data - use parametric method with default vol
            daily_vol = returns_data.std()
        else:
            daily_vol = returns_data.std()
        
        # Parametric (variance-covariance) VaR
        mean_return = returns_data.mean()
        z_score = -1 * np.abs(stats.ppf(confidence_level, 0))
        var_pct = mean_return + (z_score * daily_vol)
        
        # Adjust for time horizon
        adjusted_var = abs(var_pct) * np.sqrt(horizon_days / 252)
        
        return adjusted_var
    
    @staticmethod
    def track_drawdown(
        equity_curve: pd.Series,
        max_drawdown_pct: float = None
    ) -> Dict[str, any]:
        """
        Calculate and track drawdown metrics.
        
        Args:
            equity_curve: Cumulative portfolio value or returns series
            max_drawdown_pct: Maximum allowed drawdown (returns as soon as exceeded)
            
        Returns:
            Dict with drawdown analysis including current, maximum, recovery status
        """
        if len(equity_curve) == 0:
            return {
                'current_drawdown': 0.0,
                'max_drawdown': 0.0,
                'in_drawdown': False,
                'drawdown_start_date': None,
                'current_dd': pd.Series(dtype='float')
            }
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown (how far below peak)
        drawdowns = equity_curve / running_max - 1
        
        # Absolute values for reporting
        abs_drawdowns = abs(drawdowns)
        
        # Calculate metrics
        current_dd = abs(drawdowns.iloc[-1]) if len(drawdowns) > 0 else 0.0
        max_dd = abs_drawdowns.max()
        
        # Track drawdown period
        drawdown_start_idx = np.where(
            drawdowns < (running_max - 1 - max_dd) | 
            (running_max == equity_curve.iloc[0] if isinstance(equity_curve, pd.Series) else False)
        )[0][-1] if len(drawdowns) > 0 else None
        
        # Check if currently in drawdown
        current_in_dd = current_dd > 0
        
        return {
            'current_drawdown': current_dd,
            'max_drawdown': max_dd,
            'in_drawdown': current_in_dd,
            'drawdown_start_date': equity_curve.index[drawdown_start_idx] if drawdown_start_idx is not None else None,
            'equity_curve': equity_curve
        }
    
    @staticmethod
    def calculate_risk_reward(
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_quantity: int = 100
    ) -> Dict[str, any]:
        """
        Calculate risk/reward metrics for a position.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price level
            take_profit: Take-profit price level
            position_quantity: Number of shares
            
        Returns:
            Dict with R:R ratio, dollar risk/reward, win/loss amounts
        """
        if stop_loss > entry_price or take_profit < entry_price:
            raise ValueError("Invalid stop-loss or take-profit levels")
        
        risk_per_share = abs(entry_price - stop_loss)
        reward_per_share = take_profit - entry_price
        
        total_risk = risk_per_share * position_quantity
        total_reward = reward_per_share * position_quantity
        
        risk_reward_ratio = total_reward / total_risk if total_risk > 0 else 0
        
        return {
            'risk_per_share': risk_per_share,
            'reward_per_share': reward_per_share,
            'total_risk': total_risk,
            'total_reward': total_reward,
            'risk_reward_ratio': risk_reward_ratio,
            'is_positive_r:R': risk_reward_ratio >= 1.0,
            'min_win_percentage': (reward_per_share / risk_reward_ratio) * 100
        }
    
    @staticmethod
    def validate_position(
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        account_balance: float,
        stock_price: float,
        position_data: Dict = None
    ) -> Tuple[bool, str]:
        """
        Validate that a position meets risk management rules.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop-loss level
            take_profit: Take-profit level
            account_balance: Account balance
            stock_price: Current stock price
            position_data: Additional position context
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check 1: Valid price levels
        if stop_loss >= entry_price:
            return False, "Stop-loss must be below entry price for longs"
        
        if take_profit <= entry_price:
            return False, "Take-profit must be above entry price for longs"
        
        # Check 2: Minimum R:R ratio
        risk_reward = RiskManager.calculate_risk_reward(
            entry_price, stop_loss, take_profit, 100
        )
        
        if risk_reward['risk_reward_ratio'] < 1.5:
            return False, f"R:R ratio ({risk_reward['risk_reward_ratio']:.2f}) below minimum of 1.5"
        
        # Check 3: Position size doesn't exceed limits
        position_value = entry_price * 100  # Assume 100 shares default
        if position_value > account_balance * 0.25:
            return False, f"Position size ({position_value/1000:.0f}k) exceeds 25% of account"
        
        # Check 4: Stop loss is not too tight (slippage buffer)
        stop_pct = abs(entry_price - stop_loss) / entry_price
        
        if stop_pct < 0.02:  # Less than 2%
            return False, "Stop-loss too tight - adjust for slippage"
        
        return True, "Valid position"


def get_risk_manager_config() -> Dict[str, any]:
    """
    Get default risk management configuration.
    
    Returns recommended settings for standard trading strategy.
    """
    return {
        'stop_loss': {
            'type': StopLossType.VOLATILITY_ADJUSTED.value,
            'atr_period': 14,
            'atr_multiplier': 2.0,
            'volatility_threshold': 0.25
        },
        'take_profit': {
            'type': TakeProfitType.RISK_REWARD_RATIO.value,
            'risk_reward_ratio': 2.5
        },
        'position_sizing': {
            'type': PositionSizingType.VOLATILITY_TARGETING.value,
            'risk_per_trade_pct': 0.02,
            'target_portfolio_volatility': 0.15
        },
        'var_analysis': {
            'confidence_level': 0.95,
            'horizon_days': 1
        },
        'drawdown_limits': {
            'max_allowed': 0.20,
            'margin_call': 0.15,
            'liquidation': 0.10
        }
    }
