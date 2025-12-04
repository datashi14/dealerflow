# DealerFlow Report Design

This document describes the **output layer** of DealerFlow:  
the human-readable macro report generated from `asset_scores` and feature tables.

The goal is a **simple, opinionated weekly summary** that can be shared publicly (e.g. on LinkedIn) without exposing internal complexity.

---

## 1. Report Frequency

- **Daily snapshot** (for personal use / debugging).
- **Weekly report** (public-facing, LinkedIn-ready).

The weekly report typically runs on **weekend** data (e.g. last trading day of the week).

---

## 2. Core Concepts

For each tracked asset (initially: `SPX`, `GOLD`, `AUDUSD`), the engine computes:

- `instability_index` (0–100)
- `regime` ∈ {`STABLE`, `FRAGILE`, `EXPLOSIVE`}
- `pressure_direction` ∈ {`UP`, `DOWN`, `NEUTRAL`}
- Supporting features (from `features_*` tables).
- Global context: `credit_regime`, `rate_regime`, etc.

The report is structured into the following sections:

1. Global Flow Map
2. Per-Asset Snapshots
   - SPX (Equity Flow)
   - Gold (Commodity Flow)
   - AUDUSD (FX Flow)
3. Cross-Asset Themes
4. Credit Cycle Snapshot
5. Rates & Liquidity Snapshot (Fed vs RBA)
6. Next Week Watchlist
7. Disclaimer

---

## 3. Section-by-Section Design

### 3.1 Global Flow Map

**Purpose:** give a one-glance table for the main assets.

Example layout:

```text
| Asset  | Instability | Regime    | Pressure | Short Note                        |
|--------|-------------|-----------|----------|-----------------------------------|
| SPX    | 74          | EXPLOSIVE | Down     | Dealers short gamma; fragility.   |
| GOLD   | 61          | FRAGILE   | Up       | Backwardation + spec longs.       |
| AUDUSD | 42          | FRAGILE   | Down     | Negative carry, weak China tone.  |
```

Fields:
- **Instability** → from `asset_scores.instability_index`
- **Regime** → from `asset_scores.regime`
- **Pressure** → from `asset_scores.pressure_direction`
- **Short Note** → single summary sentence generated via commentary rules.


### 3.2 SPX Flow Snapshot

Uses `features_equity` and `asset_scores` for SPX.

**Structural Signals**
Bulleted, rule-based summary, e.g.:
- **Net Gamma:** Deeply negative → hedging flows amplify moves.
- **Near-Expiry Gamma:** Elevated → same-day/weekly options increase intraday twitchiness.
- **Gamma Slope:** Steep → small moves in price trigger large changes in hedging demand.
- **Dealer Delta:** Net short → hedging can add selling pressure on down-moves.

*These bullets come from pre-defined mapping of feature ranges → phrases.*

**Interpretation Paragraph**
A short paragraph combining:
- `regime`
- `instability_index`
- `pressure_direction`
- `gamma_state` and `delta_state`

*Example:*
> “SPX is in an EXPLOSIVE regime – dealer positioning is fragile and flows are more likely to amplify moves rather than dampen them. With dealers short gamma and leaning short delta, the structure favours wider ranges and asymmetric downside risk until positioning stabilises.”


### 3.3 Gold Flow Snapshot

Uses `features_commodity` and `asset_scores` for GOLD.

**Structural Signals**
Example bullets:
- **COT Spec Net Long:** Rising → momentum flows building on the long side.
- **Term Structure:** Mild backwardation → constructive near-term demand.
- **Roll Yield:** Positive → roll mechanics currently favour longs.
- **Open Interest:** Increasing → fresh positioning entering the market.

**Interpretation Paragraph**
*Example:*
> “Gold is in a FRAGILE but constructive regime. Rising backwardation and growing speculative length point to a structurally supportive backdrop, as long as USD strength and real yields don’t move sharply against it.”


### 3.4 AUDUSD Flow Snapshot

