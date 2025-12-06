import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db import get_connection

def seed_fx_cot():
    print("Seeding Mock FX COT for AUD...")
    
    # Check if exists
    check_sql = "SELECT 1 FROM raw_cot WHERE as_of = :as_of AND market = :market"
    
    params = {
        "as_of": "2024-01-02",
        "market": "AUD",
        "spec_long": 40000,
        "spec_short": 50000, # Net -10k
        "hedger_long": 100000,
        "hedger_short": 80000,
        "small_long": 5000,
        "small_short": 5000
    }
    
    with get_connection() as conn:
        with conn.begin():
            exists = conn.execute(text(check_sql), {"as_of": params["as_of"], "market": params["market"]}).fetchone()
            
            if not exists:
                sql = """
                INSERT INTO raw_cot (as_of, market, spec_long, spec_short, hedger_long, hedger_short, small_long, small_short)
                VALUES (:as_of, :market, :spec_long, :spec_short, :hedger_long, :hedger_short, :small_long, :small_short)
                """
                conn.execute(text(sql), params)
                print("Mock AUD COT seeded.")
            else:
                print("Mock AUD COT already exists.")

if __name__ == "__main__":
    seed_fx_cot()
