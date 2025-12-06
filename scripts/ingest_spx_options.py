import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_connectors.spx_options import SPXOptionsConnector
from src.db import write_dataframe

def ingest_spx_options(target_date, spot_price):
    connector = SPXOptionsConnector()
    
    # 1. Fetch Chain
    df = connector.get_option_chain(target_date, underlying="SPX")
    
    if df.empty:
        print("No options data found.")
        return

    print(f"Fetched {len(df)} contracts.")
    
    # 2. Calculate Greeks
    # We need the spot price to compute IV/Delta/Gamma
    df = connector.calculate_greeks(df, spot_price)

    # 2b. Check for Open Interest (Synthetic Fill)
    # Databento OHLCV-1d usually lacks OI. If max OI is 0, generate synthetic.
    if df['open_interest'].max() == 0:
        print("WARNING: No Open Interest found in feed. Using synthetic generator.")
        df = connector.generate_synthetic_oi(df, spot_price)
    
    # 3. Write to DB
    # Drop intermediate columns (T)
    if 'T' in df.columns:
        df = df.drop(columns=['T'])
        
    print(f"Ingesting {len(df)} rows to raw_options...")
    write_dataframe(df, 'raw_options', if_exists='append', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--spot", type=float, default=6000.0, help="SPX Spot Price for Greeks")
    
    args = parser.parse_args()
    
    try:
        as_of = datetime.strptime(args.date, "%Y-%m-%d").date()
        ingest_spx_options(as_of, args.spot)
    except ValueError:
        print("Invalid date format.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
