import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_connectors.alpha_vantage import AlphaVantageConnector
from src.db import write_dataframe

def ingest_gold():
    connector = AlphaVantageConnector()
    # Fetch XAUUSD (Spot Gold)
    df = connector.get_commodity_daily("GOLD")
    
    if df.empty:
        print("No data fetched.")
        return

    # Transform for raw_futures table
    # Columns: as_of, underlying, contract_symbol, expiry, settle_price, open_interest, volume
    
    # Map XAUUSD spot data to this schema
    df_fut = df.copy()
    df_fut['underlying'] = 'GOLD'
    df_fut['contract_symbol'] = 'SPOT'
    df_fut['expiry'] = df_fut['as_of'] # Spot expires daily?
    df_fut['settle_price'] = df_fut['spot_price']
    df_fut['open_interest'] = 0
    df_fut['volume'] = 0
    
    # Select only needed columns
    df_fut = df_fut[['as_of', 'underlying', 'contract_symbol', 'expiry', 'settle_price', 'open_interest', 'volume']]
    
    print(f"Ingesting {len(df_fut)} rows of Gold Spot...")
    write_dataframe(df_fut, 'raw_futures', if_exists='append', index=False)

if __name__ == "__main__":
    ingest_gold()
