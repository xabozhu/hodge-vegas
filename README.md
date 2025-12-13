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

This engine leverages two distinct mathematical models to identify pricing inefficiencies:

### 1. The Gaussian Physics Model (Local Pricing)
Used for single-game arbitrage. We model the score differential ($X$) as:
$$X \sim \mathcal{N}(\mu, \sigma^2)$$
Parameters ($\mu, \sigma$) are derived by back-solving the Z-scores from Vegas Moneyline and Spread data.

### 2. Discrete Hodge Decomposition (Global Consistency)
Used to identify **Cyclic Arbitrage** and structural market inefficiencies.

By representing the market as a graph where teams are nodes and spreads are edge flows ($Y_{ij}$), we apply **Discrete Hodge Theory** to decompose the observed betting flow:

$$Y = Y_{gradient} + Y_{curl}$$

* **$Y_{gradient}$ (Gradient Flow):** The "Global Potential" (True Strength). This represents the consistent ranking component $s$, such that $Y_{ij} \approx s_j - s_i$.
* **$Y_{curl}$ (Curl Flow):** The "Cyclic Component" (Inconsistency).
    $$\text{Curl} = Y - \text{grad}(s)$$

**The Strategy:**
When the **$L^2$-norm of the Curl component** ($||Y_{curl}||^2$) spikes, it indicates that the betting market contains internal contradictions (e.g., $A > B > C > A$). The engine flags these regimes as "High Volatility/High Opportunity" states, triggering more aggressive taker execution.

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