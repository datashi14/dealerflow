import pandas as pd
import numpy as np
from datetime import date
from src.shared.db import get_db_connection, execute_query

def compute_asset_scores(as_of: date):
    """
    Computes Instability Index and Regimes for all assets on a given date.
    Currently supports: SPX (Equity)
    """
    print(f"Computing asset scores for {as_of}...")

    # 1. Fetch Equity Features
    query = """
    SELECT * FROM features_equity
    WHERE as_of = %s
    """
    
    with get_db_connection() as conn:
        df_equity = pd.read_sql(query, conn, params=(as_of,))

    if df_equity.empty:
        print(f"No feature data found for {as_of}")
        return

    # 2. Compute Scores for SPX
    # We iterate, but currently it's likely just one row per asset
    for _, row in df_equity.iterrows():
        symbol = row['underlying']
        net_gamma = row['net_gamma'] or 0
        gamma_slope = row['gamma_slope'] or 0
        net_delta = row['net_delta'] or 0
        
        # --- SCORING LOGIC (Heuristic v1) ---
        
        # Component 1: Flow Risk (Gamma)
        # Negative Net Gamma => High Instability
        # Normalize: Assume -5B to +5B is the typical range for Net Gamma $ Notional
        # (Our mock data might be small, so we scale relative to values seen)
        
        # For this mock/MVP, let's normalize arbitrarily:
        # If Net Gamma is negative, add to instability.
        # Score 0-100 where 100 is max instability.
        
        # Term: Gamma Risk
        # If net_gamma < 0: High risk. 
        # Let's map -1e9 (1B) to Score 80?
        # For mock data, values are small. Let's just use sign for now.
        
        flow_risk = 50
        if net_gamma < 0:
            flow_risk += 30 # Penalty for negative gamma
        else:
            flow_risk -= 20 # Reward for positive gamma
            
        # Component 2: Vol/Sensitivity Risk (Gamma Slope)
        # High absolute slope means dealer hedging changes fast -> Instability
        vol_risk = min(abs(gamma_slope) * 100, 100) # Cap at 100
        
        # Component 3: Directional Pressure
        # If Net Delta is Negative (Dealers Short), they must BUY as market goes UP (Stabilizing?)
        # Wait. Dealer Short Call (-Delta). Market UP -> Delta becomes MORE Short (-0.5 -> -0.7). 
        # Dealer must SELL to hedge?
        # Dealer Short Put (+Delta). Market UP -> Delta becomes LESS Long (+0.5 -> +0.2). 
        # Dealer must SELL to hedge?
        
        # Let's stick to simplified "Pressure Direction":
        # If Dealers are Short Delta (Total Delta < 0), they benefit from down moves?
        # Pressure is usually defined by where the hedging flows push.
        
        pressure_direction = "NEUTRAL"
        if net_delta < -1000: 
            pressure_direction = "DOWN" # Dealers short delta -> want market down? (Simplication)
        elif net_delta > 1000:
            pressure_direction = "UP"
            
        # --- UNIFIED INSTABILITY INDEX ---
        # Weighted average of risks
        instability_index = (flow_risk * 0.6) + (vol_risk * 0.4)
        instability_index = max(0, min(100, instability_index)) # Clamp 0-100
        
        # Regime Mapping
        regime = "FRAGILE"
        if instability_index < 30:
            regime = "STABLE"
        elif instability_index > 70:
            regime = "EXPLOSIVE"
            
        print(f"Scored {symbol}: Instability={instability_index:.1f} ({regime})")
        
        # 3. Upsert into asset_scores
        sql = """
        INSERT INTO asset_scores 
        (as_of, asset_type, symbol, instability_index, regime, pressure_direction, flow_risk, vol_risk, global_flow_score)
        VALUES (%(as_of)s, %(asset_type)s, %(symbol)s, %(instability)s, %(regime)s, %(pressure)s, %(flow_risk)s, %(vol_risk)s, %(global_score)s)
        ON CONFLICT (as_of, symbol) DO UPDATE SET
        instability_index = EXCLUDED.instability_index,
        regime = EXCLUDED.regime,
        pressure_direction = EXCLUDED.pressure_direction,
        flow_risk = EXCLUDED.flow_risk,
        global_flow_score = EXCLUDED.global_flow_score;
        """
        
        params = {
            'as_of': as_of,
            'asset_type': 'EQUITY',
            'symbol': symbol,
            'instability': instability_index,
            'regime': regime,
            'pressure': pressure_direction,
            'flow_risk': flow_risk / 100.0, # Normalize 0-1
            'vol_risk': vol_risk / 100.0,
            'global_score': instability_index # For now equal
        }
        
        execute_query(sql, params)

    print("Scoring complete.")
