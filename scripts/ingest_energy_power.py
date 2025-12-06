import argparse
import os
import sys
import pandas as pd
from sqlalchemy import text

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_connectors.aemo import AEMOClient
from src.db import get_connection

REGIONS = ['NSW1', 'VIC1', 'QLD1', 'SA1', 'TAS1']

def ingest_power_prices(year, month):
    client = AEMOClient()
    
    for region in REGIONS:
        print(f"Processing {region} for {year}-{month:02d}...")
        
        # 1. Fetch Raw Intervals
        df_raw = client.fetch_price_and_demand(year, month, region)
        
        if df_raw.empty:
            print(f"No data for {region}.")
            continue
            
        # 2. Aggregate Daily
        df_daily = client.aggregate_daily(df_raw)
        print(f"Aggregated {len(df_daily)} daily records.")
        
        # 3. Prepare Rows
        rows = []
        for _, row in df_daily.iterrows():
            rows.append({
                "as_of": row['as_of'],
                "region": region,
                "price_average": float(row['price_average']),
                "price_min": float(row['price_min']),
                "price_max": float(row['price_max']),
                "demand_mw_average": float(row['demand_mw_average']),
                "demand_mw_peak": float(row['demand_mw_peak']),
                "currency": "AUD",
                "source": "AEMO"
            })
            
        # 4. Upsert
        sql = """
        INSERT INTO raw_energy_power_prices 
        (as_of, region, price_average, price_min, price_max, demand_mw_average, demand_mw_peak, currency, source)
        VALUES (:as_of, :region, :price_average, :price_min, :price_max, :demand_mw_average, :demand_mw_peak, :currency, :source)
        ON CONFLICT (as_of, region, source) 
        DO UPDATE SET 
            price_average = EXCLUDED.price_average,
            price_min = EXCLUDED.price_min,
            price_max = EXCLUDED.price_max,
            demand_mw_average = EXCLUDED.demand_mw_average,
            demand_mw_peak = EXCLUDED.demand_mw_peak;
        """
        
        count = 0
        with get_connection() as conn:
            with conn.begin():
                for r in rows:
                    conn.execute(text(sql), r)
                    count += 1
        
        print(f"Upserted {count} rows for {region}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2024)
    parser.add_argument("--month", type=int, default=1)
    args = parser.parse_args()
    
    ingest_power_prices(args.year, args.month)
