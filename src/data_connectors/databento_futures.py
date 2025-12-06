import os
import pandas as pd
import databento as db
from dotenv import load_dotenv
from datetime import date

load_dotenv()

class DatabentoFuturesConnector:
    def __init__(self):
        self.client = db.Historical(os.getenv("DATABENTO_API_KEY"))
        
    def get_daily_bars(self, symbol: str, start_date: str, end_date: str, dataset: str = "GLBX.MDP3") -> pd.DataFrame:
        """
        Fetches daily OHLCV bars for a futures contract.
        
        Args:
            symbol (str): The root symbol (e.g., 'GC', 'CL', '6A').
                          We will append '.n.0' for front-month continuous if supported,
                          or query all and filter. 
                          Smart Symbology 'GC.n.0' works for front month.
            start_date (str): YYYY-MM-DD
            end_date (str): YYYY-MM-DD
            dataset (str): 'GLBX.MDP3' for CME Group (Gold, Oil, FX Futures).
        """
        print(f"Fetching {symbol} from Databento ({dataset})...")
        
        # Ensure end > start (Add 1 day if equal)
        if start_date == end_date:
            # Convert to datetime, add day, convert back
            from datetime import datetime, timedelta
            s = datetime.strptime(start_date, "%Y-%m-%d")
            e = s + timedelta(days=1)
            end_date = e.strftime("%Y-%m-%d")
        
        try:
            # Fetch daily bars
            data = self.client.timeseries.get_range(
                dataset=dataset,
                symbols=symbol, 
                start=start_date,
                end=end_date,
                schema="ohlcv-1d",
                stype_in="continuous", # Use continuous contract symbology
                stype_out="instrument_id"
            )
            
            df = data.to_df()
            
            if df.empty:
                print(f"No data returned for {symbol}.")
                return pd.DataFrame()
            
            # Reset index (ts_event is index)
            df = df.reset_index()
            
            # Normalize columns
            # Standardize to: as_of, open, high, low, close, volume
            out_df = pd.DataFrame()
            out_df['as_of'] = df['ts_event'].dt.date
            out_df['open'] = df['open']
            out_df['high'] = df['high']
            out_df['low'] = df['low']
            out_df['close'] = df['close']
            out_df['volume'] = df['volume']
            out_df['symbol'] = df['symbol'] if 'symbol' in df.columns else symbol
            
            return out_df
            
        except Exception as e:
            print(f"Databento Error: {e}")
            return pd.DataFrame()

    def get_gold_futures(self, target_date: str) -> pd.DataFrame:
        # Fetch +/- 5 days around target to ensure we have data
        # GC.n.0 = Front Month Gold
        return self.get_daily_bars("GC.n.0", target_date, target_date)

    def get_oil_futures(self, target_date: str) -> pd.DataFrame:
        # CL.n.0 = Front Month Crude
        return self.get_daily_bars("CL.n.0", target_date, target_date)

    def get_aud_futures(self, target_date: str) -> pd.DataFrame:
        # 6A.n.0 = Front Month AUD/USD
        return self.get_daily_bars("6A.n.0", target_date, target_date)
