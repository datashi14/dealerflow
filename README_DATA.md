# Real Data Ingestion

This project now supports ingesting real market data from Alpha Vantage and the CFTC.

## 1. Setup

### Environment Variables
Add your Alpha Vantage API key to `.env`:
```bash
ALPHA_VANTAGE_KEY=your_key_here
```

## 2. Running Ingestion

### FX Prices (AUDUSD)
Fetches daily spot prices from Alpha Vantage.
```bash
python scripts/ingest_fx_prices.py
```

### Gold Prices (XAUUSD)
Fetches daily spot gold prices from Alpha Vantage (stored as 'SPOT' contract in futures table).
```bash
python scripts/ingest_gold_prices.py
```

### COT Data (Gold & AUD)
Downloads the latest 2025 COT reports from cftc.gov and ingests them.
*   Gold: Disaggregated Futures (Producer/Merchant vs Managed Money)
*   AUD: Traders in Financial Futures (Dealer/Asset Mgr vs Leveraged Funds)
```bash
python scripts/ingest_cot_data.py
```

## 3. Next Steps
After ingesting real data, run the feature/scoring pipeline as usual:
```bash
python scripts/compute_fx_features.py --date YYYY-MM-DD
python scripts/compute_commodity_features.py --date YYYY-MM-DD
python scripts/score_assets.py --date YYYY-MM-DD
python scripts/generate_report.py --date YYYY-MM-DD
```
