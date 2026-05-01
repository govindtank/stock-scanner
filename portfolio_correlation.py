"""
Portfolio Correlation Analysis Module for Stock Scanner
Implements advanced correlation and diversification metrics:
- Pairwise correlation matrices
- Portfolio-level risk decomposition
- Over-concentration detection
- Diversification scoring
- Sector correlation analysis (simulated)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict


class CorrelationAnalyzer:
    """
    Portfolio correlation and diversification analysis.
    
    Helps identify over-concentration risks and optimize asset allocation.
    """
    
    @staticmethod
    def calculate_correlation_matrix(
        data_dict: Dict[str, pd.Series],
        window: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Calculate rolling correlation matrix between assets.
        
        Args:
            data_dict: Dictionary of asset_name -> price returns series
            window: Rolling window size (None for full-sample)
            
        Returns:
            Correlation matrix DataFrame with date index if rolling, columns otherwise
        """
        # Align all series to same index
        aligned_data = {}
        for name, series in data_dict.items():
            if hasattr(series.index, 'union') or hasattr(series.index, 'join'):
                aligned_data[name] = series.reindex(
                    {k: list(v) for k, v in list(data_dict.items())[0].items()}
                ).fillna(method='ffill').fillna(0)
            else:
                aligned_data[name] = series
        
        # Calculate returns if prices provided
        correlation_data = {}
        for name, price_series in data_dict.items():
            if isinstance(price_series.iloc[0], (int, float)):
                returns = np.log(price_series.pct_change().fillna(0))
                correlation_data[name] = returns.fillna(0)
        
        # Calculate correlations
        if not correlation_data:
            return pd.DataFrame()
        
        df_corr = pd.DataFrame(correlation_data)
        
        if window is None:
            # Full-sample correlation matrix
            corr_matrix = df_corr.corr()
        else:
            # Rolling correlation matrix
            rolling_corr = []
            for i in range(window, len(df_corr)):
                window_data = df_corr.iloc[i-window:i+1].pct_change() if hasattr(df_corr.iloc[i-window:i+1], 'pct_change') else df_corr.iloc[i-window:i+1]
                corr_matrix_window = rolling_corr[-1] if rolling_corr else pd.DataFrame()
                rolling_corr.append(corr_matrix_window)
            
            return pd.DataFrame(rolling_corr).mean(axis=0).to_frame().T
        
        return corr_matrix
    
    @staticmethod
    def decompose_portfolio_risk(
        correlations: pd.DataFrame,
        asset_weights: Dict[str, float],
        individual_vols: Dict[str, float]
    ) -> pd.DataFrame:
        """
        Decompose portfolio risk by asset and correlation.
        
        Args:
            correlations: Asset correlation matrix
            asset_weights: Dictionary of asset weights in portfolio
            individual_vols: Dictionary of asset volatilities
            
        Returns:
            DataFrame with variance contribution analysis
        """
        assets = list(correlations.columns)
        n_assets = len(assets)
        
        # Portfolio weights as numpy array
        weights_array = np.array([asset_weights.get(asset, 0) for asset in assets])
        
        # Individual volatilities as numpy array
        vols_array = np.array([individual_vols.get(asset, 0.2) for asset in assets]) / 100
        
        # Covariance matrix
        cov_matrix = pd.DataFrame(
            data=np.outer(vols_array, vols_array) * correlations.values,
            index=assets,
            columns=assets
        )
        
        # Portfolio variance (weight vector times covariance matrix times weight vector transpose)
        portfolio_variance = weights_array @ cov_matrix @ weights_array
        
        # Risk contribution by asset
        risk_contributions = pd.DataFrame(index=assets, columns=['%_Risk'])
        
        for i, asset in enumerate(assets):
            weight = weights_array[i]
            marginal_risk_contribution = np.dot(cov_matrix.iloc[:, i], weights_array)
            risk_contribution = (weight * marginal_risk_contribution) / portfolio_variance
            risk_contributions.loc[asset, '%_Risk'] = risk_contribution
        
        # Sort by risk contribution
        risk_contributions = risk_contributions.sort_values('%_Risk', ascending=False)
        
        return risk_contributions
    
    @staticmethod
    def check_overconcentration(
        asset_weights: Dict[str, float],
        correlations: pd.DataFrame,
        concentration_threshold: float = 0.50,
        avg_correlation_threshold: float = 0.70
    ) -> Dict[str, any]:
        """
        Check for dangerous concentration in portfolio.
        
        Red flags:
        - Single asset > threshold weight
        - Group of correlated assets exceeding combined threshold
        - High correlation cluster within top positions
        
        Args:
            asset_weights: Portfolio weights by asset
            correlations: Asset correlation matrix
            concentration_threshold: Max weight for single asset to be concerning
            avg_correlation_threshold: Average correlation above which assets are considered same sector
            
        Returns:
            Dict with concentration analysis and alerts
        """
        n_assets = len(asset_weights)
        assets_sorted = sorted(asset_weights.items(), key=lambda x: x[1], reverse=True)
        
        alerts = []
        warnings = []
        info = {}
        
        # Check individual concentrations
        for i, (asset, weight) in enumerate(assets_sorted):
            pct_weight = weight * 100
            
            if pct_weight > concentration_threshold:
                alerts.append({
                    'type': 'HIGH_CONCENTRATION',
                    'asset': asset,
                    'weight_pct': pct_weight,
                    'severity': 'HIGH' if pct_weight > 70 else 'MEDIUM' if pct_weight > 50 else 'LOW'
                })
            
            # Check for concentration risk based on correlation
            remaining_portfolio = 1 - weight
            avg_corr_with_others = correlations[asset].iloc[assets_sorted.index(asset)+1:].mean() if i < len(assets_sorted)-1 else 0
            
            if avg_corr_with_others > avg_correlation_threshold:
                info[f'{asset}_correlation_risk'] = {
                    'avg_correlation': avg_corr_with_others,
                    'message': f'{asset} is highly correlated ({avg_corr_with_others:.2f}) with lower-weight assets'
                }
        
        # Check for "same sector" concentration
        if n_assets >= 3:
            correlations = correlations.corr()
            top_3_weight = sum([w for _, w in assets_sorted[:3]])
            
            if top_3_weight > 0.6 and len(assets_sorted) >= 5:
                warnings.append({
                    'type': 'LIMITED_DIVERSIFICATION',
                    'message': f'Top 3 positions ({top_3_weight*100:.1f}%) represent majority of portfolio',
                    'recommendation': 'Consider adding uncorrelated assets or reducing top positions'
                })
        
        # Check average correlation across portfolio
        avg_portfolio_corr = correlations.values.mean()
        
        if avg_portfolio_corr > 0.6:
            alerts.append({
                'type': 'HIGH_OVERALL_CORRELATION',
                'avg_correlation': avg_portfolio_corr,
                'severity': 'MEDIUM',
                'message': f'Average asset correlation ({avg_portfolio_corr:.2f}) suggests limited true diversification'
            })
        
        # Calculate effective number of assets (diversification metric)
        total_weight = sum(asset_weights.values())
        weighted_variance = sum(w**2 for w in asset_weights.values() if abs(w) > 0.01) / total_weight**2
        effective_n_assets = 1 / weighted_variance
        
        return {
            'alerts': alerts,
            'warnings': warnings,
            'info': info,
            'effective_number_of_assets': effective_n_assets,
            'total_positions': n_assets,
            'avg_correlation': avg_portfolio_corr,
            'is_concentrated': len(alerts) > 0 or effective_n_assets < 3
        }
    
    @staticmethod
    def calculate_diversification_score(
        correlations: pd.DataFrame,
        asset_weights: Dict[str, float]
    ) -> float:
        """
        Calculate portfolio diversification score (0-1 scale).
        
        Score of 1 = perfectly diversified (all assets uncorrelated equal weights)
        Score near 0 = poor diversification
        
        Args:
            correlations: Asset correlation matrix
            asset_weights: Portfolio weights
            
        Returns:
            Diversification score (0-1, higher is better)
        """
        if len(correlations.columns) < 2:
            return 0.0
        
        # Optimal diversification requires equal weights with zero correlations
        n_assets = len(correlations.columns)
        
        # Calculate current correlation matrix average
        avg_corr = correlations.values.mean()
        
        # Ideal scenario: all zeros (perfectly uncorrelated)
        optimal_avg_corr = 0.0
        
        # Penalty for unequal weights
        optimal_weights = 1.0 / n_assets
        weight_penalty = np.sum(np.abs(np.array(list(asset_weights.values())) - optimal_weights))
        
        # Score formula: penalize both correlation and weight imbalance
        correlation_penalty = (avg_corr - optimal_avg_corr) * 2  # Scale to 0-0.5 range
        weight_penalty_score = min(weight_penalty * 0.5, 0.3)  # Cap at 0.3
        
        diversity_score = max(0, 1.0 - correlation_penalty - weight_penalty_score)
        
        return diversity_score
    
    @staticmethod
    def find_low_correlation_assets(
        correlations: pd.DataFrame,
        exclude_assets: List[str] = None,
        max_correlation: float = 0.30
    ) -> List[Tuple[str, float]]:
        """
        Find assets with low correlation to existing portfolio.
        
        Args:
            correlations: Correlation matrix (including new candidates)
            exclude_assets: Assets to exclude from results
            max_correlation: Maximum acceptable correlation with portfolio
            
        Returns:
            List of (asset, min_correlation_to_portfolio) tuples sorted by correlation
        """
        if exclude_assets is None:
            exclude_assets = []
        
        # Get assets in current portfolio
        portfolio_assets = set(correlations.columns) - set(exclude_assets)
        
        # Find correlations to average portfolio exposure
        results = []
        for asset, corr_series in correlations.items():
            if asset in portfolio_assets:
                continue
            
            avg_corr_to_portfolio = abs(corr_series[portfolio_assets].mean())
            results.append((asset, avg_corr_to_portfolio))
        
        # Sort by correlation
        results.sort(key=lambda x: x[1])
        
        return [(asset, min_corr) for asset, min_corr in results if min_corr <= max_correlation]
    
    @staticmethod
    def analyze_sector_exposure(
        asset_data: Dict[str, pd.Series],
        sector_map: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        Analyze sector-level concentration in portfolio.
        
        Args:
            asset_data: Dictionary of asset name -> returns series
            sector_map: Dictionary mapping assets to sectors
            
        Returns:
            Sector exposure analysis
        """
        if sector_map is None:
            # Create simulated sector map based on correlation clustering
            return CorrelationAnalyzer._cluster_by_correlation(asset_data)
        
        # Calculate average weight per sector
        sector_weights = defaultdict(float)
        sector_correlations = defaultdict(lambda: defaultdict(float))
        
        for asset, returns_series in asset_data.items():
            if pd.isna(returns_series.iloc[0]):
                continue
            
            sector = sector_map.get(asset, 'UNASSIGNED')
            sector_weights[sector] += abs(returns_series.mean())
            
            # Correlation with assets in same sector
            for other_asset, other_returns in asset_data.items():
                if asset != other_asset and not pd.isna(other_returns.iloc[0]):
                    corr = returns_series.corr(other_returns)
                    sector_correlations[sector][other_sector] += abs(corr) / len(asset_data)
        
        # Convert defaultdicts to regular dicts for JSON serialization
        sector_weights = dict(sector_weights)
        sector_correlations = {k: dict(v) for k, v in sector_correlations.items()}
        
        # Normalize sector weights
        total_weight = sum(sector_weights.values())
        normalized_weights = {sector: weight/total_weight for sector, weight in sector_weights.items()} if total_weight > 0 else {}
        
        return {
            'sector_exposure': normalized_weights,
            'top_sectors': dict(sorted(normalized_weights.items(), key=lambda x: x[1], reverse=True)[:3]),
            'most_correlated_sector_pair': None
        }
    
    @staticmethod
    def _cluster_by_correlation(asset_data: Dict[str, pd.Series]) -> Dict[str, any]:
        """Create sector clusters based on correlation (>0.6 = same cluster)."""
        correlations = CorrelationAnalyzer.calculate_correlation_matrix(
            {name: data for name, data in asset_data.items() if len(data) > 0}
        )
        
        clusters = {}
        cluster_labels = {}
        label_counter = 0
        
        # Simple clustering based on correlation matrix
        assets = list(correlations.columns)
        visited = set()
        
        for asset in assets:
            if asset in visited:
                continue
            
            # Start new cluster with this asset
            current_cluster = [asset]
            visited.add(asset)
            
            # Find all assets highly correlated to any in cluster
            for other_asset in assets:
                if other_asset not in visited:
                    for cluster_asset in current_cluster:
                        corr = correlations.loc[cluster_asset, other_asset]
                        
                        if abs(corr) > 0.6:
                            current_cluster.append(other_asset)
                            visited.add(other_asset)
            
            # Assign cluster label
            if current_cluster:
                clusters[f'Sector_{label_counter}'] = list(set(current_cluster))
                for asset in current_cluster:
                    cluster_labels[asset] = f'Sector_{label_counter}'
                label_counter += 1
        
        return {
            'clusters': clusters,
            'cluster_assignment': cluster_labels
        }


class ConcentrationMonitor:
    """
    Monitor portfolio for dangerous concentration changes.
    
    Tracks:
    - Position weight drift
    - Correlation regime changes
    - Risk concentration alerts
    """
    
    def __init__(
        self,
        initial_weights: Dict[str, float],
        alert_thresholds: Optional[Dict] = None
    ):
        """
        Initialize concentration monitor.
        
        Args:
            initial_weights: Initial target weights by asset
            alert_thresholds: Alert configuration (optional)
        """
        self.initial_weights = initial_weights
        self.alert_thresholds = alert_thresholds or {
            'weight_drift_alert': 0.15,  # Alert if position drifts 15% from target
            'concentration_increase': 0.05,  # Alert if concentration increases by 5%
            'correlation_spike': 0.20,  # Alert if correlation spikes by 0.20
        }
    
    def check_concentration_change(
        self,
        current_weights: Dict[str, float],
        current_correlations: pd.DataFrame
    ) -> Dict[str, any]:
        """
        Check for concentration changes requiring attention.
        
        Args:
            current_weights: Current position weights
            current_correlations: Current correlation matrix
            
        Returns:
            Concentration monitoring report
        """
        alerts = []
        
        # Calculate weight drift
        weight_drifts = {}
        for asset in set(self.initial_weights.keys()) | set(current_weights.keys()):
            initial_weight = self.initial_weights.get(asset, 0)
            current_weight = current_weights.get(asset, 0)
            
            if abs(initial_weight + current_weight) > 0.01:
                drift_pct = (current_weight - initial_weight) / initial_weight * 100 if initial_weight != 0 else 0
                
                if abs(drift_pct) > self.alert_thresholds['weight_drift_alert']:
                    alerts.append({
                        'type': 'WEIGHT_DRIFT',
                        'asset': asset,
                        'initial_weight': initial_weight,
                        'current_weight': current_weight,
                        'drift_pct': drift_pct,
                        'severity': 'HIGH' if abs(drift_pct) > 50 else 'MEDIUM'
                    })
        
        # Check correlation regime changes
        initial_corr = self._get_initial_correlations()
        if initial_corr is not None and current_correlations is not None:
            for asset in set(initial_corr.columns) & set(current_correlations.columns):
                initial_avg = abs(initial_corr[asset].mean())
                current_avg = abs(current_correlations[asset].mean())
                
                if abs(current_avg - initial_avg) > self.alert_thresholds['correlation_spike']:
                    alerts.append({
                        'type': 'CORRELATION_CHANGE',
                        'asset': asset,
                        'initial_avg_corr': initial_avg,
                        'current_avg_corr': current_avg,
                        'change': current_avg - initial_avg
                    })
        
        return {
            'alerts': alerts,
            'alert_count': len(alerts),
            'is_safe': len(alerts) == 0,
            'recommendation': self._generate_recommendation(alerts)
        }
    
    def _get_initial_correlations(self) -> Optional[pd.DataFrame]:
        """Get initial correlations (would be stored or recalculated)."""
        return None  # In production, store initial correlation matrix
    
    def _generate_recommendation(self, alerts: List[Dict]) -> str:
        """Generate risk management recommendation."""
        if len(alerts) == 0:
            return "Portfolio within acceptable concentration limits."
        
        critical_alerts = [a for a in alerts if a.get('severity') == 'HIGH']
        
        if len(critical_alerts) > 2:
            return "CRITICAL: Multiple high-severity concentration alerts detected. " \
                   "Immediate portfolio rebalancing recommended."
        elif len(critical_alerts) == 1:
            return f"WARNING: High-severity alert for {critical_alerts[0].get('type')}. " \
                   "Consider reducing position size or hedging."
        else:
            return "Monitor portfolio concentration levels. " \
                   "Review recent market conditions affecting correlations."


def create_diversification_report(
    asset_weights: Dict[str, float],
    correlations: pd.DataFrame,
    individual_vols: Dict[str, float]
) -> Dict[str, any]:
    """
    Generate comprehensive diversification report.
    
    Args:
        asset_weights: Portfolio weights by asset
        correlations: Asset correlation matrix
        individual_vols: Asset volatilities
        
    Returns:
        Complete diversification analysis report
    """
    # Calculate metrics
    corr_matrix = CorrelationAnalyzer.calculate_correlation_matrix(
        {k: pd.Series(v) for k, v in correlations.items()}
    ) if not isinstance(correlations, pd.DataFrame) else correlations
    
    risk_decomposition = CorrelationAnalyzer.decompose_portfolio_risk(
        correlations, asset_weights, individual_vols
    )
    
    concentration_analysis = CorrelationAnalyzer.check_overconcentration(
        asset_weights, correlations
    )
    
    diversification_score = CorrelationAnalyzer.calculate_diversification_score(
        correlations, asset_weights
    )
    
    # Identify risk contributors
    top_risk_contributors = risk_decomposition.sort_values('%_Risk', ascending=False).head(3).to_dict('list')
    
    return {
        'diversification_score': round(diversification_score * 100, 2),
        'risk_decomposition': risk_decomposition.to_dict(),
        'top_risk_contributors': top_risk_contributors,
        'concentration_alerts': concentration_analysis.get('alerts', []),
        'effective_positions': concentration_analysis.get('effective_number_of_assets', 0),
        'is_over_concentrated': concentration_analysis.get('is_concentrated', False),
        'recommendations': [
            a.get('message') for a in concentration_analysis.get('warnings', [])
        ] if 'recommendations' not in concentration_analysis else []
    }
