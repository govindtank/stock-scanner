"""
Configuration System for Stock Scanner
======================================

This module provides a flexible configuration system with presets:
- Trading parameters
- Risk management settings
- Data source configurations
- Alert preferences
"""

from enum import Enum
from typing import Dict, List, Optional, Any


class ScanType(Enum):
    """Available scan types."""
    DARVAS_BREAKOUT = "darvas_breakout"
    MEAN_REVERSION = "mean_reversion"
    GAP_ANALYSIS = "gap_analysis"
    MOMENTUM = "momentum"
    RELATIVE_STRENGTH = "relative_strength"
    VOLUME_PATTERN = "volume_pattern"


class RiskLevel(Enum):
    """Risk levels for trading configuration."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class Timeframe(Enum):
    """Trading timeframes."""
    INTRADAY_5M = "intraday_5m"
    INTRADAY_15M = "intraday_15m"
    DAILY = "daily"
    WEEKLY = "weekly"


class Configuration:
    """Main configuration class for the stock scanner."""
    
    # Default trading parameters
    TRADING_CONFIG = {
        'max_positions': 10,
        'min_position_size': 100,
        'max_position_size': 1000,
        'take_profit_percentage': 5.0,
        'stop_loss_percentage': 3.0,
        'trailing_stop_enabled': True,
        'trailing_stop_distance': 2.0,
    }
    
    # Default risk management settings
    RISK_CONFIG = {
        'risk_level': RiskLevel.MODERATE,
        'max_portfolio_risk': 0.10,  # Max 10% of portfolio at risk
        'position_sizing_method': 'kelly',  # kelly, fixed, volatility_adjusted
        'daily_loss_limit_pct': 5.0,  # Stop trading after -5% daily
        'drawdown_limit_pct': 10.0,   # Stop trading after max drawdown
    }
    
    # Default scan parameters
    SCAN_CONFIG = {
        'darvas_window_size': 5,
        'darvas_min_volatility': 0.02,
        'darvas_volume_threshold': 1.5,
        'mean_reversion_rsi_period': 14,
        'mean_reversion_oversold': 30,
        'mean_reversion_overbought': 70,
        'gap_analysis_threshold': 0.025,
        'momentum_period': 5,
        'volume_spike_threshold': 2.0,
    }
    
    # Default alert preferences
    ALERT_CONFIG = {
        'breakout_alerts': True,
        'pattern_alerts': False,
        'daily_summary': True,
        'email_notifications': False,
        'alert_channels': ['console'],  # console, email, webhook
    }
    
    # Default data sources
    DATA_CONFIG = {
        'primary_source': 'yfinance',  # yfinance, alpha_vantage, finnhub
        'interval': '1d',  # 1m, 5m, 15m, 60m, daily
        'period': '3mo',    # 1mo, 3mo, 6mo, 1y, 2y, 5y
        'adjust_splits': True,
        'adjust_dividends': True,
    }
    
    # Default chart settings
    CHART_CONFIG = {
        'enable_plotly_charts': True,
        'chart_width': 800,
        'chart_height': 600,
        'grid_enabled': True,
        'theme': 'seaborn'  # seaborn, matplotlib
    }


class Preset:
    """Trading strategy presets."""
    
    @staticmethod
    def darvas_breakout() -> Dict[str, Any]:
        """Darvas Box Breakout Preset."""
        return {
            'scan_type': ScanType.DARVAS_BREAKOUT.value,
            'trading': {
                'take_profit_pct': 6.0,
                'stop_loss_pct': 4.0,
                'position_size_units': 2,  # Kelly criterion: 2 units
            },
            'scan_params': {
                'darvas_window_size': 5,
                'darvas_volume_threshold': 1.5,
                'min_breakout_strength': 'STRONG',
            },
        }
    
    @staticmethod
    def mean_reversion() -> Dict[str, Any]:
        """Mean Reversion Preset (RSI, Bollinger Bands)."""
        return {
            'scan_type': ScanType.MEAN_REVERSION.value,
            'trading': {
                'take_profit_pct': 3.5,
                'stop_loss_pct': 2.0,
                'position_size_units': 1,  # Smaller positions for mean reversion
            },
            'scan_params': {
                'mean_reversion_rsi_period': 14,
                'mean_reversion_oversold': 30,
                'mean_reversion_overbought': 70,
                'bb_period': 20,
                'bb_std': 2.0,
            },
        }
    
    @staticmethod
    def momentum() -> Dict[str, Any]:
        """Momentum Trading Preset."""
        return {
            'scan_type': ScanType.MOMENTUM.value,
            'trading': {
                'take_profit_pct': 8.0,
                'stop_loss_pct': 5.0,
                'position_size_units': 3,  # Larger positions for strong momentum
            },
            'scan_params': {
                'momentum_period': 5,
                'min_momentum_pct': 0.03,
                'volume_spike_threshold': 2.0,
            },
        }
    
    @staticmethod
    def gap_trading() -> Dict[str, Any]:
        """Gap Trading Preset."""
        return {
            'scan_type': ScanType.GAP_ANALYSIS.value,
            'trading': {
                'take_profit_pct': 4.0,
                'stop_loss_pct': 2.5,
                'min_gap_size': 0.03,  # 3% gap
            },
            'scan_params': {
                'gap_analysis_threshold': 0.03,
                'min_gap_volume_multiplier': 1.5,
            },
        }
    
    @staticmethod
    def relative_strength() -> Dict[str, Any]:
        """Relative Strength Preset."""
        return {
            'scan_type': ScanType.RELATIVE_STRENGTH.value,
            'trading': {
                'take_profit_pct': 5.0,
                'stop_loss_pct': 3.5,
                'position_size_units': 2,
            },
            'scan_params': {
                'comparison_period': 5,
                'min_relative_strength_pct': 3.0,
            },
        }
    
    @staticmethod
    def volume_patterns() -> Dict[str, Any]:
        """Volume Pattern Trading Preset."""
        return {
            'scan_type': ScanType.VOLUME_PATTERN.value,
            'trading': {
                'take_profit_pct': 4.5,
                'stop_loss_pct': 3.0,
                'volume_confirmation_required': True,
            },
            'scan_params': {
                'volume_spike_threshold': 2.0,
                'sustained_volume_periods': 3,
            },
        }


class Presets:
    """Collection of all available presets."""
    
    PRESETS = {
        'darvas_breakout': Preset.darvas_breakout(),
        'mean_reversion': Preset.mean_reversion(),
        'momentum': Preset.momentum(),
        'gap_trading': Preset.gap_trading(),
        'relative_strength': Preset.relative_strength(),
        'volume_patterns': Preset.volume_patterns(),
    }
    
    @classmethod
    def get_all_presets(cls) -> Dict[str, Dict]:
        """Get all available presets."""
        return cls.PRESETS.copy()
    
    @classmethod
    def validate_preset(cls, preset_name: str) -> bool:
        """Validate that a preset name exists."""
        return preset_name in cls.PRESETS


def get_full_config(preset_name: str = None, 
                     custom_params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Get complete configuration with optional preset and custom parameters.
    
    Args:
        preset_name: Name of preset to apply (e.g., 'darvas_breakout')
        custom_params: Override parameters
        
    Returns:
        Complete configuration dictionary
    """
    # Start with base configuration
    config = {
        'trading': Configuration.TRADING_CONFIG.copy(),
        'risk': Configuration.RISK_CONFIG.copy(),
        'scan': Configuration.SCAN_CONFIG.copy(),
        'alerts': Configuration.ALERT_CONFIG.copy(),
        'data': Configuration.DATA_CONFIG.copy(),
        'charts': Configuration.CHART_CONFIG.copy(),
    }
    
    # Apply preset if specified
    if preset_name and Presets.validate_preset(preset_name):
        base_config = Presets.PRESETS[preset_name]
        
        # Merge base config from preset into our config
        for section in ['scan_params', 'trading']:
            if section in base_config:
                current_section = config.get(section, {})
                config[section] = {**current_section, **base_config.get(section, {})}
    
    # Apply custom parameters (overrides)
    if custom_params:
        for key, value in custom_params.items():
            # Handle nested keys like 'scan.darvas_window_size'
            parts = key.split('.')
            target = config
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value
    
    return config


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration parameters.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check trading parameters
    trading = config.get('trading', {})
    if trading.get('max_positions', 0) <= 0:
        errors.append("max_positions must be positive")
    if trading.get('take_profit_percentage', 0) < 1 or trading.get('take_profit_percentage', 0) > 50:
        errors.append("take_profit_percentage should be between 1% and 50%")
    if trading.get('stop_loss_percentage', 0) < 1 or trading.get('stop_loss_percentage', 0) > 20:
        errors.append("stop_loss_percentage should be between 1% and 20%")
    
    # Check risk parameters
    risk = config.get('risk', {})
    if risk.get('max_portfolio_risk', 0) < 0.01 or risk.get('max_portfolio_risk', 0) > 0.30:
        errors.append("max_portfolio_risk should be between 1% and 30%")
    
    # Check scan parameters
    scan = config.get('scan', {})
    if 'darvas' in str(scan) and (
        scan.get('darvas_window_size', 0) < 2 or 
        scan.get('darvas_window_size', 0) > 30
    ):
        errors.append("darvas_window_size should be between 2 and 30")
    
    return errors


