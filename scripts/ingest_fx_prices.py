import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_connectors.alpha_vantage import AlphaVantageConnector
from src.db import write_dataframe

def ingest_fx(pair="AUD", to_symbol="USD"):
    connector = AlphaVantageConnector()
    df = connector.get_fx_daily(pair, to_symbol)
    
    if df.empty:
        print("No data fetched.")
        return

    # Write to DB
    # Table: raw_fx
    # Columns: as_of, pair, spot_price, short_rate_base, short_rate_quote, implied_vol_1m
    
    # DF has: as_of, pair, spot_price...
    # We need to map to exact schema columns if write_dataframe doesn't do it automatically?
    # to_sql usually matches by name.
    
    print(f"Ingesting {len(df)} rows for {pair}{to_symbol}...")
    write_dataframe(df, 'raw_fx', if_exists='append', index=False)

if __name__ == "__main__":
    ingest_fx()
