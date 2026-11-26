# GENESIS 2026: Virtual Stock Market Simulation Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2015+-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Deploy-Docker%20Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![Campus Firewall](https://img.shields.io/badge/Network-Fortinet%20Port%20443%20Hardened-green.svg)](#campus-firewall-hardening)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**GENESIS 2026** is a high-throughput, low-latency virtual stock market simulation platform developed for **VIT Bhopal University**. Designed to host **500+ simultaneous participants** with ₹25,000 starting virtual cash, the platform allows students to trade 30 fictional companies through **10 real-world macroeconomic eras** (ranging from the 2000 Dot-Com crash to the universal **YAPOO 59 Blackout Cataclysm**).

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Core Engineering Highlights](#core-engineering-highlights)
3. [Infinite Liquidity Dealer Model (AMM)](#infinite-liquidity-dealer-model-amm)
4. [The Game Economy Bounding Graph (DAG Reachability Envelope)](#the-game-economy-bounding-graph-dag-reachability-envelope)
5. [Anti-Exploit Economy Guardrails](#anti-exploit-economy-guardrails)
6. [Streamlined Peace-Time Market Engine](#streamlined-peace-time-market-engine)
7. [Collateralized Short Selling & Margin Math](#collateralized-short-selling--margin-math)
8. [The 10 Chronological Macroeconomic Eras](#the-10-chronological-macroeconomic-eras)
9. [The 30 Companies Master Catalog](#the-30-companies-master-catalog)
10. [Database Schema (PostgreSQL DDL)](#database-schema-postgresql-ddl)
11. [Campus Firewall Hardening (Fortinet Port 443 Bypass)](#campus-firewall-hardening-fortinet-port-443-bypass)
12. [REST API & WebSocket Specifications](#rest-api--websocket-specifications)
13. [Getting Started & Deployment](#getting-started--deployment)
14. [Load Testing & Concurrency Verification](#load-testing--concurrency-verification)

---

## System Architecture

```
+─────────────────────────────────────────────────────────────────────────────────────────+
|                               CAMPUS PARTICIPANT LAYER                                  |
|         [ 500+ Concurrent Student Laptops / Mobile Browsers (React 18 + Vite) ]        |
+─────────────────────────────────────────────────────────────────────────────────────────+
                                       │
                                       │ HTTPS / WSS (Strictly Port 443)
                                       ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                        FORTINET FIREWALL SHIELD & REVERSE PROXY                         |
|                   [ Cloudflare / Vercel Edge / Nginx Reverse Proxy ]                    |
|          • TLS 1.3 Termination  • Port 443 Passthrough  • 15s WebSocket Keep-Alives     |
+─────────────────────────────────────────────────────────────────────────────────────────+
                                       │
                                       │ Internal Network Routing
                                       ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                             FASTAPI APPLICATION SERVER                                  |
|  ┌─────────────────────────────────┐   ┌─────────────────────────────────────────────┐  |
|  │    Infinite Liquidity Engine    │   │      In-Memory RAM Ticker (Every 5-8s)      │  |
|  │  (Sub-15ms Atomic Order Fills)  │   │   (±0.1% to ±0.3% Jitter, Zero DB Writes)   │  |
|  ├─────────────────────────────────┤   ├─────────────────────────────────────────────┤  |
|  │    Collateral Risk Supervisor   │   │        Deterministic Macro Controller       │  |
|  │ (100% Escrow, +80% Liquidation) │   │     (scenarios_config.py 30x10 Deltas)      │  |
|  ├─────────────────────────────────┤   ├─────────────────────────────────────────────┤  |
|  │    Bounding Graph Validator     │   │         Leaderboard Freeze Switch           │  |
|  │ (35% Cap, 40-Share Cap, ₹10 Fl) │   │        (T-30m Masking / Unmasked Admin)     │  |
|  └─────────────────────────────────┘   └─────────────────────────────────────────────┘  |
+─────────────────────────────────────────────────────────────────────────────────────────+
                                       │
                                       │ Connection Pool (Supavisor / asyncpg)
                                       ▼
+─────────────────────────────────────────────────────────────────────────────────────────+
|                        DATABASE & PERSISTENCE (POSTGRESQL 15+)                          |
|    • users (2-Tier RBAC)    • wallets (Balance & Escrow)   • stocks (Anchor & Live)     |
|    • holdings (Long/Short)  • transactions (Audit Ledger)  • market_settings            |
+─────────────────────────────────────────────────────────────────────────────────────────+
```

---

## Core Engineering Highlights

- **2-Tier RBAC Only (`ADMIN` and `PARTICIPANT`):** Simplified permissions matrix. All privilege operations (account approvals, ₹5,000 top-ups, era triggers, market pause, leaderboard freeze) belong directly to the `ADMIN`.
- **Zero-Input Admin Operation:** All percentage price drops and booms across all 30 equities are hardcoded in `scenarios_config.py`. Organizers click 1 button to broadcast an era atomically.
- **Sub-15ms Trade Execution:** Orders execute immediately via single atomic PostgreSQL transactions.
- **Campus Firewall Immunity:** Guaranteed connectivity through strict Port 443 HTTPS and WSS routing.

---

## Infinite Liquidity Dealer Model (AMM)

### Why Peer-to-Peer (P2P) Order Books Fail in Competitions
In a traditional exchange (like NSE/NASDAQ), buyer orders match against seller orders. During market crashes (such as **Era 10: Yapoo 59** where tech falls $-85\%$), **no rational participant is willing to buy**. In an order book, sell orders get stuck permanently in an `UNFILLED / PENDING` queue. The platform grinds to a halt, students panic, and organizers face game-breaking complaints.

### The Solution: The Platform as Dealer
In GENESIS 2026, the platform operates as an **Automated Market Maker (AMM)**:
- **Instant Fills:** The exchange is the direct counterparty to every transaction.
- **Zero Waiting Queues:** Order state transitions immediately from `SUBMITTED` $\rightarrow$ `FILLED` in $<15\text{ms}$.
- **No Partial Fills:** If a student requests 20 shares, they receive 20 shares in one shot.
- **Guaranteed Exit:** A participant holding falling assets can dump them instantly at the current tick price.

### Rejection Conditions
Orders are never rejected for liquidity reasons. They can only be rejected if they violate risk guardrails:
1. `Free_Cash < Order_Value` (Insufficient cash balance).
2. `Free_Cash < Collateral_Required` (Insufficient cash for 100% short margin).
3. `Post_Trade_Concentration > 35%` (Exceeds single-stock limit).
4. `Post_Trade_Quantity > 40` (Exceeds position share cap).
5. `is_market_open == False` (Admin paused trading).

---

## The Game Economy Bounding Graph (DAG Reachability Envelope)

### 1. The Combinatorial Explosion Problem
In a market with 30 stocks, 10 sequential rounds, and ~500 participants executing arbitrary trade combinations, the number of possible portfolio trajectories exceeds:
$$\text{Total State Space} = 30^{500}$$
Simulating every player using brute force or LLM agents is mathematically impossible. Without boundaries, two severe exploits emerge:
- **Runaway Hyperinflation:** A player shorting aggressive tech before a crash could snowball from ₹25,000 to ₹10 Crore, ruining competitive balance.
- **Market Cornering:** A high-roller could purchase thousands of shares of cheap companies like KSTL (₹145) and monopolize supply.

### 2. The Directed Acyclic Graph (DAG) Solution
Rather than predicting every participant's action, the platform computes a **Min-Max Reachability Envelope** along the chronological era graph nodes:

```
                                  SCENARIO BOUNDING GRAPH (DAG)
                                  
    [Round 0: Base]  ───>  [Era 1: Dot-Com]  ───>  [Era 2: Capex]  ───>  [Era 10: Yapoo 59]
         ₹25,000                ₹41,250                 ₹63,937               ₹30,99,468  <-- UPPER BOUND (Oracle Trader)
            │                      │                       │                       │
         ₹25,000  ───────────── ₹20,500 ─────────────── ₹24,190 ────────────── ₹18,044    <-- BENCHMARK (Passive Buy & Hold)
            │                      │                       │                       │
         ₹25,000                ₹8,750                  ₹9,187                  ₹50.00    <-- LOWER BOUND (Worst Drawdown)
```

### 3. Mathematical Recursive Formulations

#### Upper Bound ($V_{\max}$ — The Oracle Trader)
The theoretical maximum net worth achieved by a hypothetical omniscient player who allocates 100% of capital into either the top-performing long asset or the deepest-falling short asset at every single era:
$$V_{\max}(t) = V_{\max}(t-1) \times \left(1 + \max\left(\max_{i \in \text{Stocks}} (\Delta_{i,t}), \max_{j \in \text{Stocks}} (|\Delta_{j,t}| \cdot \mathbb{I}_{\Delta_{j,t} < 0})\right)\right)$$

#### Market Index Benchmark ($V_{\text{index}}$ — Passive Strategy)
The performance of an equal-weighted buy-and-hold portfolio across all 30 equities:
$$V_{\text{index}}(t) = V_{\text{index}}(t-1) \times \left(1 + \frac{1}{30}\sum_{k=1}^{30}\Delta_{k,t}\right)$$

#### Lower Bound ($V_{\min}$ — Worst Drawdown Floor)
The worst-case capital loss of an unhedged player who holds 100% of their net worth in the worst-performing stock of each era:
$$V_{\min}(t) = \max\left(₹50.00, V_{\min}(t-1) \times \left(1 + \min_{i \in \text{Stocks}} (\Delta_{i,t})\right)\right)$$

### 4. 10-Era Envelope Matrix (Starting Capital: ₹25,000)

| Timeline Step | Oracle Upper Bound ($V_{\max}$) | Index Benchmark ($V_{\text{index}}$) | Worst Drawdown ($V_{\min}$) | Strategic Milestone |
| :--- | :--- | :--- | :--- | :--- |
| **Round 0: Base** | ₹25,000.00 | ₹25,000.00 | ₹25,000.00 | Baseline wallet allocation |
| **Era 1: Dot-Com** | ₹41,250.00 (+65%) | ₹20,500.00 (-18%) | ₹8,750.00 (-65%) | Shorting TMND/PAYB yields top alpha |
| **Era 2: Capex** | ₹63,937.00 (+155%) | ₹24,190.00 (+18%) | ₹9,187.00 (-63%) | Long KSTL (+55%) & SETU (+48%) |
| **Era 3: GFC 2008** | ₹1,07,414.00 (+329%) | ₹18,868.00 (-22%) | ₹2,940.00 (-88%) | Shorting VNTR (-68%) & SKYL (-58%) |
| **Era 4: QE Stimulus** | ₹1,48,231.00 (+492%) | ₹22,641.00 (+20%) | ₹3,175.00 (-87%) | Long CPBK (+38%) & GATI (+35%) |
| **Era 5: Crude Crash** | ₹2,14,935.00 (+759%) | ₹23,320.00 (+3%) | ₹1,746.00 (-93%) | Long GARU (+42%); Short PIHC (-45%) |
| **Era 6: Digital & EV** | ₹3,54,643.00 (+1,318%) | ₹26,818.00 (+15%) | ₹1,728.00 (-93%) | Long VRID (+65%) & PAYB (+55%) |
| **Era 7: COVID-19** | ₹5,95,799.00 (+2,283%) | ₹25,745.00 (-4%) | ₹656.00 (-97%) | Long GVAX (+68%); Short GARU (-62%) |
| **Era 8: Supply Bottlenecks**| ₹9,05,615.00 (+3,522%) | ₹29,606.00 (+15%) | ₹590.00 (-97%) | Long BCHIP (+52%) & KSTL (+44%) |
| **Era 9: AI Supercycle**| ₹16,75,388.00 (+6,601%) | ₹34,047.00 (+15%) | ₹507.00 (-98%) | Long TMND (+85%) & BCHIP (+48%) |
| **Era 10: YAPOO 59**| **₹30,99,468.00 (+12,297%)** | **₹18,044.00 (-47%)** | **₹50.00 (-99.8%)** | Universal crash; Shorting tech dominates |

---

## Anti-Exploit Economy Guardrails

To prevent market breaking behaviors, the backend enforces 4 hard constraints in Python:

1. **Single-Stock 35% Concentration Cap:**
   $$\text{Holding\_Value}(S_i) \le 0.35 \times \text{Total\_Portfolio\_Value}$$
   *Guarantee:* Forces participants to diversify across at least 3 distinct stocks. No all-in gambling.
2. **Maximum 40 Shares Cap per User:**
   $$\text{Quantity}(S_i) \le 40\text{ shares}$$
   *Guarantee:* Stops participants from buying thousands of shares of cheap companies (e.g. KSTL at ₹145).
3. **Absolute ₹10.00 Price Floor:**
   $$P_{\text{new}} = \max(₹10.00, P_{\text{calculated}})$$
   *Guarantee:* Prevents division-by-zero errors in P/E ratios and eliminates penny-stock glitching.
4. **100% Cash Collateral Reservation for Short Selling:**
   $$\text{Collateral}_{\text{locked}} = 1.0 \times (Q \times P_{\text{entry}})$$
   *Guarantee:* Ensures zero naked shorting. Negative wallet balances are mathematically impossible.

---

## Streamlined Peace-Time Market Engine

Between major era announcements (which occur every 15–25 minutes), stock charts must not freeze. The engine generates organic market ticks while **avoiding continuous database writes**:

```
+─────────────────────────────────────────────────────────────────────────────────────────+
|               STREAMLINED IN-MEMORY TICK ENGINE (FAIL-SAFE ARCHITECTURE)                |
+─────────────────────────────────────────────────────────────────────────────────────────+
|  1. Fast In-Memory RAM Jitter (Every 5–8 seconds):                                      |
|     ΔP = Current_Price * [ σ_stock * Normal_Random(0, 1) - 0.15 * (P_t - P_anchor) ]    |
|     • σ = 0.3% for High-Beta Tech (TMND, VRID, PAYB)                                    |
|     • σ = 0.1% for Defensive Staples (PLFE, DAIRY, SANJ)                               |
|                                                                                         |
|  2. ZERO Continuous PostgreSQL Writes:                                                  |
|     Prices are maintained in FastAPI RAM / Redis state. PostgreSQL is updated ONLY on   |
|     Era triggers and actual trade executions. Eliminates 99% of background DB load.    |
|                                                                                         |
|  3. Decoupled Architecture & Graceful Degradation:                                      |
|     The tick engine is decoupled from the order matching engine. If the background     |
|     worker encounters an error, prices freeze at current levels—the platform stays      |
|     online and trades continue executing smoothly.                                      |
|                                                                                         |
|  4. Admin Kill-Switch in Dashboard:                                                     |
|     Admin can click [TOGGLE TICKS] to pause background broadcasts instantly if campus   |
|     network bandwidth spikes.                                                           |
+─────────────────────────────────────────────────────────────────────────────────────────+
```

---

## Collateralized Short Selling & Margin Math

### Core Accounting Equations

1. **Long Position Value ($V_{\text{long}}$):**
   $$V_{\text{long}} = \sum_{i=1}^N \left(Q_{\text{long}, i} \times P_{\text{current}, i}\right)$$

2. **Short Position Liability ($L_{\text{short}}$):**
   $$L_{\text{short}} = \sum_{j=1}^M \left(Q_{\text{short}, j} \times P_{\text{current}, j}\right)$$

3. **Total Portfolio Net Worth:**
   $$\text{Net Worth} = \text{Cash Balance} + V_{\text{long}} + \text{Collateral}_{\text{locked}} - L_{\text{short}}$$

4. **Realized Short P&L on Cover:**
   $$\text{Realized P\&L} = Q_{\text{cover}} \times \left(P_{\text{entry}} - P_{\text{cover}}\right)$$

5. **Short Squeeze Circuit Breaker (+80% Forced Cover):**
   $$\text{If } P_{\text{current}} \ge 1.80 \times P_{\text{entry}} \implies \text{Forced Buy-to-Cover at Market}$$

---

## The 10 Chronological Macroeconomic Eras

All stock price deltas are fixed in `scenarios_config.py` and executed atomically:

```python
# scenarios_config.py snippet
SCENARIOS_MAP = {
    "ERA_1_DOT_COM": {
        "name": "The Silicon Vapor Implosion",
        "description": "Tech multiples crash as vaporware revenue is uncovered; FMCG safe-haven rotation.",
        "deltas": {
            "TMND": -0.65, "PAYB": -0.62, "OMNA": -0.55, "VRID": -0.48, "BCHIP": -0.45,
            "KVACH": -0.40, "STMW": -0.38, "VNTR": -0.42, "APEX": -0.22, "SKYL": -0.20,
            "GATI": -0.18, "GARU": -0.16, "SETU": -0.15, "KSTL": -0.14, "PLFE": -0.06,
            "DAIRY": -0.05, "SANJ": -0.04, "URJA": -0.06, "RVB": -0.10, "TRSH": -0.04
        }
    },
    "ERA_10_YAPOO_59": {
        "name": "YAPOO 59 – The Blackout Protocol",
        "description": "UNIVERSAL DEADLY APOCALYPSE: Solar EMP and cyber-biological strike collapse all rails.",
        "deltas": {
            "TMND": -0.85, "PAYB": -0.80, "VRID": -0.78, "OMNA": -0.75, "STMW": -0.72,
            "KVACH": -0.70, "VNTR": -0.68, "HSUN": -0.68, "GARU": -0.65, "BCHIP": -0.65,
            "SKYL": -0.62, "QDRP": -0.60, "GATI": -0.52, "APEX": -0.48, "SETU": -0.48,
            "PLFE": -0.24, "DAIRY": -0.22, "SANJ": -0.25, "TRSH": -0.18, "RVB": -0.18
        }
    }
}
```

---

## The 30 Companies Master Catalog

| # | Ticker | Company Name | Sector | Base Price (₹) | P/E Ratio | Valuation Profile |
| :- | :--- | :--- | :--- | :- | :- | :--- |
| 1 | **OMNA** | Omnia Cloud Systems | Cloud Infrastructure | ₹320.00 | 68.0x | Speculative Growth |
| 2 | **TMND** | TuringMind AI | AI Compute / LLM | ₹180.00 | 115.0x | Extreme Bubble Multiples |
| 3 | **KVACH** | CyberKavach Infosec | Cybersecurity Defense | ₹420.00 | 54.0x | Premium Tech Growth |
| 4 | **VIST** | Vistara Tech Solutions | IT Services & BPO | ₹850.00 | 24.5x | Cash-Flow Mature IT |
| 5 | **BCHIP** | Bharat Chip Foundry | Semiconductor Fab | ₹380.00 | 46.0x | Strategic Capital Capex |
| 6 | **APEX** | Apex Capital & Trust | Investment Banking | ₹540.00 | 18.2x | High-Beta Financial |
| 7 | **RVB** | Rashtriya Vikas Bank | Public Sector Bank | ₹65.00 | 6.8x | Deep Value / Sovereign |
| 8 | **CPBK** | Credence Private Bank | Commercial Private Bank| ₹720.00 | 19.5x | High-Quality Credit Book |
| 9 | **VNTR** | VentureLeap Finance | Startup & Venture Debt | ₹190.00 | 38.0x | High-Risk Speculative Lending |
| 10| **PAYB** | PayBharat Digital | Payments & FinTech | ₹95.00 | Unprofitable | Pure Multiples Speculation |
| 11| **PLFE** | PureLife Consumer | FMCG Personal Care | ₹450.00 | 48.0x | Defensive Quality Staple |
| 12| **DAIRY**| DailyDairy Agro | FMCG Dairy & Food | ₹180.00 | 36.0x | Non-Discretionary Food |
| 13| **RBEV** | Royal Beverages Co. | Discretionary Liquor | ₹820.00 | 34.0x | Urban Consumption |
| 14| **SANJ** | Sanjeevani Life Sciences| Pharma Generics | ₹640.00 | 27.0x | Inelastic Healthcare |
| 15| **GVAX** | GeneVax Therapeutics | Biotech & Vaccines | ₹290.00 | 42.0x | Binary Clinical Risk |
| 16| **MCRH** | MediCare Hospitals | Hospital Chains | ₹980.00 | 39.0x | Resilient Service Provider |
| 17| **URJA** | Global Urja Power | Thermal & Grid Utility | ₹110.00 | 11.0x | Regulated Utility Asset |
| 18| **PIHC** | PetroInd Hydrocarbons | Oil Refining & Petrochem| ₹340.00 | 9.5x | Commodity Cyclical |
| 19| **HSUN** | HelioSun Green Energy | Solar & Wind Utility | ₹160.00 | 62.0x | Capital-Intensive CleanTech |
| 20| **VRID** | VoltRide Mobility | EV 2W/4W Mobility | ₹75.00 | 88.0x | High-Beta Disruptor |
| 21| **GATI** | Gati Motors Ltd. | Commercial & Passenger | ₹480.00 | 16.0x | Rate-Sensitive OEM |
| 22| **GARU** | Garuda Airlines | Domestic Aviation | ₹210.00 | 28.0x | Fuel & FX Sensitive |
| 23| **SETU** | Setu Infrastructure | Roads & Civil EPC | ₹310.00 | 14.5x | Sovereign Order Book |
| 24| **SKYL** | Skylark Urban Realty | Real Estate Development| ₹280.00 | 31.0x | Highly Leveraged Cyclical |
| 25| **KSTL** | Kalinga Steel & Iron | Primary Steel Mills | ₹145.00 | 7.8x | Global Industrial Beta |
| 26| **BCTC** | Bharat Connect Telecom | 5G Network Carrier | ₹260.00 | 29.0x | Sticky Subscription ARPU |
| 27| **STMW** | StreamWave Entertainment| OTT Streaming & Gaming | ₹195.00 | 44.0x | Digital Attention Metric |
| 28| **QDRP** | QuickDrop Logistics | E-Commerce Express Cargo| ₹230.00 | 33.0x | Consumer Freight Volume |
| 29| **BZAR** | BazaarDirect Retail | Hypermarket Chains | ₹680.00 | 35.0x | Physical Footfall Retail |
| 30| **TRSH** | Trishul Defense Systems| Defense Electronics | ₹520.00 | 32.0x | Sovereign Military Moat |

---

## Database Schema (PostgreSQL DDL)

```sql
-- schema.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table (Strict 2-Tier RBAC)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    registration_no VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN', 'PARTICIPANT')),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Wallets Table
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE NOT NULL,
    cash_balance NUMERIC(14, 2) NOT NULL DEFAULT 25000.00 CHECK (cash_balance >= 0.00),
    collateral_locked NUMERIC(14, 2) NOT NULL DEFAULT 0.00 CHECK (collateral_locked >= 0.00),
    total_credited NUMERIC(14, 2) NOT NULL DEFAULT 25000.00,
    topup_count INT NOT NULL DEFAULT 0 CHECK (topup_count <= 1),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Stocks Table
CREATE TABLE stocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(150) NOT NULL,
    sector VARCHAR(50) NOT NULL,
    current_price NUMERIC(12, 2) NOT NULL CHECK (current_price >= 10.00),
    anchor_price NUMERIC(12, 2) NOT NULL CHECK (anchor_price >= 10.00),
    pe_ratio NUMERIC(6, 2) NOT NULL,
    max_shares_per_user INT NOT NULL DEFAULT 40,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Holdings Table
CREATE TABLE holdings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    stock_id UUID REFERENCES stocks(id) ON DELETE RESTRICT NOT NULL,
    position_type VARCHAR(10) NOT NULL CHECK (position_type IN ('LONG', 'SHORT')),
    quantity INT NOT NULL CHECK (quantity > 0),
    avg_entry_price NUMERIC(12, 2) NOT NULL,
    UNIQUE(user_id, stock_id, position_type)
);

-- 5. Transactions Ledger
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    stock_id UUID REFERENCES stocks(id) ON DELETE RESTRICT NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL', 'SHORT', 'COVER')),
    quantity INT NOT NULL CHECK (quantity > 0),
    execution_price NUMERIC(12, 2) NOT NULL,
    total_amount NUMERIC(14, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Market Settings Table
CREATE TABLE market_settings (
    id INT PRIMARY KEY DEFAULT 1,
    is_market_open BOOLEAN DEFAULT FALSE,
    is_leaderboard_frozen BOOLEAN DEFAULT FALSE,
    ticks_enabled BOOLEAN DEFAULT TRUE,
    max_concentration_pct NUMERIC(5, 2) DEFAULT 35.00,
    active_scenario_name VARCHAR(150) DEFAULT 'Normal Trading'
);
```

---

## Campus Firewall Hardening (Fortinet Port 443 Bypass)

Empirical network diagnostic verification conducted on campus Wi-Fi:

```
Target                               TcpTestSucceeded
------                               ----------------
db.bit.io:5432 (Postgres DB Port)               False  ❌ (BLOCKED BY FORTINET)
httpbin.org:8080 (Custom Web Port)              False  ❌ (BLOCKED BY FORTINET)
vercel.com:443 (Standard HTTPS Port)             True  ✅ (ALLOWED BY FORTINET)
```

### Golden Deployment Rules
1. **Never expose Port 5432 to participants:** All client communication goes to the FastAPI application layer. The database lives on an isolated private cloud VPC or local Docker network.
2. **Never serve on custom ports (`:8000`, `:8080`):** Run FastAPI behind an Nginx or Cloudflare reverse proxy bound to **Port 443** with a valid SSL/TLS certificate.
3. **Use WSS on Port 443 with 15s Heartbeats:** Long-lived idle WebSockets are terminated by Deep Packet Inspection (DPI) after 30 seconds. The frontend maintains an automated `ping`/`pong` heartbeat every 15 seconds.

---

## REST API & WebSocket Specifications

### REST Endpoints
| Endpoint | Method | Role | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/auth/register` | `POST` | Public | Register student with Registration No and Email (`status=PENDING`). |
| `/api/v1/auth/login` | `POST` | Public | Authenticate user; returns JWT token with `role` claim. |
| `/api/v1/trade/order` | `POST` | Participant | Executes instant trade (`BUY`, `SELL`, `SHORT`, `COVER`). |
| `/api/v1/portfolio/me` | `GET` | Participant | Returns cash, collateral, holdings, unrealized P&L, net worth. |
| `/api/v1/leaderboard` | `GET` | All Roles | Returns rankings. If frozen and user is Participant, serves cached snapshot. |
| `/api/v1/admin/scenario/trigger` | `POST` | Admin | Atomic trigger of an era; updates all 30 stock prices in sub-50ms. |
| `/api/v1/admin/market/pause` | `PATCH`| Admin | Toggles market trading between OPEN and PAUSED. |
| `/api/v1/admin/ticks/toggle` | `PATCH`| Admin | Emergency killswitch for in-memory price jitter. |
| `/api/v1/admin/leaderboard/freeze`| `POST`| Admin | Toggles final 30-minute leaderboard lock. |

### WebSocket Protocol (`wss://api.domain.com/ws/market`)
Clients receive real-time JSON events on Port 443:
```json
{
  "event": "PRICE_TICK",
  "data": [
    {"symbol": "TMND", "price": 185.20, "change_pct": 2.89},
    {"symbol": "PLFE", "price": 448.50, "change_pct": -0.33}
  ]
}
```

---

## Getting Started & Deployment

### 1. Prerequisites
- Docker Engine 24.0+ & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)

### 2. Environment Configuration (`.env`)
```ini
ENVIRONMENT=production
PORT=443
DATABASE_URL=postgresql+asyncpg://postgres:securepassword@db:5432/genesis_db
SECRET_KEY=supersecretjwtkeyforgenesis2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

### 3. Launch via Docker Compose
```bash
# Clone the repository
git clone https://github.com/your-username/genesis-2026.git
cd genesis-2026

# Launch backend, database, and reverse proxy
docker compose up -d --build
```

---

## Load Testing & Concurrency Verification

Run Locust to verify 500 concurrent participants placing burst orders:

```bash
# Run headless load test
locust -f tests/load_test.py --headless -u 500 -r 50 --run-time 10m --host https://api.yourdomain.com
```

**Acceptance Criteria:**
- 99th percentile response latency $< 100\text{ms}$ at 150 requests/sec.
- Zero `500 Internal Server Errors`.
- Sub-50ms execution time on `[TRIGGER ERA]` across all 30 equities simultaneously.

---

## Document Specifications & Official Artifact
- **Compiled PDF Specification:** [GENESIS_2026_Virtual_Stock_Market_Simulation_PRD.pdf](GENESIS_2026_Virtual_Stock_Market_Simulation_PRD.pdf)
- **Host Institution:** VIT Bhopal University
- **Event:** GENESIS 2026 Virtual Stock Exchange
- **Author:** Event Technical Architecture Core
