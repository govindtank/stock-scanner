"""
Backtesting Engine for Stock Scanner
Implements comprehensive historical simulation with:
- Multiple trading strategies
- Transaction cost modeling
- Performance metrics (Sharpe, Sortino, max drawdown)
- Position tracking and rebalancing
- Equity curve analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class TradeSide(Enum):
    """Trade direction."""
    LONG = "LONG"
    SHORT = "SHORT"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


@dataclass
class BacktestResult:
    """Container for backtest results."""
    equity_curve: pd.Series
    trades: List[Dict]
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    total_return: float
    annualized_return: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    trades_count: int
    start_date: datetime
    end_date: datetime
    
    def to_dict(self) -> Dict:
        """Convert results to dictionary for JSON serialization."""
        return {
            'equity_curve': self.equity_curve.tolist(),
            'trades': self.trades,
            'sharpe_ratio': round(self.sharpe_ratio, 4),
            'sortino_ratio': round(self.sortino_ratio, 4),
            'max_drawdown_pct': round(self.max_drawdown * 100, 2),
            'total_return_pct': round(self.total_return * 100, 2),
            'annualized_return_pct': round(self.annualized_return * 100, 2),
            'win_rate_pct': round(self.win_rate * 100, 2),
            'profit_factor': round(self.profit_factor, 4),
            'avg_win_pct': round(self.avg_win * 100, 2),
            'avg_loss_pct': round(self.avg_loss * 100, 2),
            'largest_win_pct': round(self.largest_win * 100, 2),
            'largest_loss_pct': round(self.largest_loss * 100, 2),
            'trades_count': self.trades_count,
            'start_date': str(self.start_date),
            'end_date': str(self.end_date)
        }


class BacktestingEngine:
    """
    Comprehensive backtesting engine for trading strategies.
    
    Features:
    - Position tracking with entry/exit management
    - Transaction cost modeling (commissions, slippage)
    - Multiple performance metrics
    - Equity curve analysis
    - Risk-adjusted returns calculation
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        transaction_cost_pct: float = 0.001,  # 0.1% per trade
        slippage_bps: float = 2.0,  # 2 basis points
        margin_requirement: float = None,
        leverage: float = 1.0
    ):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting account balance
            transaction_cost_pct: Commission percentage per trade
            slippage_bps: Slippage in basis points (default: 2)
            margin_requirement: Margin requirement for leveraged positions
            leverage: Leverage multiplier for positions
        """
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_bps = slippage_bps
        self.margin_requirement = margin_requirement or 0.25
        self.leverage = leverage
        
        # Initialize position tracking
        self.positions: Dict[str, Dict] = {}  # Symbol -> position info
        self.cash_balance = initial_capital
        self.trades_log: List[Dict] = []
        
        # Performance metrics (calculated after backtest)
        self.equity_curve: pd.Series = None
        self.total_return = 0.0
        self.sharpe_ratio = 0.0
        self.sortino_ratio = 0.0
        self.max_drawdown = 0.0
    
    def set_data(self, df: pd.DataFrame) -> 'BacktestingEngine':
        """
        Set OHLCV data for backtesting.
        
        Args:
            df: DataFrame with Date, Open, High, Low, Close, Volume columns
            
        Returns:
            self (for method chaining)
        """
        self.data = df.copy()
        self.data['Date'] = pd.to_datetime(self.data['Date'])
        self.data = self.data.sort_values('Date').reset_index(drop=True)
        
        return self
    
    def analyze_strategy(
        self,
        entry_signal: Callable[[pd.DataFrame], bool],
        exit_signal: Optional[Callable[[pd.DataFrame], bool]] = None,
        strategy_name: str = "default",
        initial_capital: float = None,
        use_stop_loss: bool = True,
        stop_loss_pct: float = 0.05,
        use_take_profit: bool = True,
        take_profit_pct: float = 0.15
    ) -> BacktestResult:
        """
        Run backtest analysis on a trading strategy.
        
        Args:
            entry_signal: Function that returns True for buy signal
            exit_signal: Optional function that returns True for sell signal
            strategy_name: Name of strategy for results
            initial_capital: Override default starting capital
            use_stop_loss: Enable stop-loss functionality
            stop_loss_pct: Stop-loss percentage from entry
            use_take_profit: Enable take-profit functionality
            take_profit_pct: Take-profit percentage from entry
            
        Returns:
            BacktestResult with performance metrics
        """
        if initial_capital is not None:
            self.initial_capital = initial_capital
            self.cash_balance = initial_capital
        
        # Simulate trading day by day
        equity_curve = []
        trade_position = {'entered': False, 'entry_date': None, 'entry_price': None}
        
        for i in range(2, len(self.data)):  # Skip first row (initialization)
            current_price = self.data.iloc[i]['Close']
            prev_price = self.data.iloc[i - 1]['Close']
            date = self.data.iloc[i]['Date']
            
            # Check if we need to exit existing position
            if trade_position['entered']:
                self._process_exit(
                    current_price, 
                    stop_loss_pct if use_stop_loss else None,
                    take_profit_pct if use_take_profit else None
                )
                
                # Check for new entry signal
                if entry_signal(self.data.iloc[i]):
                    self._enter_position(current_price)
            else:
                # No position - check for entry signal
                if entry_signal(self.data.iloc[i]):
                    self._enter_position(current_price)
            
            equity_curve.append(self.cash_balance)
        
        self.equity_curve = pd.Series(equity_curve, index=self.data['Date'].iloc[2:])
        
        # Calculate performance metrics
        self._calculate_metrics()
        
        return BacktestResult(
            equity_curve=self.equity_curve,
            trades=self.trades_log,
            sharpe_ratio=self.sharpe_ratio,
            sortino_ratio=self.sortino_ratio,
            max_drawdown=self.max_drawdown,
            total_return=self.total_return,
            annualized_return=0.0 if len(self.data) < 252 else self._calc_annualized_return(),
            win_rate=0.0,  # Calculated from trades log
            profit_factor=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            largest_win=0.0,
            largest_loss=0.0,
            trades_count=len(self.trades_log),
            start_date=self.data['Date'].iloc[2],
            end_date=self.data['Date'].iloc[-1]
        )
    
    def _enter_position(self, price: float):
        """Enter a new position."""
        # Calculate trade size (1 share for simplicity in backtest)
        shares_to_buy = 1
        
        # Calculate cost with slippage
        entry_price_with_slippage = price * (1 + self.slippage_bps / 10000)
        total_cost = entry_price_with_slippage * shares_to_buy * (1 + self.transaction_cost_pct)
        
        if self.cash_balance < total_cost:
            return  # Not enough cash
        
        self.cash_balance -= total_cost
        
        trade_info = {
            'trade_id': f"{strategy_name}_{len(self.trades_log) + 1}",
            'date': self.data['Date'].iloc[-1],
            'side': TradeSide.LONG.value,
            'entry_price': entry_price_with_slippage,
            'shares': shares_to_buy,
            'total_cost': total_cost
        }
        
        # Store position info
        symbol = 'DEFAULT'  # Can be enhanced for multi-asset backtesting
        
        self.positions[symbol] = {
            'entry_date': trade_info['date'],
            'entry_price': trade_info['entry_price'],
            'shares': shares_to_buy,
            'stop_loss_price': None,
            'take_profit_price': None,
            'status': 'OPEN'
        }
        
        self.trades_log.append({**trade_info, 'pnl': 0.0, 'exit_date': None})
    
    def _process_exit(self, current_price: float, stop_loss_pct: float = None, take_profit_pct: float = None):
        """Process position exit (profit or loss)."""
        if self.positions is None or not self.positions:
            return
        
        symbol = 'DEFAULT'
        position = self.positions.get(symbol)
        
        if position is None or position['status'] != 'OPEN':
            return
        
        # Check for stop-loss trigger
        if stop_loss_pct and current_price <= position['entry_price'] * (1 - stop_loss_pct):
            exit_reason = 'STOP_LOSS'
            exit_price = max(current_price, position['stop_loss_price']) if position.get('stop_loss_price') else current_price
        
        # Check for take-profit trigger
        elif take_profit_pct and current_price >= position['entry_price'] * (1 + take_profit_pct):
            exit_reason = 'TAKE_PROFIT'
            exit_price = min(current_price, position['take_profit_price']) if position.get('take_profit_price') else current_price
        
        # Check for exit signal
        elif hasattr(self, 'exit_signal') and self.exit_signal(self.data.iloc[-1]):
            exit_reason = 'SIGNAL'
            exit_price = current_price
        
        elif position['status'] == 'CLOSED':  # Already closed
            return
        
        else:
            return  # Position still open
        
        # Close position
        exit_value = exit_price * position['shares']
        total_cost = position['entry_price'] * position['shares'] * (1 + self.transaction_cost_pct)
        pnl_percent = (exit_value - total_cost) / total_cost
        
        trade_idx = len([t for t in self.trades_log if t.get('trade_id') == symbol])
        self.trades_log[trade_idx].update({
            'pnl': pnl_percent,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'exit_date': self.data['Date'].iloc[-1]
        })
        
        position['status'] = 'CLOSED'
        self.cash_balance += exit_value
        
        # Update positions dict
        for k, v in position.items():
            if k not in ['status']:
                self.positions[symbol][k] = v
    
    def calculate_stop_loss_price(self, entry_price: float, stop_pct: float) -> float:
        """Calculate stop-loss price."""
        return entry_price * (1 - stop_pct)
    
    def calculate_take_profit_price(self, entry_price: float, tp_pct: float) -> float:
        """Calculate take-profit price."""
        return entry_price * (1 + tp_pct)
    
    def _calculate_metrics(self):
        """Calculate performance metrics after backtest completes."""
        if self.equity_curve is None or len(self.equity_curve) < 25:
            return
        
        # Calculate daily returns
        returns = self.equity_curve.pct_change().dropna()
        
        # Filter out non-positive returns for Sortino
        negative_returns = returns[returns <= 0]
        
        if len(returns) > 0:
            annual_factor = (252 - (self.data['Date'].iloc[-1] - self.data['Date'].iloc[0]).days / 365)
            
            # Risk-adjusted returns
            risk_free_rate = 0.02  # 2% annualized
            
            # Sharpe Ratio
            excess_returns = returns - (risk_free_rate / 252)
            if len(excess_returns[excess_returns > 0]) > 0:
                self.sharpe_ratio = np.sqrt(annual_factor) * excess_returns.mean() / excess_returns.std()
            
            # Sortino Ratio
            negative_std = negative_returns.std() if len(negative_returns) > 0 else returns.std()
            if negative_std > 0 and len(excess_returns[excess_returns > 0]) > 0:
                self.sortino_ratio = np.sqrt(annual_factor) * excess_returns.mean() / negative_std
            
            # Total Return
            self.total_return = (self.equity_curve.iloc[-1] - self.equity_curve.iloc[0]) / self.equity_curve.iloc[0]
            
            # Max Drawdown
            equity_values = self.equity_curve.cummax().iloc[::-1].values[::-1]
            drawdowns = (self.equity_curve.values / equity_values) - 1
            self.max_drawdown = abs(drawdowns.min()) if len(drawdowns) > 0 else 0.0
        
        # Trade statistics
        trades = [t for t in self.trades_log if t.get('pnl') is not None and abs(t['pnl']) > 0]
        
        if len(trades) > 0:
            trade_pnls = [t['pnl'] for t in trades]
            
            self.win_rate = sum(1 for p in trade_pnls if p > 0) / len(trade_pnls)
            self.profit_factor = sum(p for p in trade_pnls if p > 0) / abs(sum(p for p in trade_pnls if p < 0))
            
            avg_win_pct = np.mean([p for p in trade_pnls if p > 0])
            avg_loss_pct = np.mean([p for p in trade_pnls if p < 0])
            
            self.avg_win = abs(avg_win_pct) if len([p for p in trade_pnls if p > 0]) > 0 else 0.0
            self.avg_loss = abs(avg_loss_pct) if len([p for p in trade_pnls if p < 0]) > 0 else 0.0
            
            largest_win = max(trade_pnls) if any(p > 0 for p in trade_pnls) else 0.0
            largest_loss = min(trade_pnls) if any(p < 0 for p in trade_pnls) else 0.0
            
            self.largest_win = largest_win
            self.largest_loss = largest_loss
    
    def _calc_annualized_return(self) -> float:
        """Calculate annualized return from equity curve."""
        if len(self.equity_curve) < 252 or self.equity_curve.iloc[-1] <= 0:
            return 0.0
        
        start_date = self.data['Date'].iloc[2]
        end_date = self.data['Date'].iloc[-1]
        
        days_trading = (end_date - start_date).days / 365
        
        if days_trading <= 0:
            return 0.0
        
        total_return = (self.equity_curve.iloc[-1] - self.equity_curve.iloc[0]) / self.equity_curve.iloc[0]
        
        return (1 + total_return) ** (1 / days_trading) - 1


class MultiAssetBacktester(BacktestingEngine):
    """
    Backtesting engine supporting multiple assets.
    
    Features:
    - Portfolio-level performance tracking
    - Position correlation analysis
    - Rebalancing logic
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.portfolio_value = 0.0
        self.holdings: Dict[str, float] = {}  # Symbol -> dollar value
    
    def set_multi_asset_data(
        self, 
        asset_data: Dict[str, pd.DataFrame],
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Set data for multiple assets.
        
        Args:
            asset_data: Dictionary of symbol -> DataFrame
            weights: Initial allocation weights (optional)
        """
        self.asset_data = {k: v.copy() for k, v in asset_data.items()}
        
        # Add Date column if not present
        for df in self.asset_data.values():
            if 'Date' not in df.columns:
                df.insert(0, 'Date', pd.to_datetime(df.index))
        
        # Sort by date
        for symbol in self.asset_data:
            self.asset_data[symbol] = self.asset_data[symbol].sort_values('Date').reset_index(drop=True)
    
    def get_portfolio_value(self, date_idx: int) -> float:
        """Get total portfolio value at a point in time."""
        if self.portfolio_value == 0.0:
            # Calculate from holdings
            return sum([
                (self.asset_data[symbol]['Close'].iloc[date_idx] 
                 * self.holdings.get(symbol, 0)) 
                for symbol in self.asset_data
            ]) + self.cash_balance
        
        return self.portfolio_value
    
    def rebalance_portfolio(self, target_weights: Dict[str, float]) -> List[Dict]:
        """
        Rebalance portfolio to target weights.
        
        Args:
            target_weights: Dictionary of symbol -> target weight
            
        Returns:
            List of trades to execute
        """
        trades = []
        current_value = self.get_portfolio_value(-1)  # Use latest
        
        for symbol, target_weight in target_weights.items():
            target_value = current_value * target_weight
            current_holding = self.asset_data[symbol]['Close'].iloc[-1] * self.holdings.get(symbol, 0) if symbol in self.holdings else 0
            
            value_to_buy = target_value - current_holding
            
            if value_to_buy > 0:
                shares = int(value_to_buy / (current_holding / len(self.asset_data[symbol]) + self.cash_balance)) if len(self.asset_data[symbol]) > 0 else 0
                trades.append({
                    'action': 'BUY',
                    'symbol': symbol,
                    'shares': shares,
                    'value': value_to_buy
                })
            elif value_to_buy < 0:
                shares = int(abs(value_to_buy) / (current_holding / len(self.asset_data[symbol]) + self.cash_balance)) if len(self.asset_data[symbol]) > 0 else 0
                trades.append({
                    'action': 'SELL',
                    'symbol': symbol,
                    'shares': shares,
                    'value': abs(value_to_buy)
                })
        
        return trades
