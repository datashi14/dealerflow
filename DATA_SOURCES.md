# Data Sources & Methodology

**DealerFlow** ingests data from a mix of professional and public sources to construct its macro risk dashboard.

## 1. Equity Volatility (SPX)
*   **Source**: [Databento](https://databento.com/) (OPRA.PILLAR / GLBX.MDP3)
*   **Data Type**: Daily Option Chains (EOD).
*   **Methodology**:
    *   Ingests raw daily OHLCV bars for SPX options.
    *   Merges with instrument definitions to resolve strikes and expirations.
    *   Infers option type (Put/Call) from CFI codes or OSI symbology.
    *   **Greeks**: Calculated via `py_vollib_vectorized` (Black-Scholes) using the daily closing spot price and a constant risk-free rate proxy.
    *   *Limitation*: Current feed (OHLCV-1d) often lacks Open Interest (OI), so Net Gamma Exposure (GEX) may default to 0. Full GEX requires a premium `open_interest` or `definition` feed.

## 2. Commodities (Gold)
*   **Source**: [Alpha Vantage](https://www.alphavantage.co/) & [CFTC](https://www.cftc.gov/)
*   **Price Data**: Uses `GLD` (SPDR Gold Shares ETF) as a high-fidelity proxy for Spot Gold prices (via Alpha Vantage `TIME_SERIES_DAILY`).
*   **Positioning**: Ingests weekly **Commitment of Traders (COT)** reports (Disaggregated Futures) from the CFTC archive.
*   **Methodology**:
    *   Maps "Managed Money" to Speculators and "Producer/Merchant" to Hedgers.
    *   *Limitation*: True "Backwardation" signals require Front-Month vs. Back-Month Futures prices. The current MVP uses Spot only, so the Term Structure signal is currently a placeholder.

## 3. FX (AUD/USD)
*   **Source**: [Alpha Vantage](https://www.alphavantage.co/) & [CFTC](https://www.cftc.gov/)
*   **Price Data**: Daily Spot FX rates (via Alpha Vantage `FX_DAILY`).
*   **Positioning**: Ingests weekly **Traders in Financial Futures (TFF)** reports from CFTC.
*   **Methodology**:
    *   Computes **Realised Volatility** (20-day annualized std dev of log returns).
    *   **Carry**: Derived from policy rate differentials (stubbed) or forward pricing.
    *   Maps "Leveraged Funds" to Speculators.

## 4. Database Schema
All data is normalized into a PostgreSQL database:
*   `raw_options`: Historical option prices and Greeks.
*   `raw_futures` / `raw_fx`: Underlying price history.
*   `raw_cot`: Weekly positioning data.
*   `features_*`: Derived structural signals (Gamma, Backwardation, Carry).
*   `asset_scores`: Final 0-100 Instability Index and Regime tags.
