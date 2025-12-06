import argparse
import os
import sys
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_connectors.databento_futures import DatabentoFuturesConnector
from src.db import get_connection, execute_sql

def upsert_future(as_of, underlying, contract_symbol, price, table="raw_futures"):
    # Delete existing to avoid ON CONFLICT issues (Schema drift protection)
    del_sql = "DELETE FROM raw_futures WHERE as_of = :as_of AND underlying = :underlying AND contract_symbol = :contract_symbol"
    execute_sql(del_sql, {"as_of": as_of, "underlying": underlying, "contract_symbol": contract_symbol})

    # Map to raw_futures schema
    sql = """
    INSERT INTO raw_futures (as_of, underlying, contract_symbol, settle_price, expiry, open_interest)
    VALUES (:as_of, :underlying, :contract_symbol, :price, :expiry, 0)
    """
    # Expiry proxy: 1 month out for Front, 2 months for Back
    expiry = as_of + timedelta(days=30) 
    if "n.1" in contract_symbol:
        expiry = as_of + timedelta(days=60)
        
    execute_sql(sql, {
        "as_of": as_of,
        "underlying": underlying,
        "contract_symbol": contract_symbol,
        "price": price,
        "expiry": expiry
    })

def ingest_all(target_date):
    connector = DatabentoFuturesConnector()
    print(f"--- Ingesting Futures via Databento for {target_date} ---")
    
    # Define assets to fetch (Front .n.0 and Back .n.1 for curve)
    assets = {
        "GOLD": ["GC.n.0", "GC.n.1"],
        "WTI": ["CL.n.0", "CL.n.1"],
        "AUDUSD": ["6A.n.0"], # FX Futures
        "JPY": ["6J.n.0"]     # JPY Futures
    }
    
    for underlying, symbols in assets.items():
        for sym in symbols:
            df = connector.get_daily_bars(sym, target_date, target_date)
            if not df.empty:
                row = df.iloc[0]
                price = float(row['close'])
                print(f"Fetched {underlying} ({sym}): {price}")
                upsert_future(row['as_of'], underlying, sym, price)
            else:
                print(f"Missing {underlying} ({sym})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default="2024-01-05")
    args = parser.parse_args()
    ingest_all(args.date)
