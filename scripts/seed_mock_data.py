import sys
import os
import random
import argparse
from datetime import date, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.shared.db import execute_query

def generate_random_walk(start_price, days, volatility=0.01):
    prices = [start_price]
    for _ in range(days):
        change = prices[-1] * random.gauss(0, volatility)
        prices.append(prices[-1] + change)
    return prices

def seed_data(days_history=30):
    print(f"Seeding {days_history} days of history...")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days_history)
    
    # Price paths
    spx_prices = generate_random_walk(4500, days_history)
    gold_prices = generate_random_walk(2000, days_history, 0.008)
    aud_prices = generate_random_walk(0.65, days_history, 0.005)
    
    curr_date = start_date
    for i in range(days_history + 1):
        print(f"Seeding {curr_date}...")
        
        # --- SPX OPTIONS ---
        # Generate ~20 options per day (mix of strikes)
        base_price = spx_prices[i]
        expiry = curr_date + timedelta(days=7) # Constant 7-day expiry for simplicity
        
        for _ in range(20):
            strike = int(base_price + (random.randint(-5, 5) * 10))
            option_type = 'call' if random.random() > 0.5 else 'put'
            symbol = f"SPXW{expiry.strftime('%y%m%d')}{'C' if option_type == 'call' else 'P'}{int(strike*1000):08d}"
            
            # Mock Greeks
            iv = random.uniform(0.1, 0.3)
            delta = random.uniform(0, 1) if option_type == 'call' else random.uniform(-1, 0)
            gamma = random.uniform(0, 0.05)
            oi = random.randint(100, 5000)
            
            query_opt = """
            INSERT INTO raw_options 
            (as_of, underlying, option_symbol, type, strike, expiry, underlying_price, bid, ask, last, open_interest, implied_volatility, delta, gamma)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            execute_query(query_opt, (
                curr_date, 'SPX', symbol, option_type, strike, expiry, base_price,
                10.0, 11.0, 10.5, oi, iv, delta, gamma
            ))

        # --- GOLD FUTURES ---
        # Front month and back month (to calc term structure)
        front_price = gold_prices[i]
        back_price = front_price * (1 + random.uniform(-0.005, 0.005)) # Slight random contango/backwardation
        
        query_fut = """
        INSERT INTO raw_futures
        (as_of, underlying, contract_symbol, expiry, settle_price, open_interest, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        # Front
        execute_query(query_fut, (curr_date, 'GOLD', 'GCZ5', curr_date + timedelta(days=30), front_price, 150000, 20000))
        # Back
        execute_query(query_fut, (curr_date, 'GOLD', 'GCG6', curr_date + timedelta(days=60), back_price, 50000, 5000))
        
        # --- COT DATA (Weekly) ---
        # Only insert if it's a Friday (approx) or just duplicate for daily simplicity in mock
        # Let's mock a trend in positioning
        trend_factor = i / days_history
        hedger_long = 100000 + (trend_factor * 10000)
        hedger_short = 150000 - (trend_factor * 5000)
        spec_long = 200000 + (trend_factor * 20000)
        spec_short = 50000
        
        query_cot = """
        INSERT INTO raw_cot
        (as_of, market, hedger_long, hedger_short, spec_long, spec_short, small_long, small_short)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(query_cot, (curr_date, 'GOLD', hedger_long, hedger_short, spec_long, spec_short, 10000, 10000))
        
        # --- AUDUSD FX ---
        aud_spot = aud_prices[i]
        query_fx = """
        INSERT INTO raw_fx
        (as_of, pair, spot_price, short_rate_base, short_rate_quote, implied_vol_1m)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_query(query_fx, (curr_date, 'AUDUSD', aud_spot, 4.35, 5.50, 9.5))

        curr_date += timedelta(days=1)

    print("Seeding complete.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30, help="Days of history to seed")
    args = parser.parse_args()
    
    try:
        seed_data(args.days)
    except Exception as e:
        print(f"Error seeding data: {e}")
