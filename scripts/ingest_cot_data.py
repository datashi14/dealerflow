import argparse
import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_connectors.cftc_cot import CFTCConnector
from src.db import write_dataframe

def map_disagg_to_schema(df, market_name):
    # Map Disaggregated columns to raw_cot
    # Prod_Merc = Hedger
    # M_Money = Spec
    
    # Clean column names first (done in connector, lowercased)
    # We expect: prod_merc_positions_long_all, m_money_positions_long_all, etc.
    
    out = pd.DataFrame()
    out['as_of'] = df['as_of']
    out['market'] = market_name
    out['hedger_long'] = pd.to_numeric(df['prod_merc_positions_long_all'], errors='coerce')
    out['hedger_short'] = pd.to_numeric(df['prod_merc_positions_short_all'], errors='coerce')
    out['spec_long'] = pd.to_numeric(df['m_money_positions_long_all'], errors='coerce')
    out['spec_short'] = pd.to_numeric(df['m_money_positions_short_all'], errors='coerce')
    out['small_long'] = pd.to_numeric(df['nonrept_positions_long_all'], errors='coerce')
    out['small_short'] = pd.to_numeric(df['nonrept_positions_short_all'], errors='coerce')
    return out

def map_fin_to_schema(df, market_name):
    # Map TFF columns to raw_cot
    # Asset Manager + Dealer = Hedger? 
    # Leveraged Funds = Spec
    
    out = pd.DataFrame()
    out['as_of'] = df['as_of']
    out['market'] = market_name
    
    # TFF Columns: 
    # dealer_positions_long_all, asset_mgr_positions_long_all, lev_money_positions_long_all
    
    dealer_L = pd.to_numeric(df['dealer_positions_long_all'], errors='coerce').fillna(0)
    dealer_S = pd.to_numeric(df['dealer_positions_short_all'], errors='coerce').fillna(0)
    asset_L = pd.to_numeric(df['asset_mgr_positions_long_all'], errors='coerce').fillna(0)
    asset_S = pd.to_numeric(df['asset_mgr_positions_short_all'], errors='coerce').fillna(0)
    lev_L = pd.to_numeric(df['lev_money_positions_long_all'], errors='coerce').fillna(0)
    lev_S = pd.to_numeric(df['lev_money_positions_short_all'], errors='coerce').fillna(0)
    
    out['hedger_long'] = dealer_L + asset_L
    out['hedger_short'] = dealer_S + asset_S
    out['spec_long'] = lev_L
    out['spec_short'] = lev_S
    out['small_long'] = pd.to_numeric(df['nonrept_positions_long_all'], errors='coerce') # TFF also has nonrept? Yes.
    out['small_short'] = pd.to_numeric(df['nonrept_positions_short_all'], errors='coerce')
    
    return out

def ingest_cot():
    connector = CFTCConnector()
    
    years = [2024, 2025]
    
    for year in years:
        print(f"Processing COT for {year}...")
        # 1. Gold (Disaggregated)
        df_disagg = connector.fetch_disagg_cot(year)
        if not df_disagg.empty:
            df_gold = connector.filter_gold(df_disagg)
            mapped_gold = map_disagg_to_schema(df_gold, "GOLD")
            print(f"Ingesting {len(mapped_gold)} rows for GOLD COT ({year})...")
            write_dataframe(mapped_gold, 'raw_cot', if_exists='append', index=False)
            
        # 2. AUD (Financial)
        df_fin = connector.fetch_financial_cot(year)
        if not df_fin.empty:
            df_aud = connector.filter_aud(df_fin)
            mapped_aud = map_fin_to_schema(df_aud, "AUD")
            print(f"Ingesting {len(mapped_aud)} rows for AUD COT ({year})...")
            write_dataframe(mapped_aud, 'raw_cot', if_exists='append', index=False)

if __name__ == "__main__":
    ingest_cot()