def save_config(config: Dict[str, Any], filepath: str = 'config.json'):
    """Save configuration to JSON file."""
    import json
    
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration saved to {filepath}")


def load_config(filepath: str = 'config.json') -> Dict[str, Any]:
    """Load configuration from JSON file."""
    import json
    
    try:
        with open(filepath, 'r') as f:
            config = json.load(f)
        print(f"Configuration loaded from {filepath}")
        return config
    except FileNotFoundError:
        print(f"Config file {filepath} not found. Using defaults.")
        return get_full_config()
    except Exception as e:
        print(f"Error loading config: {e}. Using defaults.")
        return get_full_config()


# Example usage and configuration examples
if __name__ == '__main__':
    
    # Print all presets
    print("=" * 60)
    print("AVAILABLE PRESETS:")
    print("=" * 60)
    for name, preset in Presets.get_all_presets().items():
        print(f"\n{name.upper()}:")
        print(f"  Scan Type: {preset.get('scan_type')}")
        print(f"  Take Profit: {preset.get('trading', {}).get('take_profit_pct')}%")
        print(f"  Stop Loss: {preset.get('trading', {}).get('stop_loss_pct')}%")
    
    # Show default configuration
    print("\n" + "=" * 60)
    print("DEFAULT CONFIGURATION:")
    print("=" * 60)
    
    config = get_full_config()
    print(f"Scan Type: {config.get('scan_params', {}).get('darvas_window_size')} day window")
    print(f"Take Profit: {config.get('trading', {}).get('take_profit_pct')}%")
    print(f"Stop Loss: {config.get('trading', {}).get('stop_loss_pct')}%")
    
    # Example: Load with Darvas Breakout preset
    config = get_full_config(preset_name='darvas_breakout')
    print("\n" + "=" * 60)
    print("DARVAS BREAKOUT PRESET:")
    print("=" * 60)
    print(f"Scan Type: {config.get('scan_params', {}).get('min_breakout_strength')}")
    
    # Example: Custom configuration
    custom_config = get_full_config(
        preset_name='mean_reversion',
        custom_params={
            'scan.mean_reversion_oversold': 25,
            'trading.take_profit_pct': 4.0,
        }
    )
    print("\n" + "=" * 60)
    print("CUSTOM CONFIGURATION:")
    print("=" * 60)
    print(f"RSI Oversold: {custom_config.get('scan_params', {}).get('mean_reversion_oversold')}")
    print(f"Custom Take Profit: {custom_config.get('trading', {}).get('take_profit_pct')}%")
