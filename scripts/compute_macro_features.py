import argparse
import os
import sys
import pandas as pd
from datetime import datetime, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import get_connection, execute_sql

def compute_macro_features(as_of: date):
    print(f"Computing Macro Features for {as_of}...")
    
    # --- 1. RATES (Mocked for Demo: Rising Yields Scenario) ---
    # On Jan 5 2024: US 10Y ~4.05%, JP 10Y ~0.60%
    us10y = 4.05
    jp10y = 0.60
    us2y = 4.40
    jp2y = 0.05
    
    spread_10y = us10y - jp10y
    spread_2y = us2y - jp2y
    
    policy_risk = "LOW"
    if us2y < us10y: policy_risk = "RISING" # Inversion normalization?
    
    sql_rates = """
    INSERT INTO features_rates_spreads (as_of, us10y, jp10y, us2y, jp2y, spread_usjp_10y, spread_usjp_2y, policy_error_risk)
    VALUES (:as_of, :us10y, :jp10y, :us2y, :jp2y, :spread_usjp_10y, :spread_usjp_2y, :policy_error_risk)
    ON CONFLICT (as_of) DO UPDATE SET
    us10y=EXCLUDED.us10y, jp10y=EXCLUDED.jp10y, spread_usjp_10y=EXCLUDED.spread_usjp_10y;
    """
    execute_sql(sql_rates, {
        "as_of": as_of, "us10y": us10y, "jp10y": jp10y, "us2y": us2y, "jp2y": jp2y,
        "spread_usjp_10y": spread_10y, "spread_usjp_2y": spread_2y, "policy_error_risk": policy_risk
    })
    
    # --- 2. JPY REFLEXIVITY ---
    # Logic: If JP yields rising AND Yen weakening => Bad loop?
    # Mock: Yen weakening (USDJPY up), JGB stable.
    yen_weakening = True 
    jgb_rising = (jp10y > 0.55) # It was rising from 0.50
    reflexive = yen_weakening and jgb_rising
    
    sql_reflex = """
    INSERT INTO features_reflexivity_jp (as_of, yen_weakening_with_infl, jgb_yields_rising, reflexive_loop_active, comment)
    VALUES (:as_of, :yen_weakening, :jgb_rising, :reflexive, :comment)
    ON CONFLICT (as_of) DO UPDATE SET reflexive_loop_active=EXCLUDED.reflexive_loop_active;
    """
    execute_sql(sql_reflex, {
        "as_of": as_of, "yen_weakening": yen_weakening, "jgb_rising": jgb_rising, 
        "reflexive": reflexive, "comment": "Yen carry trade unwinding pressure building."
    })
    
    # --- 3. CROSS BORDER FLOWS ---
    # DXY +3% in 20d (Mock), SPX -2% (Mock) -> Dollar Wrecking Ball
    dxy_ret = 2.5
    spx_ret = -1.5
    corr = 0.6
    
    stress = "NORMAL"
    if dxy_ret > 2.0 and spx_ret < -1.0: stress = "WARNING"
    
    sql_cb = """
    INSERT INTO features_crossborder_fx_equity (as_of, spx_ret_20d, dxy_ret_20d, corr_spx_dxy_60d, fx_equity_stress)
    VALUES (:as_of, :spx, :dxy, :corr, :stress)
    ON CONFLICT (as_of) DO UPDATE SET fx_equity_stress=EXCLUDED.fx_equity_stress;
    """
    execute_sql(sql_cb, {
        "as_of": as_of, "spx": spx_ret, "dxy": dxy_ret, "corr": corr, "stress": stress
    })
    
    print(f"Computed Macro Features for {as_of}: Reflexive={reflexive}, CrossBorder={stress}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default="2024-01-05")
    args = parser.parse_args()
    compute_macro_features(datetime.strptime(args.date, "%Y-%m-%d").date())
