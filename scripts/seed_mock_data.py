import sys
import os
import random
from datetime import date, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.shared.db import execute_query

def seed_spx_options():
    print("Seeding 10 fake SPX options...")
    
    base_price = 4500.0
    today = date.today()
    expiry = today + timedelta(days=7)
    
    for i in range(10):
        strike = base_price + (random.randint(-5, 5) * 10)
        option_type = 'call' if random.random() > 0.5 else 'put'
        symbol = f"SPXW{expiry.strftime('%y%m%d')}{'C' if option_type == 'call' else 'P'}{int(strike*1000):08d}"
        
        # Mock data
        bid = random.uniform(10, 50)
        ask = bid + random.uniform(0.5, 2.0)
        last = (bid + ask) / 2
        iv = random.uniform(0.1, 0.3)
        delta = random.uniform(0, 1) if option_type == 'call' else random.uniform(-1, 0)
        gamma = random.uniform(0, 0.05)
        oi = random.randint(100, 5000)
        
        query = """
        INSERT INTO raw_options 
        (as_of, underlying, option_symbol, type, strike, expiry, underlying_price, bid, ask, last, open_interest, implied_volatility, delta, gamma)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            today, 'SPX', symbol, option_type, strike, expiry, base_price,
            bid, ask, last, oi, iv, delta, gamma
        )
        
        try:
            execute_query(query, params)
            print(f"Inserted {symbol}")
        except Exception as e:
            print(f"Failed to insert {symbol}: {e}")

    print("Seeding complete.")

def verify_data():
    print("\nVerifying data in raw_options:")
    rows = execute_query("SELECT * FROM raw_options ORDER BY created_at DESC LIMIT 10", fetch=True)
    for row in rows:
        print(f"{row['as_of']} | {row['option_symbol']} | Strike: {row['strike']} | IV: {row['implied_volatility']:.2f}")

if __name__ == '__main__':
    try:
        seed_spx_options()
        verify_data()
    except Exception as e:
        print(f"Error seeding data (DB might not be connected): {e}")
