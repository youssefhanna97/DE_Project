# MVP Roadmap — 90-Day Build Plan

## Month 1 — Data Foundation & Trust

**Goal:**  
> *“I trust my data more than Yahoo Finance.”*

---

### Week 1–2: Market Data Backbone

#### Build
- Daily OHLCV for equities
- Corporate actions (splits, dividends)

#### Deliverables
- `raw_prices` table
- `stg_prices` (dbt model)
- `fct_prices_daily`

#### Data Quality Metrics
- % missing data
- Stale tickers
- Bad corporate action detection

🔑 **Rule:** No analytics until prices are rock solid.

---

### Week 3: Returns & Basic Risk

#### Build
- Log returns
- Rolling volatility
- Drawdown series

#### dbt Models
- `fct_returns`
- `fct_volatility`
- `fct_drawdowns`

#### Python
- Sanity checks
- Visual validation

At this point, you should already be able to answer:

> *“Which assets are riskier right now?”*

---

### Week 4: Fundamentals Ingestion

#### Build
- Income statement
- Balance sheet
- Cash flow

#### Transform
- TTM calculations
- Growth rates

#### Models
- `fct_fundamentals_ttm`

---

### End of Month 1 — State Check

- ✅ Clean prices  
- ✅ Returns  
- ✅ Fundamentals  
- ❌ No strategy yet (**this is good**)

---

## Month 2 — Intelligence & Decision Logic

**Goal:**  
> *“I can generate defensible investment signals.”*

---

### Week 5: Valuation Engine (Core Differentiator)

#### Implement
- Relative valuation by sector
- Historical percentile ranks
- Simple DCF

#### Output
- `mart_valuation`

#### Key Fields
- `fair_value`
- `upside`
- `valuation_score`
- `confidence`

This becomes your **primary signal generator**.

---

### Week 6: Risk Model

#### Implement
- Rolling covariance matrix
- Correlation regimes
- Volatility targeting

#### Outputs
- `mart_risk_inputs`

You should now be able to say:

> *“This asset is cheap, but it will blow up my risk.”*

That’s professional-grade thinking.

---
## Week 7: Portfolio Construction
- Implement **Mean-Variance Optimization**
- Implement **Risk Parity**
- Hard constraints via constraints file:
  - `max_weight: 0.10`
  - `max_sector: 0.25`
  - `target_vol: 0.12`
- Output: `proposed_weights`
- No trading yet — **paper portfolios only**

---

## Week 8: Backtesting Framework
- Build **walk-forward backtests**
- Rebalancing logic
- Transaction cost model

### Deliverables
- Sharpe ratio
- Max drawdown
- Turnover
- Hit rate

> If results are weak → **fix the strategy, not the code**

---

## Month 3 — Production Mindset
**Goal:** *“I can explain, monitor, and improve decisions.”*

---

## Week 9: Orchestration
- Airflow DAGs
- Daily prices → dbt → risk
- Weekly fundamentals → valuation
- Monthly rebalance simulation
- Nothing manual anymore

---

## Week 10: Monitoring & Alerts
- Elastic valuation signals
- Rebalance decisions
- Risk breaches

### Alerts
- Volatility spike
- Drawdown threshold
- Factor drift

> This is how you avoid emotional decisions.

---

## Week 11: Dashboards & Storytelling
- Kibana dashboards:
  - Portfolio overview
  - Risk vs return
  - Valuation heatmap
  - Decision timeline

You should be able to answer:  
**“Why do we own this today?”**

---

## Week 12: Strategy Versioning
- Create:
  - `strategies/value_equity_v1`
  - `strategies/value_equity_v2`
- Track:
  - Parameters
  - Datasets
  - Results

Now you can compare ideas **scientifically**.

---

## What Your MVP Can Already Do
After 90 days, your system can:
- Ingest & clean institutional-grade data
- Generate valuation-driven signals
- Construct risk-aware portfolios
- Backtest without hindsight bias
- Explain every decision
- Scale to more strategies

> That’s already **fund-level infrastructure**.

---

## Strategic Advice (Entrepreneur Hat On)

### Resist
- Overfitting
- Fancy ML too early
- Intraday noise

### Focus On
- Data integrity
- Explainability
- Repeatability

**Capital compounds faster when confidence compounds.**






# Turning Your System into a Multi-Asset Platform

## Core Idea
**Assets differ in behavior, not in plumbing.**  
We keep one backbone and swap asset-specific logic at the edges.

---

## 1. Multi-Asset Design Principles (Non-Negotiable)

