"""
Math Engine Module
==================
Includes:
1. GaussianPricingModel: For pairwise option pricing (Vegas vs Kalshi).
2. HodgeGraphModel: For global market consistency analysis using Discrete Hodge Theory.
"""

import numpy as np
import networkx as nx
from scipy.stats import norm
from typing import Tuple, Dict, List

# ==============================================================================
# 1. CLASSIC QUANT MODEL (GAUSSIAN)
# ==============================================================================
class GaussianPricingModel:
    """
    Standard physics-based pricing model using Normal Distribution.
    Used for direct arbitrage checks on single games.
    """
    
    MIN_SIGMA = 5.0
    MAX_SIGMA = 25.0
    DEFAULT_SIGMA = 13.5

    @staticmethod
    def american_to_prob(odds: float) -> float:
        try:
            odds = float(odds)
            if 1.0 < odds < 10.0: return (1.0 / odds) * 100.0
            if odds > 0: return (100.0 / (odds + 100.0)) * 100.0
            else: return (-odds / (-odds + 100.0)) * 100.0
        except: return 0.0

    @staticmethod
    def remove_vig(prob_fav: float, prob_dog: float) -> float:
        total = prob_fav + prob_dog
        if total == 0: return 0.0
        return (prob_fav / total) * 100.0

    @classmethod
    def solve_parameters(cls, spread: float, ml_fav: int, ml_dog: int) -> Tuple[float, float]:
        # ... (Same logic as before) ...
        p_raw_fav = cls.american_to_prob(ml_fav)
        p_raw_dog = cls.american_to_prob(ml_dog)
        true_p = cls.remove_vig(p_raw_fav, p_raw_dog) / 100.0
        
        mu = abs(spread)
        try:
            z = norm.ppf(1 - true_p)
            if abs(z) < 0.01: sigma = cls.DEFAULT_SIGMA
            else: sigma = abs(0 - mu) / abs(z)
        except: sigma = cls.DEFAULT_SIGMA
        
        if not (cls.MIN_SIGMA < sigma < cls.MAX_SIGMA): sigma = cls.DEFAULT_SIGMA
        return mu, sigma

    @staticmethod
    def calculate_fair_value(mu: float, sigma: float) -> float:
        return norm.sf((0 - mu) / sigma) * 100.0


# ==============================================================================
# 2. HODGE THEORY MODEL (THE "SECRET SAUCE")
# ==============================================================================
class HodgeGraphModel:
    """
    Implements Discrete Hodge Decomposition on the Market Graph.
    
    Theory:
    Any edge flow Y (observed spreads) can be decomposed into:
    Y = Gradient(s) + Curl(h)
    
    - Gradient(s): The "Global Potential" (True Ranking). Consistent flow.
    - Curl(h): The "Cyclic Component". Inconsistent loops (Arbitrage).
    
    If ||Curl|| is high, the market is inefficient/irrational.
    """
    
    @staticmethod
    def compute_market_inconsistency(games: List[Dict]) -> Dict:
        """
        Input: List of games [{'home': 'LAL', 'away': 'GSW', 'spread': 5.5}, ...]
        Output: Global Rankings (Gradient) and Market Inconsistency (Curl Energy)
        """
        # 1. Build the Graph
        G = nx.Graph()
        teams = set()
        
        # 'spread' is defined as Home - Away margin (Vegas expectation)
        for g in games:
            h, a, spread = g['home'], g['away'], g['spread']
            teams.add(h)
            teams.add(a)
            # Add edge with 'flow' = spread
            # If Home is favored by 5, flow from Away -> Home is +5
            G.add_edge(a, h, weight=spread)

        node_list = list(teams)
        n = len(node_list)
        if n < 2: return {"error": "Not enough data"}

        # 2. Construct Matrices
        # Index mapping
        idx = {node: i for i, node in enumerate(node_list)}
        
        # B: Divergence Vector (Net flow into each node)
        div = np.zeros(n)
        for u, v, data in G.edges(data=True):
            flow = data['weight'] # Flow u -> v
            div[idx[v]] += flow
            div[idx[u]] -= flow
            
        # L: Graph Laplacian (Unweighted for simple connectivity)
        # We perform regression on pairwise comparisons
        L = nx.laplacian_matrix(G).toarray()
        
        # 3. Hodge Decomposition (Solve L * s = div)
        # Since L is singular (sum of rows = 0), we use Pseudo-Inverse
        L_pinv = np.linalg.pinv(L)
        s = L_pinv @ div # s is the "Global Potential" (Rating) vector
        
        # 4. Calculate Residuals (Curl Component)
        # Curl_ij = Observed_ij - (s_j - s_i)
        curl_energy = 0.0
        inconsistencies = []
        
        for u, v, data in G.edges(data=True):
            observed_flow = data['weight']
            gradient_flow = s[idx[v]] - s[idx[u]] # Expected flow based on global rank
            
            residual = observed_flow - gradient_flow
            curl_energy += residual ** 2
            
            if abs(residual) > 3.0: # If discrepancy > 3 points
                inconsistencies.append({
                    "matchup": f"{u} vs {v}",
                    "vegas_spread": observed_flow,
                    "hodge_implied": gradient_flow,
                    "discrepancy": residual
                })

        # Normalize rankings
        rankings = {node_list[i]: float(s[i]) for i in range(n)}
        
        return {
            "hodge_rankings": dict(sorted(rankings.items(), key=lambda item: item[1], reverse=True)),
            "total_curl_energy": float(curl_energy), # The Arbitrage Index
            "arbitrage_loops": inconsistencies
        }