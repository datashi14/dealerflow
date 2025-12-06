import argparse
import os
import sys
import pandas as pd
from datetime import datetime

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_connectors.eia import EIAClient
from src.db import get_connection, execute_sql
from sqlalchemy import text

def ingest_oil_futures(start_date="2023-01-01"):
    client = EIAClient()
    print(f"Fetching Oil Futures from EIA since {start_date}...")
    
    # Fetch WTI (CL) - Contract 1 (Front Month)
    # Using simplified path/facets for demo. Real EIA API needs exact series IDs.
    # Series ID for WTI Fut 1: PET.RCLC1.D
    df = client.get_series(
        "petroleum/pri/fut", 
        start_date=start_date,
        facets={"series": ["RCLC1"]} # WTI Contract 1
    )
    
    if df.empty:
        print("No data returned.")
        return

    # Parse
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "as_of": row['period'],
            "symbol": "WTI",
            "contract_month": row['period'], # Proxy for now
            "contract_code": "CL1",
            "price_settle": float(row['value']),
            "currency": "USD",
            "source": "EIA"
        })
        
    # Upsert SQL
    sql = """
    INSERT INTO raw_energy_oil_futures 
    (as_of, symbol, contract_month, contract_code, price_settle, currency, source)
    VALUES (:as_of, :symbol, :contract_month, :contract_code, :price_settle, :currency, :source)
    ON CONFLICT (as_of, symbol, contract_month, source) 
    DO UPDATE SET price_settle = EXCLUDED.price_settle;
    """
    
    count = 0
    with get_connection() as conn:
        with conn.begin(): # Transaction
            for r in rows:
                conn.execute(text(sql), r)
                count += 1
                
    print(f"Upserted {count} WTI futures records.")

if __name__ == "__main__":
    ingest_oil_futures()
