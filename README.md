# Hodge-Vegas: Statistical Arbitrage & Liquidity Engine 🏛️ 🎲

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Status](https://img.shields.io/badge/Status-Production_Ready-green.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)
![Kalshi](https://img.shields.io/badge/Grant-Kalshi_Developer_Program-purple.svg)

## 📖 Executive Summary

**Hodge-Vegas** is a quantitative trading system designed to bridge the efficiency gap between mature sportsbooks (e.g., DraftKings, Vegas) and the emerging prediction market ecosystem (Kalshi).

By treating highly liquid sportsbook odds as the "ground truth," this engine utilizes a **Gaussian Physics Model** to derive the implied fair value of binary contracts. It then autonomously acts as a **Market Maker** or **Liquidity Taker** on Kalshi to enforce pricing efficiency and capture statistical arbitrage opportunities.

> **Note:** This project was developed as a proposal for the **Kalshi Developer Grant**, aiming to solve liquidity fragmentation and pricing latency in long-tail prediction markets.

---

## 💡 The Core Problem & Solution

### The Problem: Pricing Inefficiency
Prediction markets like Kalshi often suffer from **retail sentiment bias** and **low liquidity**, especially in non-headline events (e.g., regular season NBA games). This results in:
1.  **Wide Bid-Ask Spreads:** Making entry/exit costly.
2.  **Pricing Latency:** Prices fail to react instantly to real-world game developments compared to liquid sportsbooks.

### The Solution: Cross-Market Arbitrage
Hodge-Vegas acts as an **Oracle Bridge**:
1.  **Ingest:** Real-time odds (Moneyline & Point Spreads) from Vegas bookmakers.
2.  **Transform:** Convert these traditional odds into a **Binary Probability Density Function (PDF)**.
3.  **Execute:** algorithmic trading on Kalshi to align the binary price with the true mathematical probability.

---

## 🧮 Mathematical Framework

The core innovation of this engine is the translation of **Point Spreads** into **Binary Fair Values**.

Moneyline odds alone are insufficient as they only provide direction. **Point Spreads** provide the **Volatility ($\sigma$)** of the matchup, which is critical for accurate pricing.

### 1. The Gaussian Assumption
We model the score differential ($X$) between two teams as a Normal Distribution:
$$X \sim \mathcal{N}(\mu, \sigma^2)$$

### 2. Parameter Derivation
The engine solves for $\mu$ and $\sigma$ using the following logic:
* **Mean ($\mu$):** Derived from the absolute Point Spread ($S$).
    $$\mu = |S|$$
* **Volatility ($\sigma$):** Derived by back-solving the Z-score from the Moneyline Implied Probability ($P_{implied}$).
    $$\sigma = \frac{S}{\Phi^{-1}(1 - P_{implied})}$$
    *(Where $\Phi^{-1}$ is the quantile function of the standard normal distribution)*

### 3. Fair Value Calculation
The price of a Kalshi "Win" contract ($P_{binary}$) is the probability of the score differential being greater than zero (Survival Function):
$$P_{binary} = 1 - \Phi\left(\frac{0 - \mu}{\sigma}\right)$$

---

## 🏗️ System Architecture

```mermaid
graph TD
    A[Data Source: The Odds API] -->|JSON: Spreads & ML| B(Math Engine);
    B -->|Calculate Mu & Sigma| C{Opportunity Scanner};
    D[Data Source: Kalshi v2 API] -->|JSON: Order Book| C;
    C -->|Compare FV vs. Market Price| E[Strategy Engine];
    E -->|Edge > 3%| F[Taker Execution];
    E -->|Edge < 3%| G[Maker Liquidity Provision];
    F --> H[Kalshi Exchange];
    G --> H;