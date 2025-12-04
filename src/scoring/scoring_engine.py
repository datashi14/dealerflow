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

    # --- GOLD SCORING ---
    query_gold = """
    SELECT * FROM features_commodity
    WHERE as_of = %s AND underlying = 'GOLD'
    """
    with get_db_connection() as conn:
        df_gold = pd.read_sql(query_gold, conn, params=(as_of,))
        
    if not df_gold.empty:
        row = df_gold.iloc[0]
        symbol = 'GOLD'
        back_pct = float(row['backwardation_pct'] or 0)
        spec_net = float(row['spec_net_position'] or 0)
        
        # Logic:
        # 1. Structure Risk: High backwardation is bullish but "stressful" (shortage).
        #    Contango is "normal/stable".
        # 2. Positioning Risk: Crowded longs = Fragile.
        
        instability = 50
        pressure = "NEUTRAL"
        
        # Backwardation Analysis
        if back_pct > 0.001: # >0.1% backwardation
            instability += 20 # Stress
            pressure = "UP" # Scarcity drives price up
        elif back_pct < -0.005: # Deep contango
            instability -= 10 # Stable supply
            pressure = "DOWN" # Oversupply?
            
        # Positioning Analysis (Mock thresholds)
        # Assume > 200k is "Crowded Long"
        if spec_net > 200000:
            instability += 20 # Crowded
            # If crowded, could mean prone to washouts, but trend is UP.
        elif spec_net < 50000:
            instability += 10 # Speculators fled?
            
        instability = max(0, min(100, instability))
        
        regime = "FRAGILE"
        if instability < 40: regime = "STABLE"
        elif instability > 75: regime = "EXPLOSIVE"
        
        print(f"Scored {symbol}: Instability={instability:.1f} ({regime})")
        
        # Insert Scores
        sql = """
        INSERT INTO asset_scores 
        (as_of, asset_type, symbol, instability_index, regime, pressure_direction, flow_risk, vol_risk, global_flow_score)
        VALUES (%(as_of)s, %(asset_type)s, %(symbol)s, %(instability)s, %(regime)s, %(pressure)s, %(flow_risk)s, %(vol_risk)s, %(global_score)s)
        ON CONFLICT (as_of, symbol) DO UPDATE SET
        instability_index = EXCLUDED.instability_index,
        regime = EXCLUDED.regime,
        pressure_direction = EXCLUDED.pressure_direction;
        """
        
        params = {
            'as_of': as_of,
            'asset_type': 'COMMODITY',
            'symbol': symbol,
            'instability': instability,
            'regime': regime,
            'pressure': pressure,
            'flow_risk': back_pct * 1000, # Scaled arbitrarily
            'vol_risk': 0,
            'global_score': instability
        }
        execute_query(sql, params)

    # --- AUDUSD SCORING ---
    query_fx = """
    SELECT * FROM features_fx
    WHERE as_of = %s AND pair = 'AUDUSD'
    """
    with get_db_connection() as conn:
        df_fx = pd.read_sql(query_fx, conn, params=(as_of,))
        
    if not df_fx.empty:
        import json
        row = df_fx.iloc[0]
        symbol = 'AUDUSD'
        
        carry = float(row['carry_attractiveness'] or 0)
        vol = float(row['fx_vol_level'] or 0)
        net_spec = float(row['cot_net_position'] or 0)
        
        # Extract pct_oi from feature_vector if available
        pct_oi = 0.0
        if row['feature_vector']:
            try:
                fv = row['feature_vector']
                if isinstance(fv, str):
                    fv = json.loads(fv)
                pct_oi = float(fv.get('cot_net_spec_pct_oi', 0))
            except:
                pass
                
        # --- SCORING LOGIC ---
        
        # 1. Instability Score
        # Base: Volatility (5% = 0 score, 20% = 100 score)
        vol_score = max(0, min(100, (vol - 5.0) / 15.0 * 100.0))
        
        # Carry Modifier: 
        # Positive carry (stable) -> reduces score? 
        # Actually, high carry usually attracts crowded trades -> FRAGILE.
        # Negative carry -> capital flight -> UNSTABLE.
        # Let's use the user's logic:
        # "Positive carry tends to stabilise, negative tends to destabilise"
        # Carry -3% (bad) to +5% (good)
        carry_score = (5.0 - max(-3.0, min(5.0, carry))) / 8.0 * 100.0
        
        # Positioning Modifier:
        # Extreme positioning (>20% OI) -> Unstable
        pos_score = min(abs(pct_oi), 40.0) / 40.0 * 100.0
        
        # Weighted Avg
        instability = (0.5 * vol_score) + (0.25 * carry_score) + (0.25 * pos_score)
        instability = max(0, min(100, instability))
        
        # 2. Regime
        regime = "UNSTABLE"
        if instability < 30: regime = "STABLE"
        elif instability < 60: regime = "FRAGILE"
        
        # 3. Pressure
        pressure = "NEUTRAL"
        # Long Crowded + High Carry -> Downside Washout Risk
        if pct_oi > 20 and carry > 1.0:
            pressure = "DOWN"
        # Short Crowded + Positive Carry -> Squeeze Up Risk
        elif pct_oi < -20 and carry > 0.0:
            pressure = "UP"
            
        print(f"Scored {symbol}: Instability={instability:.1f} ({regime}) Pressure={pressure}")
        
        # Insert Scores
        sql = """
        INSERT INTO asset_scores 
        (as_of, asset_type, symbol, instability_index, regime, pressure_direction, flow_risk, vol_risk, global_flow_score)
        VALUES (%(as_of)s, %(asset_type)s, %(symbol)s, %(instability)s, %(regime)s, %(pressure)s, %(flow_risk)s, %(vol_risk)s, %(global_score)s)
        ON CONFLICT (as_of, symbol) DO UPDATE SET
        instability_index = EXCLUDED.instability_index,
        regime = EXCLUDED.regime,
        pressure_direction = EXCLUDED.pressure_direction;
        """
        
        params = {
            'as_of': as_of,
            'asset_type': 'FX',
            'symbol': symbol,
            'instability': instability,
            'regime': regime,
            'pressure': pressure,
            'flow_risk': pct_oi / 100.0, 
            'vol_risk': vol / 100.0,
            'global_score': instability
        }
        execute_query(sql, params)

    print("Scoring complete.")
