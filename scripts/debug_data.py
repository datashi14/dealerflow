import os
import sys
import pandas as pd
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db import get_connection

def check_data(target_date):
    print(f"--- Diagnosing Data for {target_date} ---")
    
    with get_connection() as conn:
        # 1. Check Gold Futures (Prices)
        df_gold = pd.read_sql(
            "SELECT count(*) as cnt, min(as_of) as min_date, max(as_of) as max_date FROM raw_futures WHERE underlying='GOLD'", 
            conn
        )
        print(f"\nGold Futures (raw_futures):")
        print(df_gold)
        
        # Check specific date
        df_gold_spot = pd.read_sql(
            "SELECT * FROM raw_futures WHERE underlying='GOLD' AND as_of = %s", 
            conn, params=(target_date,)
        )
        print(f"Gold Rows for {target_date}: {len(df_gold_spot)}")

        # 2. Check COT (Positioning)
        df_cot = pd.read_sql(
            "SELECT count(*) as cnt, min(as_of) as min_date, max(as_of) as max_date FROM raw_cot", 
            conn
        )
        print(f"\nCOT Data (raw_cot):")
        print(df_cot)
        
        # Check recent COT before date
        df_cot_near = pd.read_sql(
            "SELECT * FROM raw_cot WHERE as_of <= %s ORDER BY as_of DESC LIMIT 5",
            conn, params=(target_date,)
        )
        print(f"Recent COT rows before {target_date}:")
        print(df_cot_near[['as_of', 'market', 'spec_long', 'spec_short']])

        # 3. Check FX Prices
        df_fx = pd.read_sql(
            "SELECT * FROM raw_fx WHERE as_of = %s AND pair='AUDUSD'",
            conn, params=(target_date,)
        )
        print(f"\nFX Rows for {target_date}: {len(df_fx)}")

if __name__ == "__main__":
    check_data(date(2024, 1, 5))
