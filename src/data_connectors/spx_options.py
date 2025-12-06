import os
import databento as db
import pandas as pd
import numpy as np
from datetime import date, datetime
from py_vollib_vectorized import vectorized_implied_volatility, vectorized_delta, vectorized_gamma
from dotenv import load_dotenv

load_dotenv()

class SPXOptionsConnector:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DATABENTO_API_KEY")
        if not self.api_key:
            print("WARNING: No Databento API Key provided.")
        
        self.client = db.Historical(self.api_key)

    def get_option_chain(self, target_date: date, underlying="SPX") -> pd.DataFrame:
        """
        Fetches EOD option prices for SPX from Databento (OPRA).
        Returns DataFrame matching raw_options schema.
        """
        print(f"Fetching {underlying} options for {target_date} via Databento...")
        
        start_str = target_date.strftime("%Y-%m-%d")
        end_str = (target_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        
        try:
            # 1. Fetch Daily Bars (OHLCV-1d)
            # Using GLBX.MDP3 for ES Options as a proxy if SPX fails, but user asked for SPX.
            # OPRA.PILLAR is the dataset for SPX.
            dataset = "OPRA.PILLAR"
            
            # Note: OPRA full feed is huge. Filtering by symbol 'SPX' parent helps.
            # Databento symbology for parent often requires .OPT suffix for options
            query_symbol = underlying
            if dataset == "OPRA.PILLAR" and not underlying.endswith(".OPT"):
                query_symbol = f"{underlying}.OPT"
                
            data = self.client.timeseries.get_range(
                dataset=dataset,
                schema="ohlcv-1d",
                symbols=query_symbol,
                stype_in="parent",
                start=start_str,
                end=end_str
            )
            
            df = data.to_df()
            
            if df.empty:
                print("No data returned from Databento.")
                return pd.DataFrame()
            
            print(f"Fetched {len(df)} rows. Fetching definitions...")
            
            # 2. Fetch Definitions (to resolve strikes/expiries)
            defs = self.client.timeseries.get_range(
                dataset=dataset,
                schema="definition",
                symbols=query_symbol,
                stype_in="parent",
                start=start_str,
                end=end_str
            )
            df_defs = defs.to_df()
            
            # Reset index to access instrument_id
            df = df.reset_index()
            df_defs = df_defs.reset_index()
            
            # Deduplicate definitions
            df_defs = df_defs.drop_duplicates(subset=['instrument_id'], keep='last')
            
            # Merge
            merged = pd.merge(df, df_defs, on='instrument_id', how='inner', suffixes=('', '_def'))
            
            if merged.empty:
                print("Merge failed. No definitions matched.")
                return pd.DataFrame()
            
            # Debug columns
            # print(f"Merged Columns: {merged.columns.tolist()}")
            
            # 3. Map Columns
            # Construct dictionary first to ensure alignment
            data_dict = {
                'as_of': target_date,
                'underlying': underlying,
                'option_symbol': merged['raw_symbol'].values,
                'strike': merged['strike_price'].values,
                'expiry': pd.to_datetime(merged['expiration']).dt.date.values,
                'last': merged['close'].values,
                'bid': merged['close'].values,
                'ask': merged['close'].values,
                'open_interest': 0
            }
            
            # Handle type
            # Try CFI first if valid
            types = None
            if 'cfi' in merged.columns:
                # Check if CFI is populated (len > 1)
                cfi_valid = merged['cfi'].str.len() > 1
                if cfi_valid.any():
                    types = merged['cfi'].str[1].map({'C': 'call', 'P': 'put'})
            
            if types is None or types.isna().all():
                # Fallback to raw_symbol parsing (OSI format: Root YYMMDD T Strike)
                # Look for C/P followed by 8 digits at end (standard OSI)
                # e.g. SPXW  240105C04700000
                extracted = merged['raw_symbol'].str.extract(r'([CP])\d{8}$')
                if not extracted.empty:
                    types = extracted[0].map({'C': 'call', 'P': 'put'})
            
            data_dict['type'] = types.values if types is not None else [None]*len(merged)
                
            out_df = pd.DataFrame(data_dict)
            
            # Filter out unknown types
            out_df = out_df.dropna(subset=['type'])
            
            # Greeks placeholders
            out_df['underlying_price'] = 0.0
            out_df['implied_volatility'] = 0.0
            out_df['delta'] = 0.0
            out_df['gamma'] = 0.0
            
            return out_df 
            
            # Greeks placeholders
            out_df['underlying_price'] = 0.0
            out_df['implied_volatility'] = 0.0
            out_df['delta'] = 0.0
            out_df['gamma'] = 0.0
            
            return out_df

        except Exception as e:
            print(f"Databento Error: {e}")
            # Helpful hint for MVP users
            if "Authorization" in str(e) or "Authentication" in str(e):
                print("Check your API Key.")
            if "Valid dataset" in str(e):
                print(f"Dataset {dataset} might not be enabled on your key.")
            return pd.DataFrame()

    def calculate_greeks(self, df: pd.DataFrame, underlying_price: float):
        """
        Updates df with Delta/Gamma/IV using py_vollib_vectorized.
        """
        if df.empty: return df
        
        # Set underlying price
        df['underlying_price'] = underlying_price
        
        # Time to expiry (years)
        df['T'] = (pd.to_datetime(df['expiry']) - pd.to_datetime(df['as_of'])).dt.days / 365.0
        mask = df['T'] > 0.001
        
        # Risk free rate
        r = 0.045
        
        flag = df['type'].map({'call': 'c', 'put': 'p'})
        
        print("Calculating Greeks via Black-Scholes...")
        # Use only valid rows for calculation
        subset = df[mask].copy()
        
        # IV
        iv = vectorized_implied_volatility(
            subset['last'], underlying_price, subset['strike'], subset['T'], r, flag[mask], return_as='numpy'
        )
        subset['implied_volatility'] = np.nan_to_num(iv)
        
        # Greeks
        subset['delta'] = vectorized_delta(
            flag[mask], underlying_price, subset['strike'], subset['T'], r, subset['implied_volatility'], return_as='numpy'
        )
        subset['gamma'] = vectorized_gamma(
            flag[mask], underlying_price, subset['strike'], subset['T'], r, subset['implied_volatility'], return_as='numpy'
        )
        
        # Merge back
        df.update(subset)
        return df

    def generate_synthetic_oi(self, df: pd.DataFrame, spot_price: float) -> pd.DataFrame:
        """
        Generates synthetic Open Interest for demo purposes when real OI is missing.
        Logic: High OI near ATM, spikes at round strikes (100/50).
        """
        if df.empty: return df
        
        print("Generating Synthetic Open Interest (Demo Mode)...")
        
        strikes = df['strike'].values
        
        # 1. Distance Decay (Higher OI near spot)
        # Normalized distance: |Strike - Spot| / Spot
        dist = np.abs(strikes - spot_price) / spot_price
        # Decay factor: OI drops off as we move away. 
        # 1 / (1 + 20*dist)^2 gives a nice bell curve shape
        decay = 1 / (1 + 30 * dist)**2
        
        # 2. Pinning/Magnet Effect (Round Numbers)
        # Multiples of 100 get 3x boost, 50 get 1.5x boost
        multiplier = np.where(strikes % 100 == 0, 3.0, 
                     np.where(strikes % 50 == 0, 1.5, 1.0))
        
        # 3. Base Magnitude & Randomness
        base_oi = 15000 # Contracts at peak
        noise = np.random.uniform(0.7, 1.3, size=len(strikes))
        
        synthetic_oi = base_oi * decay * multiplier * noise
        
        # Assign
        df['open_interest'] = synthetic_oi.astype(int)
        
        return df
