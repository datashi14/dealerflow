import pandas as pd
from datetime import date
from src.shared.db import get_db_connection, execute_query

def compute_commodity_features(as_of: date, underlying: str = 'GOLD'):
    """
    Computes Commodity flow features (Term Structure, COT) and writes to features_commodity.
    """
    print(f"Computing {underlying} features for {as_of}...")

    # 1. Fetch Futures Data (Front & Back Month)
    # We assume the seeder inserts 2 contracts per day.
    # In real life, we'd sort by expiry and pick the first two > as_of.
    
    query_fut = """
    SELECT * FROM raw_futures
    WHERE as_of = %s AND underlying = %s
    ORDER BY expiry ASC
    """
    
    with get_db_connection() as conn:
        df_fut = pd.read_sql(query_fut, conn, params=(as_of, underlying))
        
    # 2. Fetch COT Data
    query_cot = """
    SELECT * FROM raw_cot
    WHERE as_of <= %s AND market = %s
    ORDER BY as_of DESC
    LIMIT 1
    """
    with get_db_connection() as conn:
        df_cot = pd.read_sql(query_cot, conn, params=(as_of, underlying))

    if df_fut.empty:
        print(f"No futures data found for {underlying} on {as_of}")
        return

    # --- CALCULATIONS ---
    
    # Term Structure (Backwardation %)
    # If Front > Back => Backwardation (Positive for price usually, scarcity)
    # If Front < Back => Contango (Negative/Neutral)
    # Backwardation % = (Front - Back) / Front
    
    backwardation_pct = 0
    roll_yield = 0
    
    if len(df_fut) >= 2:
        front = df_fut.iloc[0]
        back = df_fut.iloc[1]
        
        f_price = float(front['settle_price'])
        b_price = float(back['settle_price'])
        
        if f_price > 0:
            backwardation_pct = (f_price - b_price) / f_price
            # Roll Yield approximation (annualized? No, just raw spread for now)
            roll_yield = backwardation_pct 

    # COT Positioning
    hedger_net = 0
    spec_net = 0
    
    if not df_cot.empty:
        row = df_cot.iloc[0]
        hedger_net = float(row['hedger_long'] - row['hedger_short'])
        spec_net = float(row['spec_long'] - row['spec_short'])

    # OI Change
    # Need yesterday's OI to calc change. For MVP, simplified to 0 or fetched if easy.
    oi_change = 0
    
    # Upsert
    features = {
        'as_of': as_of,
        'underlying': underlying,
        'hedger_net_position': hedger_net,
        'spec_net_position': spec_net,
        'backwardation_pct': backwardation_pct,
        'roll_yield': roll_yield,
        'oi_change': oi_change,
        'vol_term_structure': 0 # Stub
    }
    
    sql = """
    INSERT INTO features_commodity 
    (as_of, underlying, hedger_net_position, spec_net_position, backwardation_pct, roll_yield, oi_change, vol_term_structure)
    VALUES (%(as_of)s, %(underlying)s, %(hedger_net_position)s, %(spec_net_position)s, %(backwardation_pct)s, %(roll_yield)s, %(oi_change)s, %(vol_term_structure)s)
    ON CONFLICT (as_of, underlying) DO UPDATE SET
    hedger_net_position = EXCLUDED.hedger_net_position,
    spec_net_position = EXCLUDED.spec_net_position,
    backwardation_pct = EXCLUDED.backwardation_pct,
    roll_yield = EXCLUDED.roll_yield;
    """
    
    execute_query(sql, features)
    print(f"Stored {underlying} features: Back%={backwardation_pct:.4f}, SpecNet={spec_net}")
