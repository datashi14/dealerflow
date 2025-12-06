from dataclasses import dataclass
from typing import Literal, Optional
from datetime import date
import pandas as pd
from src.db import get_connection

Regime = Literal["STABLE", "FRAGILE", "EXPLOSIVE", "UNSTABLE", "PENDING"]

@dataclass
class MacroState:
    as_of: str
    spx_instability: float
    spx_regime: Regime
    audusd_instability: float
    audusd_regime: Regime
    jpy_instability: float
    dxy_ret_20d: float
    wti_instability: float
    nem_instability: float
    us10y: float
    jp10y: float
    spread_usjp_10y: float
    reflexive_loop_active: bool
    fx_equity_stress: str

def build_macro_state(as_of: date) -> MacroState:
    """
    Queries the database to construct a unified MacroState snapshot.
    """
    with get_connection() as conn:
        # 1. Asset Scores
        df_scores = pd.read_sql("SELECT * FROM asset_scores WHERE as_of = %s", conn, params=(as_of,))
        
        # Helpers
        def get_score(sym):
            row = df_scores[df_scores['symbol'] == sym]
            if row.empty: return 0.0, "PENDING"
            return float(row.iloc[0]['instability_index']), row.iloc[0]['regime']

        spx_score, spx_reg = get_score('SPX')
        aud_score, aud_reg = get_score('AUDUSD')
        # JPY score? We didn't compute it in score_assets yet. Assume mock for now.
        jpy_score, jpy_reg = 60.0, "FRAGILE" 
        
        # 2. Macro Features
        df_rates = pd.read_sql("SELECT * FROM features_rates_spreads WHERE as_of = %s", conn, params=(as_of,))
        df_reflex = pd.read_sql("SELECT * FROM features_reflexivity_jp WHERE as_of = %s", conn, params=(as_of,))
        df_cb = pd.read_sql("SELECT * FROM features_crossborder_fx_equity WHERE as_of = %s", conn, params=(as_of,))
        
        us10y = float(df_rates.iloc[0]['us10y']) if not df_rates.empty else 0.0
        jp10y = float(df_rates.iloc[0]['jp10y']) if not df_rates.empty else 0.0
        spread = float(df_rates.iloc[0]['spread_usjp_10y']) if not df_rates.empty else 0.0
        
        reflexive = bool(df_reflex.iloc[0]['reflexive_loop_active']) if not df_reflex.empty else False
        
        stress = df_cb.iloc[0]['fx_equity_stress'] if not df_cb.empty else "NORMAL"
        dxy_ret = float(df_cb.iloc[0]['dxy_ret_20d']) if not df_cb.empty else 0.0
        
        return MacroState(
            as_of=as_of.strftime("%Y-%m-%d"),
            spx_instability=spx_score,
            spx_regime=spx_reg,
            audusd_instability=aud_score,
            audusd_regime=aud_reg,
            jpy_instability=jpy_score,
            dxy_ret_20d=dxy_ret,
            wti_instability=58.0, # Mock
            nem_instability=65.0, # Mock
            us10y=us10y,
            jp10y=jp10y,
            spread_usjp_10y=spread,
            reflexive_loop_active=reflexive,
            fx_equity_stress=stress
        )