Uses `features_fx` and `asset_scores` for AUDUSD.

**Structural Signals**
Example bullets:
- **COT Specs:** Heavily short AUD → crowded bearish positioning.
- **Carry:** Negative vs USD → structural flows favour USD.
- **FX Vol:** Elevated → larger intraday ranges more likely.
- **China Link:** Narrative still leans negative for AUD-sensitive sectors. (Optional if narrative engine is present.)

**Interpretation Paragraph**
*Example:*
> “AUDUSD sits in a FRAGILE / BEARISH regime. Negative carry, heavy speculative shorts and weak China-linked narrative keep the path of least resistance tilted lower, with rallies more likely to be short-covering than a shift in fundamentals.”


### 3.5 Cross-Asset Themes

Uses all three `asset_scores` plus global context (credit/rates) to emit 2–5 bulleted themes.

*Examples:*
- “Equity risk is driving the tape – SPX sits in an explosive, downside-biased regime where dealer positioning amplifies moves.”
- “Gold is acting as a hedge – flows and term structure point to a constructive backdrop for precious metals in a risk-off environment.”
- “Flows are aligning in a classic risk-off pattern – equities under pressure, AUD weak, and Gold supported.”

*A small rule engine selects which sentences to include based on current regimes and directions.*


### 3.6 Credit Cycle Snapshot

Summarises the `features_credit` state and its `credit_regime`.

*Example:*
**Credit Regime: STRESS BUILDING**
High-yield vs investment-grade spreads have been widening and the yield curve remains inverted. This indicates a background where shocks are less easily absorbed, and downside moves in risk assets can be harder to fade.

This section typically includes:
- The regime (Easy / Late-Cycle / Stress Building / Deleveraging)
- 1–2 bullets about spreads, curve, and funding proxies.


### 3.7 Rates & Liquidity Snapshot (Fed vs RBA)

Summarises `features_rates`:
- `fed_rate`
- `rba_rate`
- `rate_diff`
- `liquidity_score`

*Example:*
**Rates & Liquidity:**
The Fed–RBA rate differential currently favours USD, with global liquidity still on the tighter side. This is a structural headwind for AUD and a constraint on risk appetite until policy eases more decisively.


### 3.8 Next Week Watchlist

Combines:
- Largest week-on-week changes in `Instability Index`.
- Any notable shifts in credit or rates features.
- A manually maintained macro event calendar (e.g. major US/AU data, central bank meetings).

*Example bullets:*
- “SPX Instability has risen sharply over the past week – watch how dealer gamma evolves into next Friday’s options expiry.”
- “Gold term structure has moved into backwardation – monitor whether this persists or reverts as data comes in.”
- “AUDUSD remains heavily shorted – any positive surprise from China or RBA guidance could trigger a sharp short-covering move.”


### 3.9 Disclaimer

Every report ends with a clear, visible disclaimer, for example:

> This report is generated automatically by DealerFlow, a personal research project.
> It is not investment advice, a recommendation, or a solicitation to buy or sell any financial instrument.
> It is provided purely for educational and informational purposes.


## 4. Implementation Notes

- The report is composed in **Markdown**, then:
  - Rendered to HTML for web,
  - Or posted as text/markdown on LinkedIn.
- Commentary is **rule-based**, not LLM-dependent, to keep behaviour deterministic and reproducible.
- Numerical thresholds and phrase mappings are kept in a **config file** to make tuning easier (e.g. “what counts as ‘deeply negative gamma’ or ‘elevated vol’”).


## 5. Example Output (High-Level)

A typical weekly report includes:
1. Title + date
2. Global Flow Map table
3. SPX, Gold, AUDUSD snapshots
4. 3–5 cross-asset themes
5. 1–2 paragraphs on credit + rates backdrop
6. 3–5 bullets for next week’s watchlist
7. Disclaimer

The entire report is kept to 1–2 pages to remain readable while still conveying depth.