### 1.1 One Return Framework, Many Assets
Everything must map to:
- Prices
- Returns
- Risk
- Carry / income
- Liquidity

If an asset can’t express these, it doesn’t belong *(yet)*.

---

### 1.2 Asset-Agnostic Portfolio Layer
Portfolio construction must not care whether something is:
- A stock  
- An ETF  
- A bond  
- A future  

It only sees:
- `expected_return`
- `risk`
- `correlation`
- `constraints`

---

### 1.3 Asset-Specific Intelligence, Shared Execution
Valuation models differ, but:
- Optimization  
- Risk control  
- Rebalancing  

are shared.

---

## 2. Asset Universe (MVP Scope)

Start with **four buckets** that cover ~90% of macro behavior:

| Asset Class     | Instruments                          |
|-----------------|--------------------------------------|
| Equities        | Stocks, Equity ETFs                  |
| Fixed Income    | Bond ETFs, Rates futures             |
| Commodities     | Futures, Commodity ETFs              |
| FX              | Major currency pairs                 |

> Crypto can wait — same math, worse noise.

---

## 3. Unified Data Model (This Is the Key)

### 3.1 Core Dimensions (Shared)
- `dim_asset`
- `dim_asset_class`
- `dim_currency`
- `dim_exchange`

#### Example: `dim_asset`
- `asset_id`
- `symbol`
- `asset_class`
- `currency`
- `liquidity_score`
- `contract_size`
- `tick_value`

Everything else joins to this.

---

### 3.2 Fact Tables (Shared)
- `fct_prices`
- `fct_returns`
- `fct_volatility`
- `fct_carry`
- `fct_drawdowns`

> Even bonds and FX must produce returns.

---

## 4. Asset-Specific Ingestion & Modeling

### 4.1 Equities (Already Done)
**Data**
- Prices
- Fundamentals
- Dividends
- Buybacks *(optional)*

**Valuation**
- Multiples
- DCF
- Quality metrics

---

### 4.2 Fixed Income (The Tricky One)

**Instruments**
- Treasury ETFs (TLT, IEF)
- Yield curve data
- Futures (ZN, ZB)

**Core Metrics**
- Yield
- Duration
- Convexity
- Roll-down
- Carry

**Model Outputs**
- `fct_bond_risk`
- `fct_yield_curve`

**Valuation**
- Relative yield
- Curve positioning

---

### 4.3 Commodities
No fundamentals like equities → use structure.

**Key Signals**
- Backwardation / contango
- Momentum
- Inventory proxies

**Data**
- Futures prices
- Front vs next contracts

**Derived**
- `carry = roll_yield`

This plugs straight into portfolio logic.

---

### 4.4 FX
FX is relative valuation by definition.

**Signals**
- Interest rate differentials
- PPP deviations *(long term)*
- Momentum

**Model**
- expected_return = carry + momentum + valuation



---

### Step 3: Risk Decomposition
Your system should answer:

> “Where is my risk actually coming from?”

By:
- Asset class
- Factor
- Macro exposure

---

## 7. Portfolio Construction (Multi-Asset)

### Two Portfolio Layers (Important)

#### 1️⃣ Strategic Allocation (Slow)
- Equity / Rates / Commodity / FX
- Volatility budgets per bucket

#### 2️⃣ Tactical Allocation (Fast)
- Instrument selection within buckets
- Signal-driven tilts

This avoids **over-trading** and **regime whiplash**.

---

### Example Constraints
```yaml
asset_class_limits:
  equity: 0.60
  rates: 0.40
  commodities: 0.25
target_vol: 0.10
max_drawdown: 0.15
```

## 8. Backtesting (Multi-Asset Reality)

Your backtests must handle:
- Different trading calendars
- Roll schedules (futures)
- FX conversions
- Funding costs

> If you don’t model these,  
> **your Sharpe is fake.**

---

## 9. Monitoring & Explainability (This Is Your Edge)

Elastic / Kibana becomes gold here.

Track:
- Regime shifts
- Factor dominance
- Correlation spikes
- Asset-class contributions

You should see insights like:
> “Portfolio risk shifted from equities to rates due to yield curve inversion.”

That’s **institutional-level insight**.

---

## 10. Strategy Roadmap (Multi-Asset)

### Flagship Strategies to Build
- Global Balanced Risk Parity
- Carry + Momentum Multi-Asset
- Macro Regime-Aware Allocation
- Defensive Crisis Overlay

Each strategy is just:
- Different expected return models
- Different constraints
- Same engine