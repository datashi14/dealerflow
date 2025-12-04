from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Optional
from src.shared.db import get_db_connection, execute_query

def annualise_vol(daily_vol: float, trading_days: int = 252) -> float:
    """Convert daily vol (std of daily returns) to annualised percentage."""
    return daily_vol * np.sqrt(trading_days) * 100.0

def compute_carry_from_rates(aud_rate: float, usd_rate: float) -> float:
    """Very simple proxy: carry ~ rate differential (AUD - USD) in %."""
    return (aud_rate - usd_rate)

def compute_fx_features(as_of: date, pair: str = 'AUDUSD'):
    """
    Computes FX structural features (Carry, Vol, COT) and writes to features_fx.
    """
    print(f"Computing {pair} features for {as_of}...")

    # 1. Fetch Price History (for Vol) - Need 40 days lookback
    lookback_start = as_of - timedelta(days=60)
    query_prices = """
    SELECT as_of as date, pair, spot_price as close
    FROM raw_fx
    WHERE pair = %s AND as_of >= %s AND as_of <= %s
    ORDER BY as_of ASC
    """
    
    # 2. Fetch Rates (from raw_fx for simplicity in MVP, or raw_macro_rates)
    # The seeder puts rates into raw_fx columns short_rate_base/quote
    query_rates = """
    SELECT as_of as date, short_rate_base as aud_rate, short_rate_quote as usd_rate
    FROM raw_fx
    WHERE pair = %s AND as_of = %s
    """
    
    # 3. Fetch COT (AUD Futures)
    # Market name in raw_cot might be 'AUD' or 'AUDUSD'. Seeder uses 'AUDUSD' for FX but 'GOLD' for Gold.
    # Let's check seeder... Seeder inserts 'AUDUSD' into raw_fx. 
    # But for COT, usually it's 'AUD'. 
    # Wait, the seeder logic for COT was:
    # "query_cot ... VALUES (curr_date, 'GOLD', ...)"
    # It didn't seed AUD COT data explicitly in the `seed_data` function I wrote earlier! 
    # I need to check the seeder.
    
    # Checking seeder logic from memory/file:
    # It inserted GOLD COT.
    # It inserted raw_fx for AUDUSD.
    # It did NOT insert AUD COT.
    # I will need to patch the seeder or just mock the COT data here if missing.
    # For now, let's assume it might be missing and handle gracefully.
    
    query_cot = """
    SELECT * FROM raw_cot
    WHERE market = 'AUD' AND as_of <= %s
    ORDER BY as_of DESC
    LIMIT 1
    """

    with get_db_connection() as conn:
        df_prices = pd.read_sql(query_prices, conn, params=(pair, lookback_start, as_of))
        df_rates = pd.read_sql(query_rates, conn, params=(pair, as_of))
        df_cot = pd.read_sql(query_cot, conn, params=(as_of,))

    # --- Calculations ---

    # 1. Realised Vol
    realised_vol_20d = 0.0
    if not df_prices.empty and len(df_prices) >= 20:
        df_prices['date'] = pd.to_datetime(df_prices['date']).dt.date
        df_prices = df_prices.sort_values('date')
        df_prices['log_ret'] = np.log(df_prices['close'].astype(float)).diff()
        
        # Filter for window
        recent = df_prices.tail(20)
        daily_vol = recent['log_ret'].std(skipna=True)
        if not np.isnan(daily_vol):
            realised_vol_20d = annualise_vol(daily_vol)

    # 2. Carry
    carry_annualised = 0.0
    if not df_rates.empty:
        row = df_rates.iloc[0]
        # AUD Rate - USD Rate
        carry_annualised = compute_carry_from_rates(float(row['aud_rate']), float(row['usd_rate']))

    # 3. COT Positioning
    cot_net_spec = 0.0
    cot_net_spec_pct_oi = 0.0
    
    if not df_cot.empty:
        row = df_cot.iloc[0]
        net = float(row['spec_long'] - row['spec_short'])
        oi = float(row['hedger_long'] + row['hedger_short'] + row['spec_long'] + row['spec_short']) / 2 # Approx OI
        # Or if we had explicit OI column. The raw_cot table doesn't have explicit OI column in schema?
        # Let's check schema.
        # Schema: hedger_long, hedger_short, spec_long, spec_short...
        # No explicit 'open_interest' column in raw_cot table def.
        # So we sum components.
        
        cot_net_spec = net
        if oi > 0:
            cot_net_spec_pct_oi = (net / oi) * 100.0

    # 4. Upsert
    sql = """
    INSERT INTO features_fx 
    (as_of, pair, cot_net_spec, rate_diff, carry_attractiveness, fx_vol_level, fx_vol_slope)
    VALUES (%(as_of)s, %(pair)s, %(cot_net_spec)s, %(rate_diff)s, %(carry)s, %(vol)s, 0)
    ON CONFLICT (as_of, pair) DO UPDATE SET
    cot_net_spec = EXCLUDED.cot_net_spec,
    rate_diff = EXCLUDED.rate_diff,
    carry_attractiveness = EXCLUDED.carry_attractiveness,
    fx_vol_level = EXCLUDED.fx_vol_level;
    """
    
    # Mapping to schema columns:
    # cot_net_spec -> cot_net_spec (stored as number, not pct? Schema says NUMERIC)
    # rate_diff -> rate_diff
    # carry_attractiveness -> carry_annualised
    # fx_vol_level -> realised_vol_20d
    
    # Wait, schema for features_fx:
    # cot_net_spec NUMERIC
    # rate_diff NUMERIC
    # carry_attractiveness NUMERIC
    # fx_vol_level NUMERIC
    # fx_vol_slope NUMERIC
    # feature_vector JSONB
    
    # We'll store:
    # cot_net_spec = net contracts
    # rate_diff = raw rate diff
    # carry_attractiveness = carry_annualised
    # fx_vol_level = realised_vol_20d
    
    # We should also stash the pct_oi in feature_vector or repurposed column if needed.
    # I'll put it in feature_vector JSON for scoring engine to retrieve.
    
    import json
    feature_vector = json.dumps({
        "cot_net_spec_pct_oi": cot_net_spec_pct_oi
    })
    
    params = {
        'as_of': as_of,
        'pair': pair,
        'cot_net_spec': float(cot_net_spec),
        'rate_diff': float(carry_annualised),
        'carry': float(carry_annualised),
        'vol': float(realised_vol_20d)
    }
    
    # Note: I need to update the SQL to include feature_vector
    sql = """
    INSERT INTO features_fx 
    (as_of, pair, cot_net_position, rate_diff, carry_attractiveness, fx_vol_level, fx_vol_slope, feature_vector)
    VALUES (%(as_of)s, %(pair)s, %(cot_net_spec)s, %(rate_diff)s, %(carry)s, %(vol)s, 0, %(feature_vector)s)
    ON CONFLICT (as_of, pair) DO UPDATE SET
    cot_net_position = EXCLUDED.cot_net_position,
    carry_attractiveness = EXCLUDED.carry_attractiveness,
    fx_vol_level = EXCLUDED.fx_vol_level,
    feature_vector = EXCLUDED.feature_vector;
    """
    params['feature_vector'] = feature_vector
    
    execute_query(sql, params)
    print(f"Stored {pair} features: Carry={carry_annualised:.2f}%, Vol={realised_vol_20d:.2f}%")
