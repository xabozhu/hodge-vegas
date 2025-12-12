"""
Math Engine Module
==================

This module handles the statistical modeling of sports outcomes.
It assumes that the score differential between two teams follows a 
Normal (Gaussian) Distribution: X ~ N(mu, sigma^2).

Responsibilities:
1. Converting betting odds (American/Decimal) into implied probabilities.
2. Removing bookmaker margin ("vig") to derive true probabilities.
3. Solving for implied volatility (sigma) based on point spreads.
4. Calculating Fair Value probabilities for binary contracts.
"""

import numpy as np
from scipy.stats import norm
from typing import Tuple

class GaussianPricingModel:
    """
    A physics-based pricing model for binary prediction markets based on 
    continuous spread data.
    """
    
    # Physics Constraints for NBA (Based on historical distribution)
    # Prevents model explosion on outliers or sparse data.
    MIN_SIGMA = 5.0
    MAX_SIGMA = 25.0
    DEFAULT_SIGMA = 13.5

    @staticmethod
    def american_to_prob(odds: float) -> float:
        """
        Converts American Odds to Implied Probability (0.0 to 100.0).
        
        Args:
            odds (float): American odds (e.g., -110, +150)
            
        Returns:
            float: Implied probability percentage.
        """
        try:
            odds = float(odds)
            # Handle Decimal Odds (rare but possible)
            if 1.0 < odds < 10.0: 
                return (1.0 / odds) * 100.0
            
            # Handle American Odds
            if odds > 0: 
                return (100.0 / (odds + 100.0)) * 100.0
            else: 
                return (-odds / (-odds + 100.0)) * 100.0
        except ZeroDivisionError:
            return 0.0

    @staticmethod
    def remove_vig(prob_fav: float, prob_dog: float) -> float:
        """
        Normalizes probabilities to remove the bookmaker's margin (vigorish).
        Ensures probabilities sum to 100% to get the 'True Probability'.
        """
        total_implied = prob_fav + prob_dog
        if total_implied == 0:
            return 0.0
        return (prob_fav / total_implied) * 100.0

    @classmethod
    def solve_parameters(cls, spread_points: float, ml_fav_odds: int, ml_dog_odds: int) -> Tuple[float, float]:
        """
        Derives Gaussian parameters (Mu, Sigma) from Spread and Moneyline.
        
        Logic:
        1. Mu (Mean) = Absolute value of the Point Spread.
        2. Sigma (Volatility) = Derived by back-solving the Z-score from 
           the Moneyline probability.
           
        Returns:
            Tuple[float, float]: (Mu, Sigma)
        """
        # 1. Get Implied Probabilities
        p_fav_raw = cls.american_to_prob(ml_fav_odds)
        p_dog_raw = cls.american_to_prob(ml_dog_odds)
        
        # 2. Remove Vig to get True Probability
        true_p_fav = cls.remove_vig(p_fav_raw, p_dog_raw) / 100.0
        
        # 3. Define Mu (Mean expected score differential)
        mu = abs(spread_points)
        
        # 4. Solve for Sigma (Implied Volatility)
        # Z = (X - Mu) / Sigma  => Sigma = (X - Mu) / Z
        try:
            z_score = norm.ppf(1 - true_p_fav)
            
            # Avoid division by zero for 50/50 games
            if abs(z_score) < 0.01:
                sigma = cls.DEFAULT_SIGMA
            else:
                sigma = abs(0 - mu) / abs(z_score)
        except Exception:
            sigma = cls.DEFAULT_SIGMA

        # 5. Volatility Clamping
        if not (cls.MIN_SIGMA < sigma < cls.MAX_SIGMA):
            sigma = cls.DEFAULT_SIGMA
            
        return mu, sigma

    @staticmethod
    def calculate_fair_value(mu: float, sigma: float, threshold: float = 0.0) -> float:
        """
        Calculates the probability of the score differential exceeding a threshold.
        Uses the Survival Function (1 - CDF).
        """
        return norm.sf((threshold - mu) / sigma) * 100.0