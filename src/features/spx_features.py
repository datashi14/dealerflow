import pandas as pd
import numpy as np
from datetime import date
from src.shared.db import get_db_connection, execute_query

def compute_spx_features(as_of: date):
    """
    Computes SPX flow features for a given date and writes to features_equity.
    """
    print(f"Computing SPX features for {as_of}...")

    # 1. Fetch raw options data
    query = """
    SELECT 
        option_symbol, type, strike, expiry, 
        open_interest, gamma, delta, underlying_price
    FROM raw_options
    WHERE as_of = %s AND underlying = 'SPX'
    """
    
    with get_db_connection() as conn:
        df = pd.read_sql(query, conn, params=(as_of,))

    if df.empty:
        print(f"No data found for {as_of}")
        return

    # Ensure numeric types
    cols = ['strike', 'open_interest', 'gamma', 'delta', 'underlying_price']
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    # 2. Core Calculations
    # GEX Contribution per contract = Gamma * Open Interest * 100 * Spot
    # But simplified: Gamma * OI
    
    # Convention: Net Gamma = (Call Gamma - Put Gamma)
    # This assumes dealers are short calls and long puts? 
    # Actually, let's calculate strictly "Call Gamma" and "Put Gamma" totals first.
    
    spot = df['underlying_price'].iloc[0]
    
    calls = df[df['type'] == 'call'].copy()
    puts = df[df['type'] == 'put'].copy()
    
    # Total GEX ($ exposure per 1% move approx)
    # GEX = Gamma * OI * 100 * Spot
    calls['gex'] = calls['gamma'] * calls['open_interest'] * 100 * spot
    puts['gex'] = puts['gamma'] * puts['open_interest'] * 100 * spot
    
    total_call_gex = calls['gex'].sum()
    total_put_gex = puts['gex'].sum()
    
    # Net Gamma: Often defined as Call GEX - Put GEX
    net_gamma = total_call_gex - total_put_gex
    
    # Gamma Flip Level
    # Find the strike where cumulative GEX turns from negative to positive?
    # Or simply where the Call GEX > Put GEX?
    # A simple approximation: bin by strike, calc net GEX per strike, find zero crossing.
    
    df['gex'] = df['gamma'] * df['open_interest'] * 100 * spot
    # If Put, GEX contribution is negative (assuming Dealer Long Put / Customer Short Put?) 
    # Let's stick to: Net GEX per strike = (Call GEX - Put GEX)
    
    gex_by_strike = pd.DataFrame(index=df['strike'].unique()).sort_index()
    gex_by_strike['call_gex'] = calls.groupby('strike')['gex'].sum()
    gex_by_strike['put_gex'] = puts.groupby('strike')['gex'].sum()
    gex_by_strike = gex_by_strike.fillna(0)
    gex_by_strike['net_gex'] = gex_by_strike['call_gex'] - gex_by_strike['put_gex']
    
    # Find zero crossing
    # We look for the strike where the cumulative sum crosses zero? 
    # Or just the strike where net_gex is closest to zero?
    # Usually Gamma Flip is where Net Gamma flips signs. 
    # Let's find the strike where the sign changes.
    
    # Simple approach: The strike with minimum absolute Net GEX? No.
    # Let's use the strike with the largest volume? No.
    # Let's just store the Net Gamma for now. 
    # A rigorous flip level requires a full volatility surface model.
    # We'll approximate it as the strike where Call OI = Put OI for now (PCR flip) 
    # or simply omit if too complex for v1.
    # Let's calculate Put/Call OI Ratio instead as a proxy.
    
    put_oi = puts['open_interest'].sum()
    call_oi = calls['open_interest'].sum()
    pcr = put_oi / call_oi if call_oi > 0 else 0
    
    # Gamma Slope: (Net Gamma) / Spot
    gamma_slope = net_gamma / spot if spot > 0 else 0
    
    # 3. Near Term / Expiry Buckets
    # Filter for < 5 days
    df['days_to_expiry'] = (pd.to_datetime(df['expiry']) - pd.to_datetime(as_of)).dt.days
    near_term = df[df['days_to_expiry'] <= 5]
    
    near_term_gamma = 0
    if not near_term.empty:
        nt_calls = near_term[near_term['type'] == 'call']
        nt_puts = near_term[near_term['type'] == 'put']
        nt_gex = (nt_calls['gamma'] * nt_calls['open_interest']).sum() - (nt_puts['gamma'] * nt_puts['open_interest']).sum()
        near_term_gamma = nt_gex * 100 * spot
        
    # Net Delta
    # Dealers are usually short calls (-Delta) and short puts (+Delta) ??
    # Let's just sum (Delta * OI) for calls and puts separately.
    # Dealer Net Delta = (Put Delta * Put OI) + (Call Delta * Call OI)
    # Assuming Dealers are SHORT everything:
    # Dealer Call Delta = -1 * Call Delta * OI
    # Dealer Put Delta = -1 * Put Delta * OI
    
    # Note: Put Delta is usually negative in data (-0.5). 
    # So Dealer Short Put (-1 * -0.5) = +0.5 (Long Delta). Correct.
    # Dealer Short Call (-1 * 0.5) = -0.5 (Short Delta). Correct.
    
    total_delta = (-1 * calls['delta'] * calls['open_interest']).sum() + (-1 * puts['delta'] * puts['open_interest']).sum()
    
    # Prepare record
    features = {
        'as_of': as_of,
        'underlying': 'SPX',
        'net_gamma': float(net_gamma),
        'gamma_below_spot': 0, # TODO: filter strikes < spot
        'gamma_above_spot': 0, # TODO: filter strikes > spot
        'gamma_near_expiry': float(near_term_gamma),
        'near_term_gamma_ratio': float(near_term_gamma / net_gamma) if net_gamma != 0 else 0,
        'gamma_slope': float(gamma_slope),
        'put_call_oi_ratio': float(pcr),
        'net_delta': float(total_delta),
        'gamma_flip_level': 0 # Stub
    }
    
    # Upsert into DB
    sql = """
    INSERT INTO features_equity 
    (as_of, underlying, net_gamma, gamma_near_expiry, near_term_gamma_ratio, gamma_slope, put_call_oi_ratio, net_delta, gamma_flip_level)
    VALUES (%(as_of)s, %(underlying)s, %(net_gamma)s, %(gamma_near_expiry)s, %(near_term_gamma_ratio)s, %(gamma_slope)s, %(put_call_oi_ratio)s, %(net_delta)s, %(gamma_flip_level)s)
    ON CONFLICT (as_of, underlying) DO UPDATE SET
    net_gamma = EXCLUDED.net_gamma,
    gamma_near_expiry = EXCLUDED.gamma_near_expiry,
    put_call_oi_ratio = EXCLUDED.put_call_oi_ratio,
    net_delta = EXCLUDED.net_delta;
    """
    
    execute_query(sql, features)
    print(f"Successfully computed and stored features for {as_of}")

